'use strict';

const get = (id) => document.getElementById(id);
const make = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
};
const localTime = new Intl.DateTimeFormat('en-NP', {
  dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Kathmandu',
});
const localDate = new Intl.DateTimeFormat('en-NP', {
  dateStyle: 'medium', timeZone: 'Asia/Kathmandu',
});
const npr = new Intl.NumberFormat('en-NP', { maximumFractionDigits: 2 });
const rupees = (n) => 'Rs ' + npr.format(n);
const when = (value) => localDate.format(new Date(value + 'T00:00:00+05:45'));
const stillCurrent = (asOf, expiresAt) => {
  const now = Date.now();
  return Date.parse(asOf) <= now + 300000 && Date.parse(expiresAt) > now;
};

function link(label, url) {
  try {
    const target = new URL(url);
    if (target.protocol !== 'https:' || target.username || target.password) {
      return make('span', label);
    }
    const a = make('a', label);
    a.href = target.href;
    return a;
  } catch {
    return make('span', label);
  }
}

function status(heading, message, ready = false) {
  get('buy').classList.toggle('ready', ready);
  get('buy').replaceChildren(make('p', heading, 'status-name'), make('p', message));
}

function ticker(symbol, label) {
  const article = make('article', null, 'ticker');
  const heading = make('h4');
  const button = make('button', symbol, 'symbol link');
  button.type = 'button';
  button.setAttribute('aria-label', 'Show sell conditions for ' + symbol);
  button.addEventListener('click', () => {
    const select = get('holding');
    select.value = symbol;
    select.dispatchEvent(new Event('change'));
    select.focus();
  });
  heading.append(button, make('span', label, 'issuer'));
  article.append(heading);
  return article;
}

function term(root, label, value) {
  const row = make('div');
  row.append(make('dt', label), make('dd', value));
  root.append(row);
}

function fact(label, value) {
  const row = make('article');
  row.append(make('h3', label), make('p', value));
  return row;
}

function render(data) {
  const current = stillCurrent(data.as_of, data.expires_at) && data.engine_connected;
  get('stamp').textContent = 'Snapshot: ' + localTime.format(new Date(data.as_of)) + ' Nepal time';
  const listing = get('holding');
  listing.replaceChildren(make('option', 'Select a ticker'));
  listing.options[0].value = '';
  for (const symbol of Object.keys(data.companies).sort()) {
    const option = make('option', symbol + ' · ' + data.companies[symbol].name);
    option.value = symbol;
    listing.append(option);
  }
  listing.disabled = false;

  listing.onchange = () => {
    const model = data.companies[listing.value];
    if (!model) {
      const guidance = make('dl', null, 'checks');
      term(guidance, 'Sell review', 'New evidence undermines the reason you bought.');
      term(guidance, 'Trim review', 'The price exceeds a supported valuation or the position exceeds your own risk limit.');
      get('holding-detail').replaceChildren(guidance);
      return;
    }
    const checks = make('dl', null, 'checks');
    const rules = data.exit_rules[model.sector] || {};
    const value = model.valuation;
    if (model.risk_note) term(checks, 'Risk to verify', model.risk_note);
    term(checks, 'Review selling if', (rules.invalidate || []).join('. ') || 'New filings undermine the original case.');
    if (current && value && stillCurrent(value.price_observed_at, value.expires_at)) {
      const crossed = value.price > value.exit_review_above;
      term(checks, 'Price for a trim review',
        (crossed ? 'Review: the verified quote is above ' : 'Review if the verified price rises above ') +
        rupees(value.exit_review_above) + '. Recheck fair value before acting.');
    } else {
      term(checks, 'Price for a trim review', 'No verified price level is available. Check your own position and liquidity limits.');
    }
    if (rules.monitor?.length) term(checks, 'What to check', rules.monitor.join('. '));
    get('holding-detail').replaceChildren(make('h3', listing.value + ' · ' + model.name), checks);
    if (current && value && stillCurrent(value.price_observed_at, value.expires_at)) {
      const source = make('p', null, 'rule');
      source.append(link('Official price source', value.source));
      get('holding-detail').append(source);
    }
  };

  const qualified = current ? data.buy.filter((symbol) => {
    const value = data.companies[symbol]?.valuation;
    return value && stillCurrent(value.price_observed_at, value.expires_at) && value.price <= value.entry_ceiling;
  }) : [];
  if (!current) {
    status('No current buy call', 'The snapshot is too old or the engine could not confirm its data. Check again after the next refresh.');
  } else if (!qualified.length) {
    status('Wait. No buy qualifies.', data.official_prices === 0
      ? 'The board has no verified NEPSE quote for the shares it tracks.'
      : 'No share clears the evidence checks and the entry price limit.');
  } else {
    status(qualified.length + (qualified.length === 1 ? ' share meets' : ' shares meet') + ' the entry rules',
      'Check the official price and buy ceiling before placing an order.', true);
  }
  get('qualified').replaceChildren(...qualified.map((symbol) => {
    const model = data.companies[symbol];
    const value = model.valuation;
    const article = ticker(symbol, model.name);
    article.append(make('p', 'Entry at or below ' + rupees(value.entry_ceiling) + ' · verified quote ' + rupees(value.price)));
    if (value.margin) article.append(make('p', npr.format(100 * value.margin) + '% below model fair value.'));
    if (value.reason) article.append(make('p', value.reason));
    const source = make('p', null, 'proof');
    source.append(link('Official price source', value.source));
    article.append(source);
    return article;
  }));

  const watch = data.watch.filter((row) => !qualified.includes(row.symbol));
  get('watch').hidden = !watch.length;
  get('watch-cards').replaceChildren(...watch.map((row) => {
    const article = ticker(row.symbol, data.companies[row.symbol].name);
    const source = make('p', null, 'proof');
    source.append(link('Financial evidence', row.source), document.createTextNode(' · Period to ' + when(row.period)));
    article.append(make('p', row.why), source);
    return article;
  }));
  const marketDate = data.market_date ? when(data.market_date) : 'Date unavailable';
  get('facts').replaceChildren(
    fact('Latest market observation', marketDate + (data.official_prices === 0 ? ' · secondary feed' : ' · market feed')),
    fact('Verified NEPSE quotes in snapshot', data.official_prices + ' of ' + data.registered),
    fact('Companies with some primary financial evidence', data.primary_financials + ' of ' + data.registered),
  );
}

fetch('./data/decisions.json', {cache: 'no-cache'})
  .then((response) => {
    if (!response.ok) throw new Error('Snapshot unavailable');
    return response.json();
  })
  .then((data) => {
    if (data.schema !== 1 || !data.companies || !Array.isArray(data.buy) || !Array.isArray(data.watch)) {
      throw new Error('Invalid snapshot');
    }
    render(data);
  })
  .catch(() => {
    get('stamp').textContent = 'Snapshot unavailable';
    status('No current buy call', 'The decision evidence did not load. Refresh to try again.');
    get('facts').replaceChildren(make('p', 'No current evidence is available to compare.'));
  });
