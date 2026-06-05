import json
import os
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import yfinance as yf
from datetime import datetime

#Asset class
#Blueprint for single asset

@dataclass
class Asset:
    ticker: str           #Stock symbol e.g. "AAPL"
    sector: str           #e.g. "Technology"
    asset_class: str      #e.g. "Equity", "Bond", "Real Estate"
    quantity: float       #Number of shares/units owned
    purchase_price: float #Price paid per share at time of purchase

    @property
    def transaction_value(self) -> float:
        """What you paid in total when you bought this asset"""
        return self.quantity * self.purchase_price

    def current_price(self) -> float:
        """Fetch the live current price from Yahoo Finance"""
        ticker_data = yf.Ticker(self.ticker)
        price = ticker_data.fast_info.get("last_price")
        if price is None:
            raise ValueError(f"Could not fetch price for {self.ticker}")
        return round(price, 2) #I round the price to 2 decimal places

    def current_value(self) -> float:
        """Current market value of this position"""
        return round(self.quantity * self.current_price(), 2) #Again, I round the value to 2 decimal places

    def profit_loss(self) -> float:
        """How much money you made or lost on this asset"""
        return round(self.current_value() - self.transaction_value, 2) #I round the profit/loss to 2 decimal places

    def profit_loss_pct(self) -> float:
        """Profit/loss as a percentage of what you paid"""
        return round((self.profit_loss() / self.transaction_value) * 100, 2) #I round the percentage to 2 decimal places, will do that for all remainder functions as well

    def to_dict(self) -> dict:
        """Convert asset to dictionary so we can save it to a file"""
        return {
            "ticker": self.ticker,
            "sector": self.sector,
            "asset_class": self.asset_class,
            "quantity": self.quantity,
            "purchase_price": self.purchase_price
        }
    
    @staticmethod  #I use a static method here because it doesn't need to access any instance variables, it just takes a dictionary and returns an Asset object
    def from_dict(data: dict) -> "Asset":
        """Recreate an Asset object from a saved dictionary"""
        return Asset(
            ticker=data["ticker"],
            sector=data["sector"],
            asset_class=data["asset_class"],
            quantity=data["quantity"],
            purchase_price=data["purchase_price"]
        )
    
#Portfolio class
#Blueprint for the whole portfolio, which can contain multiple assets


class Portfolio:
    def __init__(self, filepath: str = "data/portfolio.json"):
        self.filepath = filepath      #Where we save/load the portfolio
        self.assets: list[Asset] = [] #List of all Asset objects
        self.load()                   #Load existing data on startup

    def add_asset(self, asset: Asset) -> None:
        """Add a new asset to the portfolio"""
        #Check if ticker already exists — update quantity if so
        for existing in self.assets:
            if existing.ticker == asset.ticker:
                existing.quantity += asset.quantity #If the asset already exists, we just update the quantity by adding the new quantity to the existing one
                self.save()
                return
        self.assets.append(asset) #If the asset is not found, we add the whole object includong ticker, sector, asset class, quantity and purchase price
        self.save()

    def remove_asset(self, ticker: str) -> bool:
        """Remove an asset by ticker, returns True if found"""
        for asset in self.assets:
            if asset.ticker == ticker.upper():
                self.assets.remove(asset)
                self.save()
                return True
        return False

    def get_asset(self, ticker: str) -> Optional[Asset]:
        """Find and return a single asset by ticker"""
        for asset in self.assets:
            if asset.ticker == ticker.upper():
                return asset
        return None

    def total_transaction_value(self) -> float:
        """Total amount invested across all assets"""
        return round(sum(a.transaction_value for a in self.assets), 2)

    def total_current_value(self) -> float:
        """Total current market value of entire portfolio"""
        return round(sum(a.current_value() for a in self.assets), 2)

    def total_profit_loss(self) -> float:
        """Total profit or loss across entire portfolio"""
        return round(self.total_current_value() - self.total_transaction_value(), 2)

    def asset_weights(self) -> dict:
        """
        Weight of each asset as percentage of total portfolio value
        e.g. {"AAPL": 35.2, "ASML": 28.1, ...}
        """
        total = self.total_current_value()
        if total == 0:
            return {}
        return {
            a.ticker: round((a.current_value() / total) * 100, 2)
            for a in self.assets
        }

    def weights_by_sector(self) -> dict:
        """
        Weight of each sector as percentage of total portfolio value
        e.g. {"Technology": 63.3, "Healthcare": 20.1, ...}
        """
        total = self.total_current_value()
        if total == 0:
            return {}
        sector_values = {}
        for a in self.assets:
            sector_values[a.sector] = sector_values.get(a.sector, 0) + a.current_value()
        return {
            sector: round((value / total) * 100, 2)
            for sector, value in sector_values.items()
        }

    def weights_by_asset_class(self) -> dict:
        """
        Weight of each asset class as percentage of total portfolio value
        e.g. {"Equity": 80.0, "Bond": 20.0}
        """
        total = self.total_current_value()
        if total == 0:
            return {}
        class_values = {}
        for a in self.assets:
            class_values[a.asset_class] = class_values.get(a.asset_class, 0) + a.current_value()
        return {
            asset_class: round((value / total) * 100, 2)
            for asset_class, value in class_values.items()
        }

    def save(self) -> None:
        """Save the entire portfolio to a JSON file"""
        os.makedirs("data", exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump([a.to_dict() for a in self.assets], f, indent=4)

    def load(self) -> None:
        """Load portfolio from JSON file if it exists"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                data = json.load(f)
                self.assets = [Asset.from_dict(d) for d in data]
