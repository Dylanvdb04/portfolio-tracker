 # Portfolio Tracker

A command-line interface (CLI) investment portfolio tracker built for the "Vermogensbeheer Assignment Portfolio Tracker". The application follows the Model-View-Controller (MVC) architecture as desired in the assignment. It will allow users to manage a portfolio, get live prices from yahoo finance, visualise historical data, 
and perform quantitative risk analysis. 

---

## Features

- **Portfolio Management** — add and remove assets (to the portfolio) with ticker, sector, asset class, quantity and purchase price
- **Live Prices** — get real-time and historical prices via yahoo finance
- **Portfolio Overview** — view current values, transaction values and P&L per asset
- **Weight Analysis** — calculate portfolio weights by asset, sector and asset class
- **Price Charts** — generate historical price charts for one or multiple tickers
- **Monte Carlo Simulation** — simulate 100,000 portfolio paths over 15 years using Geometric Brownian Motion
- **VaR & CVaR** — calculate Value at Risk and Conditional Value at Risk using both historical and simulation-based methods
- **Sharpe Ratio** — calculate risk-adjusted return

---

## Project Structure


portfolio_tracker/
│
├── portfolio_tracker/        
│   ├── models/               
│   │   ├── portfolio.py      
│   │   └── simulation.py     
│   ├── views/                
│   │   └── display.py        
│   └── controllers/          
│       └── cli.py            
│
├── data/                     
├── charts/                   
├── main.py                   
└── requirements.txt   

The application follows the **MVC design pattern** as specified above:
- **Model** — stores and manipulates asset data, performs all calculations
- **View** — handles all output: tables, charts, and formatted text
- **Controller** — receives CLI commands and coordinates Model and View

---
## Installation

**1. Clone the repository**
```bash
git clone https://github.com/Dylanvdb04/portfolio-tracker.git
cd portfolio-tracker
```

**2. Create a virtual environment (recommended)**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

---

## Usage

### Add an asset
```bash
python main.py add AAPL --sector Technology --class Equity --qty 10 --price 182.50  
```


### Remove an asset
```bash
python main.py remove AAPL
```

### View portfolio
```bash
python main.py show
```

### View weights in the portfolio
```bash
python main.py weights --by asset      # by individual asset
python main.py weights --by sector     # by sector
python main.py weights --by class      # by asset class
```

### View price info
```bash
python main.py price AAPL
```

### Plot price history
```bash
python main.py chart AAPL                        # single ticker, 1 year by default
python main.py chart AAPL MSFT --period 5y       # multiple tickers, 5 years
```
Available periods: `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `max` #from Yahoo finance

### Monte Carlo simulation
```bash
python main.py simulate
```
Simulates 100,000 paths over 15 years using Geometric Brownian Motion (GBM). 
Drift and volatility are estimated from 2 years of historical data.
Charts are saved to the `charts/` folder.

### VaR and CVaR
```bash
python main.py risk                        # 95% confidence level, by default
python main.py risk --confidence 0.99      # 99% confidence level
```
Calculates both historical and Monte Carlo based VaR and CVaR.

### Sharpe Ratio
```bash
python main.py sharpe                  # default 2% risk-free rate
python main.py sharpe --rf 0.03        # custom risk-free rate
```

---

## Quantitative Methods

### Monte Carlo Simulation
Portfolio paths are simulated using the **Geometric Brownian Motion** (GBM) closed form solution:

```math
S_t = S_0 \cdot e^{(\mu - \frac{\sigma^2}{2})t + \sigma \sqrt{t} \cdot Z}
```

Where:
- $\mu$ = annualised drift estimated from 2 years of historical log returns
- $\sigma$ = annualised volatility estimated from 2 years of historical log returns
- $Z \sim \mathcal{N}(0,1)$ = standard normal random variable
- The $\frac{\sigma^2}{2}$ term is the **Itô correction** ensuring unbiased simulation

### Value at Risk (VaR)

```math
VaR_{\alpha} = -\text{percentile}(PnL, 1-\alpha)
```

### Conditional Value at Risk (CVaR)

```math
CVaR_{\alpha} = -E[PnL \mid PnL \leq -VaR_{\alpha}]
```

### Sharpe Ratio

```math
S = \frac{R_p - R_f}{\sigma_p}
```

---

## Dependencies

| Library | Purpose |
|---|---|
| `yfinance` | Live and historical price data |
| `pandas` | Data manipulation |
| `numpy` | Numerical computing and simulation |
| `matplotlib` | Chart generation |
| `rich` | Terminal tables and formatting |
| `click` | CLI command structure |

---

## Author

Dylan van den Bergen — MSc Quantitative Finance and Actuarial Science (QFAS), Tilburg University