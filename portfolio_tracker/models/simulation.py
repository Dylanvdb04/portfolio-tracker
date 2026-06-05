import numpy as np
import pandas as pd
import yfinance as yf
from rich.console import Console

console = Console()



def get_portfolio_returns(portfolio) -> pd.Series:
    """
    Calculate historical weighted portfolio returns
    from actual price data of all assets
    """
    #First check whether there are any assets in the portfolio, if not we can't run a simulation
    if not portfolio.assets:
        raise ValueError("Portfolio is empty — add assets first")

    #Get total portfolio value for weight calculation
    total_value = portfolio.total_current_value()

    #Initialize an empty Series to accumulate weighted returns
    weighted_returns = None

    #Loop over all assets and calculate their weighted returns
    for asset in portfolio.assets:
        #Calculate this asset's weight in the portfolio
        weight = asset.current_value() / total_value

        #Download 2 years of historical daily prices via yahoo finance
        console.print(f"[cyan]Fetching historical data for {asset.ticker}...[/cyan]")
        data = yf.download(asset.ticker, period="2y", progress=False)   #Gives us two years of data

        #Warning message if we cannot retrieve the data for this particular asset (ticker) 
        if data.empty:
            console.print(f"[red]Warning: no data for {asset.ticker}, skipping[/red]")
            continue

        #Calculate daily log returns, this is needed due to normality assumption of GBM and it is mathematically convenient
        #log(S_t / S_{t-1})
        close = data["Close"]
        if hasattr(close, "columns"):
            close = close.iloc[:, 0]
        log_returns = np.log(close / close.shift(1)).dropna()

        #Weight the returns by portfolio weight
        weighted = log_returns.squeeze() * weight

        #Add to portfolio returns
        if weighted_returns is None:
            weighted_returns = weighted.squeeze()
        else:
            #Handle differences between continents when one stock is traded for example, but another is not due to holidays. We use add with fill_value=0 to treat missing days as zero return for that asset.
            weighted_returns = weighted_returns.add(weighted.squeeze(), fill_value=0)

    return weighted_returns


def run_simulation(portfolio, years: int = 15, n_paths: int = 100_000) -> dict:
    """
    Run a Monte Carlo simulation using Geometric Brownian Motion (GBMs)
    over the specified number of years with n_paths simulated paths. By default, we simulate 100,000 paths over 15 years.

    Returns a dictionary with:
        - paths:         numpy array of shape (time_steps, n_paths)
        - years:         number of years simulated
        - initial_value: starting portfolio value
        - percentiles:   p10, p50, p90 at each time step
    """

    #Step 1: Get historical returns, here we use or function from above which calculated the weighted returns for all assets in the portfolio.
    returns = get_portfolio_returns(portfolio)  #This is the weighted returns including all the assets. (shape is 1 x N where N is the number of trading days in the historical data)

    #Step 2: Estimate drift and volatility from historical data
    #Annualise by multiplying by 252 trading days
    mu_daily    = float(returns.mean())  #Likely very small number
    sigma_daily = float(returns.std())

    mu    = mu_daily    * 252          #annual drift. This is the average return that you get daily, multiplied with all the trading days in a year. This is the return you would expect on average per year.
    sigma = sigma_daily * np.sqrt(252) #annual volatility

    console.print(f"[cyan]Estimated annual drift:      {mu:.2%}[/cyan]")
    console.print(f"[cyan]Estimated annual volatility: {sigma:.2%}[/cyan]")

    #Step 3: Simulation parameters
    dt          = 1 / 12              #monthly time steps
    n_steps     = years * 12          #15 years × 12 months = 180 steps
    S0          = portfolio.total_current_value()  #starting value (at start of simulation, t=0)

    #Step 4: Pre-calculate the GBM components
    #From the GBM closed form solution:
    #S(t+dt) = S(t) * exp((μ - σ²/2)dt + σ√dt * Z)  
    drift     = (mu - 0.5 * sigma ** 2) * dt       #deterministic part
    diffusion = sigma * np.sqrt(dt)                 #stochastic part

    #Step 5: Simulate all paths at once using numpy
    #Generate all random shocks at once; shape (n_steps, n_paths)
    #Each column is one path, each row is one time step
    Z = np.random.standard_normal((n_steps, n_paths)) #180 x 100,000

    #Calculate log returns for each step and path. This gives the whole future return for each path in one go. We will convert these log returns to price levels in the next step.
    log_returns = drift + diffusion * Z  #shape (n_steps, n_paths)

    #Convert log returns to price levels using cumulative sum
    #cumsum gives us the cumulative log return up to each time step
    log_price_paths = np.cumsum(log_returns, axis=0)  #shape (n_steps, n_paths), shape preserved but now each value is the cumulative log return from t=0 to that time step for each path.

    #Convert from log prices back to actual portfolio values
    #Add row of zeros so paths start at S0 at t=0 which is month 0 so our starting values
    log_price_paths = np.vstack([
        np.zeros((1, n_paths)),   #t=0: everyone starts at S0
        log_price_paths
    ])

    #Final paths in euros. Note that at t= 0, exp(0) = 1, so we start at S0 as expected. Then the paths evolve according to the GBM dynamics.
    paths = S0 * np.exp(log_price_paths)  #shape (n_steps+1, n_paths)

    #Step 6: Calculate percentiles at each time step ─────────────
    percentiles = {
        "p10": np.percentile(paths, 10, axis=1),  #bad case
        "p50": np.percentile(paths, 50, axis=1),  #median
        "p90": np.percentile(paths, 90, axis=1),  #good case
    }

    console.print(f"[green] Simulation complete — {n_paths:,} paths over {years} years[/green]")

    return {
        "paths":         paths,
        "years":         years,
        "initial_value": S0,
        "percentiles":   percentiles
    }