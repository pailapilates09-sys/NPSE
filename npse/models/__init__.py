from .banks import MODEL as BANKS
from .hydropower import MODEL as HYDRO
from .manufacturing import MODEL as MANUFACTURING
from .microfinance import MODEL as MICROFINANCE
from .life_insurance import MODEL as LIFE
from .nonlife_insurance import MODEL as NONLIFE

MODELS = {"banks": BANKS, "hydropower": HYDRO, "manufacturing": MANUFACTURING,
          "microfinance": MICROFINANCE, "life-insurance": LIFE, "non-life-insurance": NONLIFE}
