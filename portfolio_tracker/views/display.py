import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
import yfinance as yf
import os


#From rich package
console = Console()

#Now we gonna make a portfolio table that shows all assets with their current value

def show_portfolio_table(assets: list) -> None:
    """Display a rich table with all assets in the portfolio"""

    if len(assets) == 0:
        console.print(Panel("Portfolio is empty. We first need to add assets.", 
                           style="yellow"))
        return

    #Create the table
    table = Table(
        title="Current Portfolio",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    #Define columns
    table.add_column("Ticker",          style="bold white",  justify="center")
    table.add_column("Sector",          style="blue",        justify="center")
    table.add_column("Asset Class",     style="blue",        justify="center")
    table.add_column("Quantity",        style="white",       justify="right")
    table.add_column("Buy Price",       style="white",       justify="right")
    table.add_column("Transaction Val", style="white",       justify="right")
    table.add_column("Current Price",   style="white",       justify="right")
    table.add_column("Current Val",     style="white",       justify="right")
    table.add_column("P&L",             style="white",       justify="right")
    table.add_column("P&L %",           style="white",       justify="right")

    total_transaction = 0
    total_current = 0

    #Add a row for each asset
    for asset in assets:
        current_price   = asset.current_price()
        current_val     = asset.current_value()
        pl              = asset.profit_loss()
        pl_pct          = asset.profit_loss_pct()

        total_transaction += asset.transaction_value
        total_current     += current_val

        #Color P&L green if positive, red if negative
        pl_color    = "green" if pl >= 0 else "red"
        pl_str      = f"[{pl_color}]€{pl:,.2f}[/{pl_color}]"
        pl_pct_str  = f"[{pl_color}]{pl_pct:+.2f}%[/{pl_color}]"

        #Now populate the table columns with the asset data from the assets list using the properties and methods we defined in the Asset class
        table.add_row(
            asset.ticker,
            asset.sector,
            asset.asset_class,
            str(asset.quantity),
            f"€{asset.purchase_price:,.2f}",
            f"€{asset.transaction_value:,.2f}",
            f"€{current_price:,.2f}",
            f"€{current_val:,.2f}",
            pl_str,
            pl_pct_str
        )

    console.print(table)

    # Print summary below the table
    total_pl        = total_current - total_transaction
    total_pl_pct    = (total_pl / total_transaction) * 100
    pl_color        = "green" if total_pl >= 0 else "red"
    

    console.print(f"\n[bold]Total Invested:[/bold]     €{total_transaction:,.2f}")
    console.print(f"[bold]Total Current Value:[/bold] €{total_current:,.2f}")
    console.print(f"[bold]Total P&L:[/bold]           [{pl_color}]€{total_pl:,.2f} ({total_pl_pct:+.2f}%)[/{pl_color}]\n")


#Now weight tables, showing portfolio weights by asset, sector and asset class

def show_weights_table(weights: dict, title: str) -> None:
    """Display a table showing portfolio weights"""

    table = Table(
        title=f"{title}",
        box=box.ROUNDED,
        header_style="bold cyan"
    )

    table.add_column("Name",    style="bold white", justify="left")
    table.add_column("Weight",  style="green",      justify="right")

    #Sort by weight descending, largest position first
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)

    #Unpack the tuple into its name and weight components
    for name, weight in sorted_weights:
        # Visual bar to represent weight
        bar_length  = int(weight / 2)
        bar         = "█" * bar_length
        table.add_row(name, f"{weight:.2f}%  {bar}")

    console.print(table)


#Now price table which shows the current price for a ticker

def show_price_table(ticker: str) -> None:
    """Display current price information for a ticker"""

    ticker_obj = yf.Ticker(ticker)
    
    # Use history for reliable price data
    hist_1d  = ticker_obj.history(period="1d")
    hist_1y  = ticker_obj.history(period="1y")

    def fmt(val):
        """Safely format a price value"""
        try:
            return f"€{float(val):,.2f}"
        except (TypeError, ValueError):
            return "N/A"

    # Extract values safely
    current_price   = hist_1d["Close"].iloc[-1]  if not hist_1d.empty  else None
    day_high        = hist_1d["High"].iloc[-1]   if not hist_1d.empty  else None
    day_low         = hist_1d["Low"].iloc[-1]    if not hist_1d.empty  else None
    week52_high     = hist_1y["High"].max()      if not hist_1y.empty  else None
    week52_low      = hist_1y["Low"].min()       if not hist_1y.empty  else None

    table = Table(
        title=f"💰 {ticker} Price Info",
        box=box.ROUNDED,
        header_style="bold cyan"
    )

    table.add_column("Metric", style="bold white", justify="left")
    table.add_column("Value",  style="green",      justify="right")

    table.add_row("Current Price", fmt(current_price))
    table.add_row("Day High",      fmt(day_high))
    table.add_row("Day Low",       fmt(day_low))
    table.add_row("52W High",      fmt(week52_high))
    table.add_row("52W Low",       fmt(week52_low))

    console.print(table)

#Now a historical price chart for one (or more) tickers

def plot_price_history(tickers: list, period: str = "1y") -> None:
    """
    Plot historical price chart for one or multiple tickers
    period options: 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    #Make sure charts folder exists
    os.makedirs("charts", exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    for ticker in tickers:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty:
            console.print(f"[red]No data found for {ticker}[/red]")
            continue
        ax.plot(data.index, data["Close"], label=ticker, linewidth=2)

    # Formatting the chart
    ax.set_title(f"Price History — {', '.join(tickers)}", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (€)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save to charts folder
    filename = f"charts/{'_'.join(tickers)}_{period}.png"
    plt.savefig(filename, dpi=150)
    plt.close()

    console.print(f"[green]Chart saved to {filename}[/green]")



#Monte Carlo simulation paths for the coming (15) years. 100,000 paths assumed.



def plot_simulation(simulation_results: dict) -> None:
    """
    Plot the Monte Carlo simulation results
    simulation_results comes from the model layer
    """

    os.makedirs("charts", exist_ok=True)

    paths           = simulation_results["paths"]
    years           = simulation_results["years"]
    initial_value   = simulation_results["initial_value"]
    percentiles     = simulation_results["percentiles"]

    fig, ax = plt.subplots(figsize=(14, 7))

    #Plot a random sample of 500 paths for sake of computational efficiency and readibility. 100000 paths would be hard to see.
    sample_indices = np.random.choice(paths.shape[1], size=500, replace=False)
    time_axis = np.linspace(0, years, paths.shape[0])

    for i in sample_indices:
        ax.plot(time_axis, paths[:, i], alpha=0.05, color="steelblue", linewidth=0.5)

    #Plot percentile lines on top
    ax.plot(time_axis, percentiles["p10"],  color="red",    linewidth=2, 
            linestyle="--", label="10th percentile (bad case)")
    ax.plot(time_axis, percentiles["p50"],  color="white",  linewidth=2.5, 
            label="50th percentile (median)")
    ax.plot(time_axis, percentiles["p90"],  color="green",  linewidth=2, 
            linestyle="--", label="90th percentile (good case)")

    ax.set_facecolor("#1e1e2e")
    fig.patch.set_facecolor("#1e1e2e")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")

    ax.set_title(f"Monte Carlo Simulation — {years} Year Portfolio Projection "
                 f"({paths.shape[1]:,} paths)", fontsize=13)
    ax.set_xlabel("Years")
    ax.set_ylabel("Portfolio Value (€)")
    ax.legend(facecolor="#2e2e3e", labelcolor="white")
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, p: f"€{x:,.0f}")
    )
    ax.set_ylim(0, np.percentile(paths[-1, :], 99) * 1.1)
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    filename = "charts/monte_carlo_simulation.png"
    plt.savefig(filename, dpi=150, facecolor=fig.get_facecolor())
    plt.close()

    console.print(f"[green]Simulation chart saved to {filename}[/green]")

    #Print summary statistics
    final_values = paths[-1, :] #Last row, every column.
    console.print(f"\n[bold cyan]Simulation Summary (after {years} years):[/bold cyan]")
    console.print(f"  Initial Portfolio Value:  €{initial_value:,.2f}")
    console.print(f"  [red]10th Percentile (bad):    €{np.percentile(final_values, 10):,.2f}[/red]")
    console.print(f"  Median outcome:           €{np.percentile(final_values, 50):,.2f}")
    console.print(f"  [green]90th Percentile (good):   €{np.percentile(final_values, 90):,.2f}[/green]")
    console.print(f"  Probability of profit:    "
                  f"{(final_values > initial_value).mean() * 100:.1f}%\n")