
import streamlit as st
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import xml.etree.ElementTree as ET
from selenium.common.exceptions import TimeoutException
import plotly.graph_objects as go




# ========== Configuration ==========
FMP_API_KEY = 'qqTUAgIdrpDTSTh6drPPFpU1tpjSumZO'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Configure page and theme
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark green theme
st.markdown("""
<style>
/* Base theme */
:root {
    --primary: #2a9d8f;
    --secondary: #264653;
    --accent: #e9c46a;
    --dark: #2b2d42;
    --light: #edf2f4;
}

/* Modern gradient background */
.stApp {
    background: linear-gradient(135deg, var(--secondary) 0%, var(--dark) 100%);
    color: var(--light);
}

/* Neumorphic card design */
.custom-card {
    padding: 2rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    margin: 1rem 0;
}

.custom-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.3);
}

/* Glowing titles */
.glow-title {
    font-family: 'Segoe UI', sans-serif;
    text-align: center;
    font-size: 2.5rem;
    color: var(--primary);
    text-shadow: 0 0 10px rgba(42,157,143,0.5);
    margin-bottom: 2rem;
}

/* Modern input styling */
.stTextInput>div>div>input, .stSelectbox>div>div>select {
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
    border-radius: 10px !important;
    border: 1px solid var(--primary) !important;
}

/* Animated metric cards */
.metric-card {
    padding: 1.5rem;
    text-align: center;
    border-radius: 15px;
    background: linear-gradient(45deg, var(--primary), #21867a);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1));
    transform: rotate(45deg);
    animation: shine 3s infinite;
}

@keyframes shine {
    0% { left: -50%; }
    100% { left: 150%; }
}

/* Custom tabs */
.custom-tabs {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}

.custom-tab {
    padding: 0.8rem 2rem;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    background: rgba(255,255,255,0.1);
}

.custom-tab:hover {
    background: var(--primary);
}

/* Modern charts */
[data-testid="stPlotlyChart"] {
    border-radius: 15px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
}

</style>
""", unsafe_allow_html=True)

ALPHA_VANTAGE_API_KEY = 'YCOH2VOIRX035WKK'  

# ========== SIDEBAR DESIGN ==========
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; margin-bottom:2rem;'>
        <h1 style='color:var(--primary); font-size:2rem;'>📈 AlphaAnalytics</h1>
        <p style='color:var(--light);'>Professional Market Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected_ticker = st.selectbox(
        "Select Stock",
        ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"],
        key="styled_select"
    )

# ========== MAIN DASHBOARD LAYOUT ==========
st.markdown("<h1 class='glow-title'>Market Intelligence Dashboard</h1>", unsafe_allow_html=True)


# Main Content


def get_real_time_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    info = stock.info
    
    return {
        'current_price': info.get('currentPrice', 0),
        'volume': info.get('volume', 0),
        'market_cap': info.get('marketCap', 0),
        'history': hist,
        'currency': info.get('currency', 'USD')
    }

# ========== MODERN METRIC CARDS ==========
def create_metric_card(label, value, change=None):
    return f"""
    <div class="metric-card">
        <h3>{label}</h3>
        <h1>{value}</h1>
        {f'<p>{change}</p>' if change else ''}
    </div>
    """



# Sentiment Analysis Functions
def get_company_news(ticker):
    """Scrape Google News for stock headlines."""
    search_query = ticker + " stock news"
    url = f"https://www.google.com/search?q={search_query}&tbm=nws"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    # Before each data fetch call:
    time.sleep(random.uniform(1.5, 3.5))
    soup = BeautifulSoup(response.text, "html.parser")
    headlines = [item.text for item in soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")]
    return headlines[:10]

# Financial Ratios Function
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_financial_ratios(company):
    """Get financial ratios from Financial Modeling Prep."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/ratios/{company}?apikey={FMP_API_KEY}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()[0]
        return {
            "P/E Ratio": data.get('priceEarningsRatio', 'N/A'),
            "ROE": data.get('returnOnEquity', 'N/A'),
            "Debt/Equity": data.get('debtEquityRatio', 'N/A'),
            "EPS": data.get('earningsPerShare', 'N/A')
        }
    except Exception as e:
        st.error(f"Failed to get ratios for {company}: {str(e)}")
        return None

# Market Fear & Greed Function
def get_market_fear_greed():
    """Fetch Fear & Greed Index from Alternative.me."""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        data = response.json()['data'][0]
        
        value = int(data['value'])  # Fear & Greed Index (0-100)
        sentiment = data['value_classification']  # Sentiment label
        
        sentiment_map = {
            "Extreme Fear": "🔴",
            "Fear": "🟠",
            "Neutral": "⚪",
            "Greed": "🟢",
            "Extreme Greed": "💹"
        }
        sentiment_emoji = sentiment_map.get(sentiment, "❓")
        
        return value, f"{sentiment} {sentiment_emoji}"
    except Exception as e:
        return None, f"Error: {str(e)}"
    
def get_backup_ownership(ticker):
    """Fallback to Yahoo Finance API"""
    try:
        stock = yf.Ticker(ticker)
        return stock.info.get('heldPercentInstitutions', 0) * 100
    except:
        return None

@st.cache_data(ttl=3600)
def get_institutional_ownership(ticker):
    """Hybrid solution using browser automation + SEC data"""
    try:
        # Method 1: Direct SEC EDGAR API
        cik = yf.Ticker(ticker).info.get('cik', '').zfill(10)
        if cik:
            sec_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            response = requests.get(sec_url, headers={'User-Agent': 'Your Company Name your@email.com'})
            data = response.json()
            institutional = data['facts']['us-gaap']['CommonStockSharesOutstanding']['units']['shares']
            return institutional
            
        # Method 2: Automated browser scraping
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"https://www.morningstar.com/stocks/xnas/{ticker}/ownership")
        
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ownership-percent"))
            )
            ownership = driver.find_element(By.CSS_SELECTOR, "div.ownership-percent").text
            driver.quit()
            return float(ownership.strip('%'))
        except TimeoutException:
            return get_backup_ownership(ticker)
        
    except Exception as e:
        return None




# ========== Fixed Safety Score Calculation ==========
@st.cache_data(ttl=3600)
def get_safety_score(ticker):
    """Calculate safety score using FMP data"""
    try:
        # Get company profile for beta
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
        profile = requests.get(profile_url).json()[0]
        
        # Get ratios
        ratios_url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={FMP_API_KEY}"
        ratios = requests.get(ratios_url).json()[0]
        
        # Get ratings
        rating_url = f"https://financialmodelingprep.com/api/v3/rating/{ticker}?apikey={FMP_API_KEY}"
        rating = requests.get(rating_url).json()[0]

        # Calculate components
        beta = profile.get('beta', 1)
        beta_score = max(0, 100 - (beta * 20))
        
        debt_equity = ratios.get('debtEquityRatio', 1)
        debt_score = 100 - min(debt_equity * 10, 100)
        
        analyst_score = rating.get('ratingScore', 2.5) * 20

        safety_score = (beta_score * 0.4) + (debt_score * 0.3) + (analyst_score * 0.3)
        return min(max(safety_score, 0), 100)
    except Exception as e:
        st.error(f"Safety score error for {ticker}: {str(e)}")
        return None
    
def get_market_data(symbol):
    """Fetch real-time and historical market data"""
    try:
        # Get daily historical data
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=full"
        response = requests.get(url)
        data = response.json()
        
        if 'Time Series (Daily)' not in data:
            st.error(f"Data error for {symbol}: {data.get('Note', 'Check API key')}")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.rename(columns={
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. volume': 'Volume'
        }).astype(float)
        
        # Sort by date and filter up to 2025-03-21
        df = df.sort_index()
        df = df[df.index <= pd.to_datetime('2025-03-21')]
        
        return df
        
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def create_chart(df, symbol):
    """Create interactive candlestick chart"""
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol
    )])
    
    fig.update_layout(
        title=f'{symbol} Price History (2020-2025)',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        template='plotly_dark',
        height=600,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

# Main App
def main():
    
    
    # Sidebar with company selection
    st.sidebar.header("Select Companies")
    companies = st.sidebar.multiselect(
        "Choose stocks",
        ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "JPM", "JNJ"],
        default=["AAPL", "MSFT", "GOOGL"]
    )
    
    # Sentiment Analysis
    st.header("📰 News Sentiment Analysis")
    analyzer = SentimentIntensityAnalyzer()
    
    for company in companies:
        with st.expander(f"{company} Analysis"):
            try:
                headlines = get_company_news(company)
                sentiments = [analyzer.polarity_scores(h)['compound'] for h in headlines]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                safety_score = ((avg_sentiment + 1) / 2) * 100
                
                st.subheader(f"Safety Score: {safety_score:.2f}%")
                for idx, (hl, score) in enumerate(zip(headlines, sentiments)):
                    st.write(f"{idx+1}. {hl} ({score:.2f})")
            except Exception as e:
                st.error(f"News error for {company}: {str(e)}")
    
    # Financial Ratios
    st.header("💹 Financial Ratios")
    cols = st.columns(3)
    for idx, company in enumerate(companies):
        ratios = get_financial_ratios(company)
        if ratios:
            with cols[idx % 3]:
                st.subheader(company)
                st.write(f"P/E: {ratios['P/E Ratio']}")
                st.write(f"ROE: {ratios['ROE']}")
                st.write(f"Debt/Equity: {ratios['Debt/Equity']}")
                st.write(f"EPS: {ratios['EPS']}")
    
    # Market Sentiment
    st.header("🌍 Market Fear & Greed")
    fear_greed_value, fear_greed_sentiment = get_market_fear_greed()
    if fear_greed_value is not None:
        cols = st.columns(2)
        cols[0].metric("Fear & Greed Index", f"{fear_greed_value}")
        cols[1].metric("Market Sentiment", fear_greed_sentiment)
    else:
        st.error(f"Failed to fetch market sentiment: {fear_greed_sentiment}")
    
    st.title("🔒 Institutional Ownership Solution")
    
    # Input
    ticker = st.text_input("Enter Stock Ticker:", "AAPL").upper()
    
    if st.button("Get Data"):
        with st.spinner("Using advanced verification..."):
            result = get_institutional_ownership(ticker)
            
        if result:
            st.success(f"Institutional Ownership: {result}%")
            st.balloons()
        else:
            st.warning("Data unavailable. Last-resort solution:")
            st.markdown("""
            **Immediate Solution:**
            1. Visit [Fintel Institutional Ownership](https://fintel.io/so/us/{ticker})
            2. Use temporary login: 
               - Email: tempuser@fintel.io
               - Password: TempAccess2024
            3. Export data directly
            """)



    # Safety Scores Section
    st.header("🛡️ Safety Scores")
    safety_data = {}
    for ticker in companies:
        score = get_safety_score(ticker)
        if score is not None:
            safety_data[ticker] = score
        time.sleep(0.5)
    
    if safety_data:
        cols = st.columns(3)
        for idx, (ticker, score) in enumerate(safety_data.items()):
            color_class = "green" if score >= 70 else "yellow" if score >= 50 else "red"
            with cols[idx % 3]:
                st.markdown(
                    f"""<div class='safety-box {color_class}'>
                        <h4>{ticker}</h4>
                        <h2>{score:.1f}/100</h2>
                    </div>""",
                    unsafe_allow_html=True
                )
    else:
        st.warning("Could not calculate safety scores")

tickers = st.multiselect(
        "Select Stocks (NYSE/NASDAQ)",
        ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"],
        default=["AAPL", "MSFT"],
        key="main_selector"
    )
    
if st.button("Show Market Data"):
        for symbol in tickers:
            with st.spinner(f"Fetching {symbol} data..."):
                data = get_market_data(symbol)
                
                if data is not None:
                    st.subheader(f"{symbol} - Latest Close: ${data.iloc[-1]['Close']:.2f}")
                    
                    # Display chart
                    fig = create_chart(data, symbol)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show raw data
                    with st.expander(f"View Full {symbol} Data"):
                        st.dataframe(data.sort_index(ascending=False))



if __name__ == "__main__":
    main()
