import click
from portfolio_tracker.models.portfolio import Portfolio, Asset #Two classes that we defined in portfolio.py
from portfolio_tracker.views.display import (
    show_portfolio_table,
    show_weights_table,
    show_price_table,
    plot_price_history,
    plot_simulation
)   #Functions we defined in the views/display.py file to show tables and charts.
from rich.console import Console
from portfolio_tracker.models.simulation import run_simulation, calculate_var_cvar, calculate_sharpe


console = Console()


#Create global portfolio instance
portfolio = Portfolio()


@click.group()
def cli():
    """ASR Portfolio Tracker — manage and analyse your investments"""
    pass



#To add an asset:
#python main.py add AAPL --sector Technology --class Equity --qty 10 --price 182.50

@cli.command()
@click.argument("ticker")
@click.option("--sector",   required=True,  help="Sector e.g. Technology")
@click.option("--class",    "asset_class",  required=True, help="Asset class e.g. Equity")
@click.option("--qty",      required=True,  type=float,    help="Quantity of shares")
@click.option("--price",    required=True,  type=float,    help="Purchase price per share")
def add(ticker, sector, asset_class, qty, price):
    """Add a new asset to the portfolio"""
    asset = Asset(
        ticker=ticker.upper(),
        sector=sector,
        asset_class=asset_class,
        quantity=qty,
        purchase_price=price
    )
    portfolio.add_asset(asset)
    console.print(f"[green] Added {ticker.upper()} to portfolio[/green]")



#To remove an asset:
#python main.py remove AAPL


@cli.command()
@click.argument("ticker")
def remove(ticker):
    """Remove an asset from the portfolio"""
    success = portfolio.remove_asset(ticker.upper())
    if success:
        console.print(f"[green] Removed {ticker.upper()} from portfolio[/green]")
    else:
        console.print(f"[red] {ticker.upper()} not found in portfolio[/red]")



#To view portfolio:
#python main.py portfolio

@cli.command()
def show():
    """Display the current portfolio with values and P&L"""
    show_portfolio_table(portfolio.assets)



#To show weights:
#python main.py weights --by asset
#python main.py weights --by sector
#python main.py weights --by class


@cli.command()
@click.option("--by", 
              type=click.Choice(["asset", "sector", "class"]), 
              default="asset",
              help="Group weights by asset, sector or class")
def weights(by):
    """Show portfolio weights by asset, sector or asset class"""
    if by == "asset":
        show_weights_table(portfolio.asset_weights(), "Weights by Asset")
    elif by == "sector":
        show_weights_table(portfolio.weights_by_sector(), "Weights by Sector")
    elif by == "class":
        show_weights_table(portfolio.weights_by_asset_class(), "Weights by Asset Class")



#Show price
#python main.py price AAPL


@cli.command()
@click.argument("ticker")
def price(ticker):
    """Show current price information for a ticker"""
    show_price_table(ticker.upper())



#Show charts of prices for the tickers
#python main.py chart AAPL
#python main.py chart AAPL MSFT --period 5y


@cli.command()
@click.argument("tickers", nargs=-1, required=True)
@click.option("--period",
              default="1y",
              type=click.Choice(["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]),
              help="Time period for the chart")
def chart(tickers, period):
    """Plot historical price chart for one or more tickers"""
    plot_price_history(list(tickers), period=period)



#Simulation command
#python main.py simulate


@cli.command()
def simulate():
    """Run Monte Carlo simulation over 15 years for the portfolio"""
    from portfolio_tracker.models.simulation import run_simulation
    console.print("[cyan]Running 100,000 path simulation... this may take a moment[/cyan]")
    results = run_simulation(portfolio)
    plot_simulation(results)

#VaR/ CVaR command
#python main.py risk
# python main.py risk --confidence 0.99

@cli.command()
@click.option("--confidence",
              default=0.95,
              type=float,
              help="Confidence level e.g. 0.95 for 95%, 0.99 for 99%")
def risk(confidence):
    """Calculate VaR and CVaR risk metrics for the portfolio"""
    from portfolio_tracker.views.display import show_var_cvar_table
    console.print(f"[cyan]Calculating VaR and CVaR at "
                  f"{confidence:.0%} confidence level...[/cyan]")
    results = calculate_var_cvar(portfolio, confidence=confidence)
    show_var_cvar_table(results)

#Sharpe Ratio command
#python main.py sharpe
#python main.py sharpe --rf 0.03

@cli.command()
@click.option("--rf",
              default=0.02,
              type=float,
              help="Annual risk-free rate e.g. 0.02 for 2%")
def sharpe(rf):
    """Calculate the Sharpe Ratio of the portfolio"""
    from portfolio_tracker.views.display import show_sharpe_table
    console.print(f"[cyan]Calculating Sharpe Ratio "
                  f"(risk-free rate: {rf:.2%})...[/cyan]")
    results = calculate_sharpe(portfolio, risk_free_rate=rf)
    show_sharpe_table(results)



