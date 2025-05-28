import yfinance as yf
import ast

import yfinance as yf
import ast
from typing import List, Union, Dict

def get_stock_summary(stock_symbols: Union[str, List[str]]) -> List[Dict]:
    """
    Fetch summary info for a list of stock symbols using yfinance.

    Args:
        stock_symbols (str or list): Comma-separated string or list of stock symbols

    Returns:
        List of dicts containing stock info or error messages
    """

    # Normalize input to a list of symbols
    if isinstance(stock_symbols, str):
        try:
            stock_symbols = ast.literal_eval(stock_symbols)
            if not isinstance(stock_symbols, list):
                stock_symbols = [str(stock_symbols)]
        except (ValueError, SyntaxError):
            stock_symbols = [s.strip() for s in stock_symbols.split(',') if s.strip()]
    elif not isinstance(stock_symbols, list):
        # If not list or str, return error in list form
        return [{"error": "Input must be a list or a string."}]

    if not stock_symbols:
        return [{"error": "No valid stock symbols provided."}]

    summaries = []
    for symbol in stock_symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            current_price = info.get("currentPrice")
            previous_close = info.get("previousClose")
            open_price = info.get("open")
            day_high = info.get("dayHigh")
            day_low = info.get("dayLow")
            volume = info.get("volume")
            market_cap = info.get("marketCap")
            pe_ratio = info.get("trailingPE")
            beta = info.get("beta")
            week_52_high = info.get("fiftyTwoWeekHigh")
            week_52_low = info.get("fiftyTwoWeekLow")
            sector = info.get("sector")
            industry = info.get("industry")

            percent_change = (
                round(((current_price - previous_close) / previous_close) * 100, 2)
                if current_price is not None and previous_close is not None and previous_close != 0 else None
            )

            summaries.append({
                "symbol": symbol,
                "current_price": current_price,
                "day_high": day_high,
                "day_low": day_low,
                "open": open_price,
                "previous_close": previous_close,
                "volume": volume,
                "percent_change": percent_change,
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "beta": beta,
                "52_week_high": week_52_high,
                "52_week_low": week_52_low,
                "sector": sector,
                "industry": industry
            })
        except Exception as e:
            summaries.append({
                "symbol": symbol,
                "error": str(e)
            })

    return summaries

# # Example usage:
# symbols = ["TATAMOTORS.NS", "RELIANCE.NS", "INFY.NS"]
# print(get_stock_summary(symbols))
