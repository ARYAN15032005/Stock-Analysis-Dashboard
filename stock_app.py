# -*- coding: utf-8 -*-
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Configuration
st.set_page_config(page_title="Market Sentiment Analyzer", layout="wide")

# Initialize Sentiment Analyzer
analyzer = SentimentIntensityAnalyzer()

def get_company_news(ticker):
    """Fetch company news from Google"""
    try:
        search_query = f"{ticker} stock news"
        url = f"https://www.google.com/search?q={search_query}&tbm=nws"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        return [item.text for item in soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")][:10]
    except Exception as e:
        st.error(f"News fetching failed for {ticker}: {e}")
        return []

def analyze_sentiment(text):
    return analyzer.polarity_scores(text)["compound"]

def institutional_ownership_analysis(companies):
    """Analyze institutional ownership"""
    high, medium, low = [], [], []
    ownership_data = {}
    
    for company in companies:
        try:
            stock = yf.Ticker(company)
            holders = stock.institutional_holders
            
            if holders is not None and not holders.empty:
                institutional_shares = holders['Shares'].sum()
                market_cap = stock.info.get('marketCap')
                price = stock.history(period='1d')['Close'].iloc[-1] if not stock.history(period='1d').empty else None
                
                if pd.notna(market_cap) and price and price > 0:
                    total_shares = market_cap / price
                    ownership = (institutional_shares / total_shares) * 100
                    ownership_data[company] = ownership
                    
                    if ownership >= 70: high.append(company)
                    elif ownership < 30: low.append(company)
                    else: medium.append(company)
            else:
                ownership_data[company] = 0  # Default value
                
        except Exception as e:
            st.error(f"Ownership analysis failed for {company}: {e}")
            ownership_data[company] = 0
            
    return high, medium, low, ownership_data

def get_financial_ratios(company):
    """Fetch and display financial ratios"""
    try:
        stock = yf.Ticker(company)
        info = stock.info
        return {
            'P/E Ratio': info.get('trailingPE', 'N/A'),
            'ROE': info.get('returnOnEquity', 'N/A'),
            'Debt/Equity': info.get('debtToEquity', 'N/A'),
            'EPS': info.get('trailingEps', 'N/A')
        }
    except Exception as e:
        st.error(f"Financial ratios failed for {company}: {e}")
        return {}

def get_market_fear_greed():
    """Get market sentiment from VIX"""
    try:
        vix = yf.Ticker("^VIX").history(period="1d")
        if not vix.empty:
            current_vix = vix['Close'].iloc[-1]
            if current_vix > 30:
                return "Extreme Fear", current_vix
            elif 20 <= current_vix <= 30:
                return "Fear", current_vix
            elif 15 <= current_vix < 20:
                return "Neutral", current_vix
            elif 10 <= current_vix < 15:
                return "Greed", current_vix
            else:
                return "Extreme Greed", current_vix
        else:
            st.error("No VIX data available")
            return "Unknown", None
    except Exception as e:
        st.error(f"VIX fetch failed: {str(e)}")
        return "Unknown", None
    return "Unknown", None  # Final fallback
def main():
    st.title("📈 Market Sentiment Analyzer")
    
    default_companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
                        "META", "NVDA", "BRK-B", "JPM", "V"]
    
    with st.sidebar:
        st.header("Configuration")
        companies = st.multiselect("Select Companies", default_companies, default=default_companies)
        analysis_types = st.multiselect("Select Analyses", [
            "News Sentiment", "Ownership Analysis", 
            "Financial Ratios", "Market Sentiment"
        ], default=["News Sentiment"])

    if "News Sentiment" in analysis_types:
        st.header("📰 News Sentiment Analysis")
        if not companies:
            st.warning("Please select companies in the sidebar")
            return
            
        company_data = []
        
        for company in companies:
            with st.spinner(f"Analyzing {company}..."):
                headlines = get_company_news(company)
                if not headlines:
                    continue
                
                sentiment_scores = [analyze_sentiment(h) for h in headlines]
                avg_sentiment = sum(sentiment_scores)/len(sentiment_scores)
                safety_score = ((avg_sentiment + 1)/2) * 100
                
                company_data.append({
                    "Company": company,
                    "Safety Score": safety_score,
                    "Average Sentiment": avg_sentiment,
                    "Headlines": headlines,
                    "Sentiment Scores": sentiment_scores
                })
        
        if company_data:
            st.subheader("Investment Safety Scores")
            fig, ax = plt.subplots(figsize=(10,6))
            ax.pie(
                [d["Safety Score"] for d in company_data],
                labels=[d["Company"] for d in company_data],
                autopct='%1.1f%%',
                startangle=140,
                colors=plt.cm.Paired.colors
            )
            ax.set_title("Investment Safety Distribution")
            st.pyplot(fig)
            
            for data in company_data:
                with st.expander(f"{data['Company']} - Safety Score: {data['Safety Score']:.1f}%"):
                    st.write(f"**Average Sentiment:** {data['Average Sentiment']:.2f}")
                    for idx, (h, s) in enumerate(zip(data["Headlines"], data["Sentiment Scores"])):
                        st.markdown(f"{idx+1}. {h} _(Sentiment: {s:.2f})_")

    if "Ownership Analysis" in analysis_types:
        st.header("🏦 Institutional Ownership Analysis")
        high, medium, low, ownership_data = institutional_ownership_analysis(companies)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High Ownership (≥70%)", len(high))
        with col2:
            st.metric("Medium Ownership (30-70%)", len(medium))
        with col3:
            st.metric("Low Ownership (<30%)", len(low))
        
        if ownership_data:
            fig, ax = plt.subplots(figsize=(12,6))
            ax.bar(ownership_data.keys(), ownership_data.values(), color='skyblue')
            ax.axhline(70, color='green', linestyle='--', label='High Ownership')
            ax.axhline(30, color='red', linestyle='--', label='Low Ownership')
            ax.set_ylabel("Ownership Percentage")
            ax.set_title("Institutional Ownership Breakdown")
            plt.xticks(rotation=45)
            st.pyplot(fig)

    if "Financial Ratios" in analysis_types:
        st.header("💹 Financial Ratios Analysis")
        selected_company = st.selectbox("Select Company", companies)
        
        if selected_company:
            with st.spinner(f"Fetching {selected_company} ratios..."):
                ratios = get_financial_ratios(selected_company)
                
                if ratios:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("P/E Ratio", 
                              f"{ratios['P/E Ratio']:.2f}" if isinstance(ratios['P/E Ratio'], float) else "N/A",
                              help="Price-to-Earnings Ratio")
                    col2.metric("ROE", 
                              f"{ratios['ROE']:.2%}" if isinstance(ratios['ROE'], float) else "N/A",
                              help="Return on Equity")
                    col3.metric("Debt/Equity", 
                              f"{ratios['Debt/Equity']:.2f}" if isinstance(ratios['Debt/Equity'], float) else "N/A",
                              help="Debt to Equity Ratio")
                    col4.metric("EPS", 
                              f"${ratios['EPS']:.2f}" if isinstance(ratios['EPS'], float) else "N/A",
                              help="Earnings Per Share")

    if "Market Sentiment" in analysis_types:
        st.header("📊 Overall Market Sentiment")
        sentiment, vix_value = get_market_fear_greed()
        
        if vix_value:
            col1, col2 = st.columns(2)
            col1.metric("Current VIX Index", f"{vix_value:.2f}")
            col2.metric("Market Sentiment", sentiment,
                      help="VIX Interpretation:\n"
                           ">30: Extreme Fear\n"
                           "20-30: Fear\n"
                           "15-20: Neutral\n"
                           "10-15: Greed\n"
                           "<10: Extreme Greed")
            
            # Sentiment gauge
            fig, ax = plt.subplots(figsize=(8,2))
            ax.barh([0], [vix_value], color='purple')
            ax.set_xlim(0, 50)
            ax.axvline(30, color='red', linestyle='--')
            ax.axvline(20, color='orange', linestyle='--')
            ax.axvline(15, color='yellow', linestyle='--')
            ax.axvline(10, color='green', linestyle='--')
            ax.set_title("VIX Fear & Greed Gauge")
            ax.set_yticks([])
            st.pyplot(fig)

if __name__ == "__main__":
    main()