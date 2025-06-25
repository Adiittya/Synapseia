import yfinance as yf
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from datetime import datetime
import streamlit as st
from streamlit_echarts import st_echarts
from datetime import date
import ast


@st.cache_data(show_spinner="📦 Fetching stock data...")
def return_historical_data(months: int, stock_symbol: str):
    from datetime import date
    from dateutil.relativedelta import relativedelta

    back_date = relativedelta(months=months)
    end_date = date.today()
    start_date = end_date - back_date

    stock_data = yf.download(
        tickers=stock_symbol,
        start=start_date,
        end=end_date,
        interval="1d",
        actions=True,
        progress=False,
        multi_level_index= False
    )

    try:
        if not stock_data.empty:
            stock_data.index = pd.to_datetime(stock_data.index, errors='coerce')
            stock_data = stock_data.dropna(subset=["Close"])
        else:
            print(f"[⚠️] No data fetched for {stock_symbol}")
    except Exception as e:
        print(f"[❌ Error cleaning data]: {e}")

        stock_data = pd.DataFrame()

    return stock_data, {"start_date": start_date, "end_date": end_date}

def get_key_ratios(ticker_info: dict):
    return {
        "P/E Ratio": ticker_info.get('trailingPE'),
        "Beta": ticker_info.get('beta'),
        "Price/Book": ticker_info.get('priceToBook'),
        "ROE (%)": ticker_info.get('returnOnEquity'),
        "Debt/Equity": ticker_info.get('debtToEquity'),
        "Dividend Yield (%)": ticker_info.get('dividendYield')
    }


def find_nearest_date(x_data, target_date_str):
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    x_dates = [datetime.strptime(d, "%Y-%m-%d") for d in x_data]
    nearest_date = min(x_dates, key=lambda d: abs(d - target_date))
    return nearest_date.strftime("%Y-%m-%d")

def build_earnings_mark_areas(x_data, earnings_dates, earnings_values):
    mark_areas = []

    for i in range(1, len(earnings_values)):
        current_val = earnings_values[i]
        prev_val = earnings_values[i - 1]
        date_str = earnings_dates[i]

        nearest_date = find_nearest_date(x_data, date_str)
        formatted_date = datetime.strptime(nearest_date, "%Y-%m-%d").strftime('%d %b')
        idx = x_data.index(nearest_date)
        start_index = max(idx - 1, 0)
        end_index = min(idx + 2, len(x_data) - 1)

        color = "rgba(144, 238, 144, 0.3)" if current_val > prev_val else "rgba(255, 99, 71, 0.3)"

        mark_areas.append([
            {
                "name": f"{int(current_val)/1e7:.2f}Cr {'↑' if current_val > prev_val else '↓'}\n{formatted_date}",
                "xAxis": x_data[start_index]
            },
            {
                "xAxis": x_data[end_index],
                "itemStyle": {"color": color},
                "label": {
                    "color": "#ffffff",
                    "fontWeight": "normal",
                    "fontSize": 12
                }
            }
        ])

    return mark_areas


def build_chart_options(x_data, close_data, dividend_data, mark_areas):
    return {
        "legend": {
            "data": [
                {"name": "Earnings Highlight", "icon": "rect"},
                {"name": "Dividend", "icon": "pin"}
            ],
            "textStyle": {
                "color": "#FFFFFF",
                "fontSize": 12
            }
        },
        "color": [
            "rgba(144, 238, 144, 0.6)", 
            "#FFD700",
            "#5470C6"
        ],
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"}
        },
        "toolbox": {
            "show": True,
            "feature": {"saveAsImage": {}}
        },
        "grid": {
            "top": "15%",
            "left": "10%",
            "right": "5%",
            "bottom": "15%"
        },
        "dataZoom": [
            {"type": "slider", "start": 0, "end": 100},
            {"type": "inside"}
        ],
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": x_data
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"formatter": "{value} ₹"},
            "axisPointer": {"snap": True}
        },
        "series": [
            {
                "name": "Close Price",
                "type": "line",
                "smooth": True,
                "data": close_data,
                "lineStyle": {"width": 2},
                "itemStyle": {"color": "#5470C6"},
                "animation": True,
                "animationDuration": 1000,
                "animationEasing": "cubicOut"
            },
            {
                "name": "Earnings Highlight",
                "type": "custom",
                "renderItem": None,
                "data": [0],
                "markArea": {
                    "data": mark_areas,
                    "itemStyle": {"color": "rgba(144, 238, 144, 0.3)"},
                    "label": {
                        "color": "#000",
                        "fontWeight": "bold",
                        "fontSize": 11
                    }
                },
                "tooltip": {"show": False}
            },
            {
                "name": "Dividend",
                "type": "scatter",
                "symbol": "pin",
                "symbolSize": 25,
                "z": 10,
                "data": [
                    {
                        "value": [x_data[i], close_data[i]],
                        "itemStyle": {
                            "color": "#FFD700",
                            "borderColor": "#000",
                            "borderWidth": 1
                        },
                        "tooltip": {
                            "formatter": f"<b>{x_data[i]}</b><br/>Close Price: ₹{close_data[i]:.2f}<br/>Dividend: ₹{dividend_data[i]:.2f}"
                        },
                        "label": {
                            "show": True,
                            "position": "top",
                            "formatter": f"₹{dividend_data[i]:.2f}",
                            "color": "#333",
                            "fontSize": 10,
                            "backgroundColor": "#fff",
                            "padding": 4,
                            "borderRadius": 5
                        }
                    }
                    for i in range(len(dividend_data)) if dividend_data[i] > 0
                ],
                "tooltip": {
                    "trigger": "item"
                }
            }
        ]
    }


def generate_multiple_charts(stock_symbols: list):

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

    try:
        # Generate a unique key based on the stock list
        radio_key = f"stock_select_radio_{'_'.join(stock_symbols)}"
        selected_stock = st.radio("📌 Select a Stock", stock_symbols, key=radio_key)

        # st.write(f"📦 Selected stock: `{selected_stock}`")
        stock_data, dates = return_historical_data(months=12, stock_symbol=selected_stock)
        
        ticker_data = yf.Ticker(selected_stock)
        
        stock_data.index = pd.to_datetime(stock_data.index, errors='coerce')
        x_data = stock_data.index.strftime('%Y-%m-%d').tolist()
        close_data = stock_data['Close'].squeeze().fillna(method='ffill').round(2).tolist()
        dividend_data = stock_data['Dividends'].squeeze().fillna(0).tolist()

        today_str = date.today().strftime('%Y-%m-%d')
        if x_data[-1] != today_str:
            x_data.append(today_str)
            current_price = ticker_data.info.get("currentPrice") or stock_data['Close'].iloc[-1]
            close_data.append(round(current_price, 2))

        quaterly_earnings = ticker_data.quarterly_incomestmt.loc["Net Income"].dropna()
        earnings_dates = quaterly_earnings.index.strftime('%Y-%m-%d').tolist()
        earnings_values = quaterly_earnings.tolist()
        mark_areas = build_earnings_mark_areas(x_data, earnings_dates, earnings_values)
        st.sidebar.info("""
🧠 **What You See:**
- 📊 Price trend over past 1 year
- 📌 Key earnings and dividend events
- 📈 Financial ratios like P/E, ROE, D/E

Use these tools to make better stock decisions.

🛠️ Powered by SYNAPSEIA
""")
        st.header(f"📈 {selected_stock} Price Trend with Earnings & Dividends")
        st.caption("This chart includes dividend payouts (🟡), earnings highlights (🟩), and major stock moves.")
        option = build_chart_options(x_data, close_data, dividend_data, mark_areas)
        st_echarts(options=option, height="500px", width="100%")

        ticker_info = ticker_data.info
        key_ratios = get_key_ratios(ticker_info)
        st.subheader("📊 Key Financial Metrics (Live Extract)")
        st.json(key_ratios)

    except Exception as e:
        st.error(f"❌ Something broke inside generate_multiple_charts: {e}")


# stock_list = ['TATAMOTORS.NS', 'INFY.NS', 'RELIANCE.NS', 'ICICIBANK.NS']
# generate_multiple_charts(stock_list)



