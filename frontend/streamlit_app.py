"""
AI Financial Advisor - Streamlit Web Application.

Interactive web application for financial advisory using Streamlit.
Connects to FastAPI backend for data and analysis.

Run with:
    streamlit run frontend/streamlit_app.py
    
Or with custom port:
    streamlit run frontend/streamlit_app.py --server.port 8501
"""

import os

import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="AI Financial Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_HEALTH_ENDPOINT = f"{BACKEND_URL}/health"


def check_backend_health() -> bool:
    """
    Check if backend service is running and healthy.
    
    Returns:
        bool: True if backend is healthy, False otherwise
    """
    try:
        response = requests.get(API_HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def main():
    """Main application entry point."""
    # Sidebar navigation
    st.sidebar.title("AI Financial Advisor")
    st.sidebar.write("💰 Your Intelligent Financial Guide")

    page = st.sidebar.radio(
        "Navigate",
        [
            "Home",
            "Portfolio Analysis",
            "Risk Assessment",
            "Insights",
            "About",
        ],
    )

    # Health check indicator
    backend_healthy = check_backend_health()
    status_color = "🟢" if backend_healthy else "🔴"
    st.sidebar.write(f"{status_color} Backend: {'Healthy' if backend_healthy else 'Offline'}")

    if page == "Home":
        show_home()
    elif page == "Portfolio Analysis":
        show_portfolio_analysis()
    elif page == "Risk Assessment":
        show_risk_assessment()
    elif page == "Insights":
        show_insights()
    elif page == "About":
        show_about()


def show_home():
    """Display home page."""
    st.title("Welcome to AI Financial Advisor 💰")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        ## Your Intelligent Financial Guide

        AI Financial Advisor helps you make better financial decisions with:

        - 📊 **Portfolio Analysis** - Deep insights into your investments
        - ⚖️ **Risk Assessment** - Understand your risk exposure
        - 💡 **Smart Insights** - AI-powered financial recommendations
        - 📈 **Performance Tracking** - Monitor your wealth growth

        ### Quick Links
        - [API Documentation](http://localhost:8000/docs)
        - [Source Code](https://github.com/yourorg/smartbridge)
        - [Documentation](./docs/quick_start.md)
        """
        )

    with col2:
        st.info(
            """
        ### Getting Started
        
        1. Connect your investment accounts
        2. Review your portfolio analysis
        3. Get personalized recommendations
        4. Track performance over time
        """
        )

    # Backend connectivity check
    st.divider()
    if st.button("Check Backend Health"):
        backend_healthy = check_backend_health()
        if backend_healthy:
            st.success("✅ Backend is healthy and responsive!")
        else:
            st.error("❌ Cannot reach backend. Check if services are running.")
            st.code(
                """
            docker-compose up -d
            uvicorn backend.main:app --reload
            """
            )


def show_portfolio_analysis():
    """Display portfolio analysis page."""
    st.title("Portfolio Analysis 📊")

    st.info("Portfolio analysis features coming soon!")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Portfolio Value", "$50,000", "+5.2%")
        st.metric("YTD Return", "8.3%", "+2.1%")

    with col2:
        st.metric("Risk Score", "6/10", "Moderate")
        st.metric("Diversification", "Good", "✓")

    st.write("### Asset Allocation (Coming Soon)")
    st.bar_chart({
        "Stocks": 45,
        "Bonds": 30,
        "Real Estate": 15,
        "Cash": 10,
    })


def show_risk_assessment():
    """Display risk assessment page."""
    st.title("Risk Assessment ⚖️")

    st.info("Risk assessment features coming soon!")

    # Risk profile selection
    risk_profile = st.radio(
        "Your Risk Profile",
        ["Conservative", "Moderate", "Aggressive"],
    )

    st.write(f"### You selected: {risk_profile}")

    # Risk metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Volatility", "12.5%")

    with col2:
        st.metric("Max Drawdown", "-8.2%")

    with col3:
        st.metric("Sharpe Ratio", "1.45")


def show_insights():
    """Display AI insights page."""
    st.title("Smart Insights 💡")

    st.info("AI-powered insights coming soon!")

    # Sample insights
    st.write("### Recommended Actions")
    st.success("✓ Rebalance portfolio - your allocation has drifted 3%")
    st.warning("⚠ Consider reducing concentration in Tech sector")
    st.info("ℹ Review high-dividend stocks for tax efficiency")


def show_about():
    """Display about page."""
    st.title("About AI Financial Advisor")

    st.markdown(
        """
    ## Project Overview

    **AI Financial Advisor** is a production-ready financial advisory platform
    combining FastAPI backend with an interactive Streamlit frontend.

    ### Technology Stack
    - **Backend**: FastAPI with PostgreSQL
    - **Frontend**: Streamlit
    - **Containerization**: Docker & Docker Compose
    - **Testing**: pytest with comprehensive coverage

    ### Key Features
    - RESTful API for financial data
    - Real-time portfolio analysis
    - Risk assessment algorithms
    - AI-powered recommendations

    ### Repository
    [GitHub - SmartBridge](https://github.com/yourorg/smartbridge)

    ### License
    MIT License - See LICENSE file for details

    ### Contact
    For support or questions, please open an issue on GitHub.
    """
    )

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Version**: 1.0.0")

    with col2:
        st.info("**Environment**: " + os.getenv("ENVIRONMENT", "development"))

    with col3:
        st.info("**Backend**: " + BACKEND_URL)


if __name__ == "__main__":
    main()
