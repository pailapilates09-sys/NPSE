"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Mover = { symbol: string; name: string; ltp: number; percent_change: number; turnover: number };
type Sector = { code: string; name: string; latest_date: string; return_1d: number | null; return_5d: number | null; return_20d: number | null };
type TurnoverPoint = { date: string; turnover: number };
type IndexPoint = { date: string; close: number; sma20: number | null; sma50: number | null };
type Dashboard = {
  market: {
    is_open: boolean;
    index: number | null;
    change: number | null;
    percent_change: number | null;
    turnover: number | null;
    turnover_vs_20d_pct: number | null;
    traded_scrips: number | null;
  };
  breadth: { advancers: number; decliners: number; unchanged: number; ratio: number | null };
  turnover_history: TurnoverPoint[];
  index_history: IndexPoint[];
  sectors: Sector[];
  top_gainers: Mover[];
  top_losers: Mover[];
  top_turnover: Mover[];
  provenance: {
    adapter: string;
    upstream: string;
    retrieved_at: string;
    market_observed_at: string | null;
    index_history_final_through: string | null;
  };
};

const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 });

function pct(value: number | null | undefined) {
  return value == null ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="metric card">
      <span>{label}</span>
      <strong>{value}</strong>
      {sub && <small>{sub}</small>}
    </div>
  );
}

function Movers({ title, rows }: { title: string; rows: Mover[] }) {
  return (
    <section className="card table-card">
      <h2>{title}</h2>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Symbol</th><th>LTP</th><th>Change</th><th>Turnover</th></tr></thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.symbol}>
                <td><b>{row.symbol}</b><span className="company">{row.name}</span></td>
                <td>{fmt.format(row.ltp)}</td>
                <td className={row.percent_change >= 0 ? "up" : "down"}>{pct(row.percent_change)}</td>
                <td>Rs {compact.format(row.turnover)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function Home() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/dashboard")
      .then(async (res) => {
        if (!res.ok) throw new Error(`API ${res.status}`);
        return res.json();
      })
      .then(setData)
      .catch((err) => setError(String(err)));
  }, []);

  const sector20 = useMemo(
    () => (data?.sectors ?? []).filter((s) => s.return_20d != null).sort((a, b) => (b.return_20d ?? 0) - (a.return_20d ?? 0)),
    [data]
  );

  if (error) {
    return <main className="shell"><div className="error card"><h1>Market diagnostics</h1><p>Data API is unavailable: {error}</p><p>Check <code>/api/dashboard</code> and the Vercel function logs.</p></div></main>;
  }

  if (!data) {
    return <main className="shell"><div className="loading card">Loading live market evidence…</div></main>;
  }

  const totalBreadth = data.breadth.advancers + data.breadth.decliners + data.breadth.unchanged;

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Nepal Stock Exchange research system</p>
          <h1>Market diagnostics</h1>
          <p className="lede">Market structure first: trend, breadth, money flow, sector rotation and liquid leaders — all tied to machine-readable source timestamps.</p>
        </div>
        <div className={`status ${data.market.is_open ? "open" : "closed"}`}>
          <i /> {data.market.is_open ? "Market open" : "Market closed"}
        </div>
      </header>

      <div className="notice">Secondary market diagnostics. Observation: {data.provenance.market_observed_at ?? "Unavailable"}; finalized index history: {data.provenance.index_history_final_through ?? "Unavailable"}. Older history must not be interpreted as current investment evidence.</div>
      <p><a href="/technical">Open completed-session price / volume research →</a></p>
      <section className="metrics">
        <Metric label="NEPSE" value={data.market.index == null ? "—" : fmt.format(data.market.index)} sub={pct(data.market.percent_change)} />
        <Metric label="Turnover" value={data.market.turnover == null ? "—" : `Rs ${compact.format(data.market.turnover)}`} sub={`${pct(data.market.turnover_vs_20d_pct)} vs 20-session avg`} />
        <Metric label="All-scrip breadth" value={`${data.breadth.advancers} ↑ / ${data.breadth.decliners} ↓`} sub={`${data.breadth.unchanged} unchanged · ${totalBreadth} upstream traded scrips`} />
        <Metric label="Scrips traded" value={data.market.traded_scrips == null ? "—" : fmt.format(data.market.traded_scrips)} sub={`All-scrip A/D ratio ${data.breadth.ratio == null ? "—" : data.breadth.ratio.toFixed(2)}`} />
      </section>

      <section className="grid two">
        <div className="card chart-card">
          <div className="section-head"><div><span>Trend</span><h2>NEPSE index</h2></div><small>SMA 20 / SMA 50</small></div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.index_history} margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" minTickGap={36} tickFormatter={(v) => v.slice(5)} />
                <YAxis domain={["auto", "auto"]} width={58} />
                <Tooltip formatter={(v) => typeof v === "number" ? fmt.format(v) : v} />
                <Line type="monotone" dataKey="close" name="Close" dot={false} strokeWidth={2.4} />
                <Line type="monotone" dataKey="sma20" name="SMA 20" dot={false} strokeWidth={1.4} />
                <Line type="monotone" dataKey="sma50" name="SMA 50" dot={false} strokeWidth={1.4} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card chart-card">
          <div className="section-head"><div><span>Money flow</span><h2>Daily turnover</h2></div><small>Last {data.turnover_history.length} sessions</small></div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.turnover_history} margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" minTickGap={36} tickFormatter={(v) => v.slice(5)} />
                <YAxis tickFormatter={(v) => compact.format(v)} width={58} />
                <Tooltip formatter={(v) => typeof v === "number" ? `Rs ${compact.format(v)}` : v} />
                <Line type="monotone" dataKey="turnover" name="Turnover" dot={false} strokeWidth={2.4} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="card chart-card sector-card">
        <div className="section-head"><div><span>Rotation</span><h2>Sector performance — 20 sessions</h2></div><small>Final history through {data.provenance.index_history_final_through ?? "—"}</small></div>
        <div className="sector-chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sector20} layout="vertical" margin={{ top: 8, right: 28, bottom: 8, left: 28 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => `${v}%`} />
              <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v) => typeof v === "number" ? pct(v) : v} />
              <Bar dataKey="return_20d" name="20-session return" radius={[0, 5, 5, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid three">
        <Movers title="Top gainers" rows={data.top_gainers} />
        <Movers title="Top losers" rows={data.top_losers} />
        <Movers title="Turnover leaders" rows={data.top_turnover} />
      </section>

      <footer className="provenance card">
        <div><b>Source adapter</b><span>{data.provenance.adapter}</span></div>
        <div><b>Market observed</b><span>{data.provenance.market_observed_at ? new Date(data.provenance.market_observed_at).toLocaleString() : "—"}</span></div>
        <div><b>Retrieved</b><span>{new Date(data.provenance.retrieved_at).toLocaleString()}</span></div>
        <div><b>Upstream</b><span>{data.provenance.upstream}</span></div>
      </footer>
      <p className="disclaimer">Research dashboard only. The breadth metric currently counts every traded scrip returned by the upstream adapter, so it is not directly comparable with media reports that count listed companies only. Source freshness and discrepancies must be checked before relying on any figure. This system does not place trades.</p>
    </main>
  );
}
