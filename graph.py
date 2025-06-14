import yfinance as yf
import datetime
from dateutil.relativedelta import relativedelta
import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts  # Make sure you installed streamlit-echarts
from datetime import date
from datetime import datetime

def find_nearest_date(x_data, target_date_str):
    """Find the nearest date string in x_data to the given earnings date."""
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    x_dates = [datetime.strptime(d, "%Y-%m-%d") for d in x_data]
    nearest_date = min(x_dates, key=lambda d: abs(d - target_date))
    return nearest_date.strftime("%Y-%m-%d")

  
def return_historical_data(months: int, stock_symbol: str) -> pd.DataFrame:
    back_date = relativedelta(months=months)
    end_date = datetime.today().date()

    start_date = end_date - back_date
    stock_data = yf.download(
        tickers=stock_symbol,
        start=start_date,
        end=end_date,
        interval="1d",
        actions=True,
        progress=False
    )
    ticker_data = yf.Ticker(stock_symbol)
    
    print(ticker_data.get_info().keys())
    ticker_data.get_info()
    dates = {
        'start_date': start_date,
        'end_date': end_date
    }
    return stock_data, ticker_data ,dates

stock_symbol = "Rites.NS"
stock_data, ticker_data, dates = return_historical_data(months= 12, stock_symbol=stock_symbol)


x_data = stock_data.index.strftime('%Y-%m-%d').tolist() 
close_data = stock_data['Close'].squeeze().fillna(method='ffill').round(2).tolist()
today_str = date.today().strftime('%Y-%m-%d')
if x_data[-1] != today_str:
    x_data.append(today_str)
    try:
        current_price = ticker_data.info.get("currentPrice")
        if current_price is None:
            current_price = stock_data['Close'].iloc[-1]  
            
    except:
        current_price = stock_data['Close'].iloc[-1]  

    close_data.append(round(current_price, 2)) #Appendending the latest price of current day
    
    
dividend_data = stock_data['Dividends'].squeeze().fillna(0).tolist()
quaterly_earnings = ticker_data.quarterly_incomestmt.loc["Net Income"].dropna()



earnings_dates = quaterly_earnings.index.strftime('%Y-%m-%d').tolist()
earnings_values = quaterly_earnings.tolist()

print(earnings_dates ,"->", earnings_values)

mark_areas = []

for i in range(1, len(earnings_values)):
    current_val = earnings_values[i]
    prev_val = earnings_values[i - 1]
    date_str = earnings_dates[i]
  
    nearest_date = find_nearest_date(x_data, date_str)
    formated_nearest_date = datetime.strptime(nearest_date, "%Y-%m-%d")
    formated_nearest_date = formated_nearest_date.strftime('%d %b') 
    idx = x_data.index(nearest_date)

    start_index = max(idx - 1, 0)
    end_index = min(idx + 2, len(x_data) - 1)

    color = "rgba(144, 238, 144, 0.3)" if current_val > prev_val else "rgba(255, 99, 71, 0.3)"  # soft green / red

    mark_areas.append([
        {
            "name": f"{int(earnings_values[i])/1e7:.2f}Cr {'↑' if current_val > prev_val else '↓'} \n {formated_nearest_date}",
            "xAxis": x_data[start_index]
        },
        {
            "xAxis": x_data[end_index],
            "itemStyle": {"color": color},
            "label": {
                "color": "#ffffff",
                "fontWeight": "normal",
                "fontSize": 12
            },
                "tooltip": {
    "show": True,
    "formatter": "function(params) { return params[0].name; }"
}

        }
    ])
    
# Streamlit UI
st.header(f"Historical comparison for {stock_symbol} from {dates['start_date']} to {dates['end_date']}")
option = {
    
    "legend": {
    "data": [
        {
        "name": "Earnings Highlight",
        "icon": "rect"
        },
        {
        "name": "Dividend",
        "icon": "pin"
        }
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
    ]
    ,
    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "cross"}
    }, 
    
   "toolbox": {
        "show": True,
        "feature": {"saveAsImage": {}}
    },
        "grid": {
        "top": "15%",  # Pushes chart lower
        "left": "10%",
        "right": "5%",
        "bottom": "15%"
    },
        
    "dataZoom": [
    {
        "type": "slider",   # slider bar at bottom for scroll/zoom
        "start": 0,        # initial window start (%)
        "end": 100          # initial window end (%)
    },
    {
        "type": "inside"    
    }
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

        # 🎯 Series 1: Close Price (just the line)
        {
            "name": "Close Price",
            "type": "line",
            "smooth": True,
            "data": close_data,
            "lineStyle": {"width": 2},
            "itemStyle": {"color": "#5470C6"},
                "animation": True,
            "animationDuration": 1000,
            "animationEasing": "cubicOut",

        },

        # 💡 Series 2: Earnings Highlight (fake, only to control markArea visibility)
        {
            "name": "Earnings Highlight",
            "type": "custom",
            "renderItem": None,  # Dummy renderer
            "data": [0],  # Dummy data
            "markArea": {
                "data": mark_areas,
                "itemStyle": {"color": "rgba(144, 238, 144, 0.3)"},
                "label": {
                    "color": "#000",
                    "fontWeight": "bold",
                    "fontSize": 11
                }
            },
            "tooltip": {"show": False}  # No tooltip on dummy
        },

        # 💰 Series 3: Dividend Markers
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
                        "valueFormatter": None,
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
                        "borderRadius": 5,
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

 #Render chart using streamlit-echarts
 
st_echarts(options=option, height="425px", width="100%")

ticker_info = ticker_data.get_info()
key_ratios = {

 "P/E Ratio": ticker_info['trailingPE'],
'Beta': ticker_info['beta'],
'Price/Book': ticker_info['priceToBook'],
'ROE (%)': ticker_info['returnOnEquity'],
'Debt/Equity': ticker_info['debtToEquity'],
'Dividend Yield (%)': ticker_info['dividendYield']

}

print(key_ratios)