# -*- coding: utf-8 -*-
"""Stock Analysis Streamlit App"""
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pytrends.request import TrendReq
import numpy as np
import time

# Page configuration
st.set_page_config(
    page_title="Stock Analyzer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {padding: 2rem 5rem;}
    .stProgress > div > div > div {background-color: #2ecc71;}
    .st-bb {background-color: transparent;}
    .st-at {background-color: #2ecc71;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'companies' not in st.session_state:
    st.session_state.companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# Sidebar controls
with st.sidebar:
    st.title("⚙️ Controls")
    st.session_state.companies = st.text_input(
        "Enter Stock Tickers (comma-separated)",
        value=", ".join(st.session_state.companies)
    ).upper().split(', ')
    analysis_type = st.selectbox(
        "Analysis Mode",
        ["Full Analysis", "News & Sentiment", "Market Trends"]
    )
    start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("today"))

# Cached functions
@st.cache_data(show_spinner=False, ttl=3600)
def get_company_news(ticker):
    """Fetch recent news headlines for a given ticker"""
    try:
        search_query = f"{ticker} stock news"
        url = f"https://www.google.com/search?q={search_query}&tbm=nws"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return [item.text for item in soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")][:10]
    except Exception as e:
        st.error(f"Error fetching news for {ticker}: {str(e)}")
        return []

@st.cache_data(show_spinner=False)
def analyze_sentiment(text):
    """Analyze text sentiment using VADER"""
    return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]

@st.cache_data(show_spinner=False, ttl=10800)
def get_google_trends(keywords):
    """Fetch Google Trends data"""
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,30))
        trend_data = pd.DataFrame()
        for keyword in keywords:
            pytrends.build_payload([keyword], cat=0, timeframe='today 12-m')
            data = pytrends.interest_over_time()
            if not data.empty:
                data['Keyword'] = keyword
                trend_data = pd.concat([trend_data, data])
            time.sleep(1)  # Rate limiting
        return trend_data
    except Exception as e:
        st.error(f"Trends API Error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def get_stock_data(companies, start_date, end_date):
    """Fetch historical stock data"""
    try:
        combined = pd.DataFrame()
        for ticker in companies:
            data = yf.download(ticker, start=start_date, end=end_date)
            if not data.empty:
                data['Ticker'] = ticker
                combined = pd.concat([combined, data])
        return combined.reset_index().set_index(['Ticker', 'Date'])
    except Exception as e:
        st.error(f"Stock Data Error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def institutional_ownership_analysis(companies):
    """Analyze institutional ownership"""
    high, med, low = [], [], []
    ownership = {}
    for ticker in companies:
        try:
            stock = yf.Ticker(ticker)
            holders = stock.institutional_holders
            if holders is not None and not holders.empty:
                total_shares = stock.info.get('sharesOutstanding', 0)
                inst_shares = holders['Shares'].sum()
                if total_shares > 0:
                    perc = (inst_shares / total_shares) * 100
                    ownership[ticker] = perc
                    if perc >= 70: high.append(ticker)
                    elif perc < 30: low.append(ticker)
                    else: med.append(ticker)
        except Exception as e:
            st.warning(f"Ownership data unavailable for {ticker}")
    return high, med, low, ownership

def main():
    """Main app function"""
    st.title("🚀 Stock Analysis Dashboard")
    
    with st.spinner("Initializing analysis..."):
        # Stock Price Visualization
        st.header("📈 Price Movement Analysis")
        stock_data = get_stock_data(st.session_state.companies, start_date, end_date)
        if not stock_data.empty:
            fig, ax = plt.subplots(figsize=(14, 6))
            for ticker in st.session_state.companies:
                try:
                    ticker_data = stock_data.xs(ticker, level='Ticker')
                    ax.plot(ticker_data.index, ticker_data['Close'], label=ticker)
                except KeyError:
                    continue
            ax.set_title("Comparative Stock Performance")
            ax.legend()
            st.pyplot(fig)
        else:
            st.warning("No stock data available for selected tickers")
        
        # Ownership Metrics
        st.header("🏦 Institutional Ownership")
        high, med, low, ownership = institutional_ownership_analysis(st.session_state.companies)
        cols = st.columns(3)
        metrics = [
            ("High (>70%)", len(high), "#27ae60"),
            ("Medium (30-70%)", len(med), "#f1c40f"),
            ("Low (<30%)", len(low), "#e74c3c")
        ]
        for col, (label, value, color) in zip(cols, metrics):
            col.markdown(f"<h3 style='color:{color}'>{label}<br>{value}</h3>", unsafe_allow_html=True)
        
        # Sentiment Analysis
        if analysis_type in ["Full Analysis", "News & Sentiment"]:
            st.header("📰 News Sentiment Analysis")
            for ticker in st.session_state.companies:
                with st.expander(f"{ticker} News Analysis", expanded=False):
                    news = get_company_news(ticker)
                    if news:
                        scores = [analyze_sentiment(n) for n in news]
                        avg = np.mean(scores) if scores else 0
                        st.subheader(f"Average Sentiment: {avg:.2f}")
                        for i, (n, s) in enumerate(zip(news, scores)):
                            st.write(f"**{i+1}.** {n}")
                            st.progress((s + 1) / 2)
                    else:
                        st.warning("No news articles found")
        
        # Market Trends
        if analysis_type in ["Full Analysis", "Market Trends"]:
            st.header("🌍 Market Trends Analysis")
            trends = get_google_trends(["stocks", "investing", "recession"])
            if not trends.empty:
                st.line_chart(trends[['stocks', 'investing', 'recession']])
            else:
                st.info("Trends data currently unavailable")

if __name__ == "__main__":
    main()
    st.success("Analysis complete! Explore the tabs above.")
    st.markdown("---")
    st.markdown("**Note:** Data updates may take several minutes. Refresh for latest results.")