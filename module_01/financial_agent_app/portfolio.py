"""Simulated data and deterministic calculations for the Module 1 lab."""

from decimal import Decimal, DecimalException
from math import isfinite


_PRICES = {"LUMR": 245.50, "AAPL": 180.00, "GOOG": 140.00}


def get_stock_price(ticker: str) -> dict:
    """Look up a simulated USD quote, or return an error for an unknown ticker."""
    if not isinstance(ticker, str) or not ticker.strip():
        return {"error": "Provide a stock ticker."}
    symbol = ticker.strip().upper()
    if symbol not in _PRICES:
        return {"symbol": symbol, "error": f"No simulated quote for {symbol}."}
    return {
        "symbol": symbol,
        "price": _PRICES[symbol],
        "currency": "USD",
        "source": "simulated",
    }


def get_holdings() -> dict:
    """Return the simulated portfolio's share counts and uninvested USD cash."""
    return {
        "holdings": {"LUMR": 20, "AAPL": 100},
        "cash": 77_090,
        "currency": "USD",
        "source": "simulated",
    }


def _decimal_number(value: object) -> Decimal | None:
    if type(value) is int:
        return Decimal(value)
    if type(value) is float and isfinite(value):
        return Decimal(str(value))
    return None


def calculate_shock(
    holdings: dict[str, int],
    quotes: dict[str, float],
    cash: float,
    changes_pct: dict[str, float],
) -> dict:
    """Revalue shares after price-only shocks, with cash unchanged.

    Use uppercase ticker keys for all mappings. Holdings are whole share counts,
    quotes are prices in USD, and changes_pct uses percentages (e.g. -10 for a
    10% decline). A holding without a specified shock keeps its original price.
    """
    if not isinstance(holdings, dict) or not isinstance(quotes, dict):
        return {"error": "Provide holdings and quotes as ticker mappings."}
    if not isinstance(changes_pct, dict):
        return {"error": "Provide percentage changes as a ticker mapping."}
    for mapping in (holdings, quotes, changes_pct):
        for symbol in mapping:
            if (
                not isinstance(symbol, str)
                or not symbol
                or symbol != symbol.strip().upper()
            ):
                return {"error": "Use uppercase ticker keys without extra whitespace."}

    balance = _decimal_number(cash)
    if balance is None or balance < 0:
        return {"error": "Cash must be a finite, nonnegative amount."}

    for symbol, shares in holdings.items():
        if type(shares) is not int or shares < 0:
            return {"error": f"Shares for {symbol} must be a nonnegative integer."}
        if symbol not in quotes:
            return {"error": f"Missing quote for {symbol}."}

    prices = {}
    for symbol, quote in quotes.items():
        price = _decimal_number(quote)
        if price is None or price <= 0:
            return {"error": f"Quote for {symbol} must be finite and positive."}
        prices[symbol] = price

    changes = {}
    for symbol, change_pct in changes_pct.items():
        if symbol not in holdings:
            return {"error": f"Cannot shock {symbol}: it is not in the portfolio."}
        change = _decimal_number(change_pct)
        if change is None or change < -100:
            return {"error": f"Shock for {symbol} must be finite and at least -100%."}
        changes[symbol] = change

    # Decimal arithmetic preserves values such as 245.50 and -0.491 exactly.
    try:
        starting_value = balance
        ending_value = balance
        change_dollars = Decimal(0)
        for symbol, shares in holdings.items():
            position_value = shares * prices[symbol]
            price_change = changes.get(symbol, Decimal(0)) / 100
            starting_value += position_value
            ending_value += position_value * (1 + price_change)
            change_dollars += position_value * price_change

        if starting_value <= 0:
            return {"error": "The starting portfolio value must be positive."}

        result = {
            "starting_value": float(starting_value),
            "ending_value": float(ending_value),
            "change_dollars": float(change_dollars),
            "change_pct": float(100 * change_dollars / starting_value),
        }
    except (DecimalException, OverflowError):
        return {"error": "The scenario exceeds the supported numeric range."}
    if not all(isfinite(value) for value in result.values()):
        return {"error": "The scenario exceeds the supported numeric range."}
    return result
