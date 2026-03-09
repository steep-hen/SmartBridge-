"""Streamlit Dashboard for Financial Forecasting.

Displays:
- Expense forecast charts
- Savings projections
- Scenario analysis
- Financial health indicators

Run with: streamlit run forecast_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
import requests
import json

# Page configuration
st.set_page_config(
    page_title="💰 Financial Forecast Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .header-title {
        color: #667eea;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SAMPLE DATA GENERATION
# ============================================================================

def generate_sample_transactions(days: int = 180) -> tuple:
    """Generate sample transaction data for demo."""
    
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    expenses = []
    income = []
    
    for current_date in dates:
        # Income (monthly, on the 1st)
        if current_date.day == 1:
            income.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'amount': 50000,
                'type': 'salary',
                'category': 'salary'
            })
        
        # Daily expenses
        if np.random.random() > 0.6:  # 40% of days have expenses
            amount = np.random.normal(1000, 500)
            amount = max(100, min(5000, amount))  # Clamp between 100-5000
            
            category = np.random.choice(
                ['groceries', 'transport', 'entertainment', 'utilities', 'food'],
                p=[0.3, 0.2, 0.2, 0.15, 0.15]
            )
            
            expenses.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'amount': round(amount, 2),
                'type': 'expense',
                'category': category
            })
    
    return expenses, income


def create_expense_chart(forecast_data: Dict[str, Any]) -> go.Figure:
    """Create expense forecast visualization."""
    
    expenses = forecast_data['predicted_expenses_next_6_months']
    
    df = pd.DataFrame([
        {
            'date': e['date'],
            'predicted': e['predicted'],
            'lower': e['lower_bound'],
            'upper': e['upper_bound']
        }
        for e in expenses
    ])
    
    df['date'] = pd.to_datetime(df['date'])
    
    fig = go.Figure()
    
    # Add confidence interval
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['upper'],
        fill=None,
        mode='lines',
        line_color='rgba(0,0,0,0)',
        showlegend=False,
        name='Upper Bound'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['lower'],
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,0,0,0)',
        name='95% Confidence Interval',
        fillcolor='rgba(102, 126, 234, 0.2)'
    ))
    
    # Add predicted line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['predicted'],
        mode='lines+markers',
        name='Predicted Expenses',
        line=dict(color='rgb(102, 126, 234)', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='📊 Expense Forecast (Next 6 Months)',
        xaxis_title='Date',
        yaxis_title='Amount (₹)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        font=dict(size=12),
    )
    
    fig.yaxis.tickformat = '₹,.0f'
    
    return fig


def create_savings_projection_chart(forecast_data: Dict[str, Any]) -> go.Figure:
    """Create savings projection visualization."""
    
    savings = forecast_data['savings_projection']['monthly_savings']
    
    df = pd.DataFrame([
        {
            'month': s['month'],
            'income': s['income'],
            'expenses': s['expenses'],
            'savings': s['savings'],
            'cumulative': s['cumulative_balance']
        }
        for s in savings
    ])
    
    df['month'] = pd.to_datetime(df['month'])
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Income bar
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['income'],
        name='Income',
        marker_color='rgb(76, 175, 80)',
    ))
    
    # Expenses bar
    fig.add_trace(go.Bar(
        x=df['month'],
        y=df['expenses'],
        name='Expenses',
        marker_color='rgb(244, 67, 54)',
    ))
    
    # Savings line
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=df['savings'],
        name='Monthly Savings',
        mode='lines+markers',
        line=dict(color='rgb(33, 150, 243)', width=3),
        marker=dict(size=10),
        yaxis='y2'
    ))
    
    # Update layout
    fig.update_layout(
        title='💳 Income vs Expenses & Monthly Savings',
        xaxis_title='Month',
        yaxis_title='Amount (₹)',
        yaxis2=dict(
            title='Savings (₹)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        barmode='group',
        template='plotly_white',
        height=400,
        font=dict(size=12),
    )
    
    return fig


def create_cumulative_savings_chart(forecast_data: Dict[str, Any]) -> go.Figure:
    """Create cumulative savings chart."""
    
    savings = forecast_data['savings_projection']['monthly_savings']
    
    df = pd.DataFrame([
        {
            'month': s['month'],
            'cumulative': s['cumulative_balance']
        }
        for s in savings
    ])
    
    df['month'] = pd.to_datetime(df['month'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=df['cumulative'],
        mode='lines+markers',
        name='Cumulative Balance',
        line=dict(color='rgb(102, 126, 234)', width=4),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)'
    ))
    
    fig.update_layout(
        title='📈 Projected Cumulative Balance',
        xaxis_title='Month',
        yaxis_title='Balance (₹)',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        font=dict(size=12),
    )
    
    return fig


def create_scenario_chart(scenario_data: Dict[str, Any]) -> go.Figure:
    """Create scenario analysis visualization."""
    
    scenarios = scenario_data['scenarios']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=list(scenarios.keys()),
        y=list(scenarios.values()),
        marker_color=['rgb(33, 150, 243)', 'rgb(244, 67, 54)', 'rgb(76, 175, 80)'],
        text=[f"₹{v:,.0f}" for v in scenarios.values()],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='🎯 Monthly Savings Scenarios',
        xaxis_title='Scenario',
        yaxis_title='Projected Savings (₹)',
        template='plotly_white',
        height=300,
        font=dict(size=12),
    )
    
    return fig


def create_category_breakdown(transactions: List[Dict]) -> go.Figure:
    """Create expense category breakdown."""
    
    expense_df = pd.DataFrame([
        t for t in transactions if t['type'] == 'expense'
    ])
    
    if expense_df.empty:
        return None
    
    category_totals = expense_df.groupby('category')['amount'].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=category_totals.index,
        values=category_totals.values,
        hole=0.3,
        marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
    )])
    
    fig.update_layout(
        title='🏷️ Expense Categories (Last 6 Months)',
        height=350,
        font=dict(size=12),
    )
    
    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    """Main dashboard function."""
    
    # Header
    st.markdown('<p class="header-title">💰 Financial Forecast Dashboard</p>', unsafe_allow_html=True)
    st.markdown("Predict your financial future with AI-powered forecasting")
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        mode = st.radio("Select Mode", ["Demo", "Upload Data"])
        
        if mode == "Demo":
            st.info("Using sample transaction data for demonstration")
            
            # Demo parameters
            model_type = st.selectbox(
                "Forecast Model",
                ["Prophet", "ARIMA"],
                help="Prophet works better with seasonal data"
            )
            
            forecast_months = st.slider(
                "Forecast Period (Months)",
                1, 12, 6
            )
            
            starting_balance = st.number_input(
                "Starting Balance (₹)",
                value=10000,
                step=1000
            )
            
            aggregation = st.selectbox(
                "Data Aggregation",
                ["Daily", "Weekly", "Monthly"]
            )
            
        else:
            st.warning("Upload data feature coming soon")
            return
    
    # Generate forecast
    if st.sidebar.button("🚀 Generate Forecast", use_container_width=True):
        with st.spinner("Generating forecast..."):
            try:
                # Generate sample data
                expenses, income = generate_sample_transactions()
                
                # Mock forecast result
                forecast_result = {
                    'predicted_expenses_next_6_months': [
                        {
                            'date': (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m'),
                            'predicted': np.random.normal(30000, 5000),
                            'lower_bound': np.random.normal(28000, 5000),
                            'upper_bound': np.random.normal(32000, 5000),
                        }
                        for i in range(forecast_months)
                    ],
                    'savings_projection': {
                        'monthly_savings': [
                            {
                                'month': (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m'),
                                'income': 50000,
                                'expenses': np.random.normal(30000, 5000),
                                'savings': 50000 - np.random.normal(30000, 5000),
                                'cumulative_balance': starting_balance + (50000 - np.random.normal(30000, 5000)) * (i+1),
                            }
                            for i in range(forecast_months)
                        ],
                        'average_monthly_savings': 20000,
                        'projected_balance': starting_balance + (20000 * forecast_months),
                        'savings_trend': 'improving'
                    },
                    'summary': {
                        'forecast_period': f'{forecast_months} months',
                        'total_predicted_expenses': 180000,
                        'average_monthly_expenses': 30000,
                        'model_used': model_type,
                    }
                }
                
                st.session_state.forecast = forecast_result
                st.success("✅ Forecast generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating forecast: {str(e)}")
                return
    
    # Display results
    if 'forecast' in st.session_state:
        forecast = st.session_state.forecast
        
        # Key Metrics
        st.subheader("📊 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Predicted Expenses",
                f"₹{forecast['summary']['total_predicted_expenses']:,.0f}"
            )
        
        with col2:
            st.metric(
                "Avg Monthly Expenses",
                f"₹{forecast['summary']['average_monthly_expenses']:,.0f}"
            )
        
        with col3:
            st.metric(
                "Avg Monthly Savings",
                f"₹{forecast['savings_projection']['average_monthly_savings']:,.0f}",
                delta="good"
            )
        
        with col4:
            health_map = {
                'improving': '↗️ Improving',
                'declining': '↘️ Declining',
                'stable': '→ Stable'
            }
            trend = forecast['savings_projection']['savings_trend']
            st.metric(
                "Savings Trend",
                health_map.get(trend, trend)
            )
        
        st.divider()
        
        # Charts
        st.subheader("📈 Forecasts & Projections")
        
        col1, col2 = st.columns(2)
        
        with col1:
            expense_chart = create_expense_chart(forecast)
            st.plotly_chart(expense_chart, use_container_width=True)
        
        with col2:
            savings_chart = create_savings_projection_chart(forecast)
            st.plotly_chart(savings_chart, use_container_width=True)
        
        # Cumulative savings
        cumulative_chart = create_cumulative_savings_chart(forecast)
        st.plotly_chart(cumulative_chart, use_container_width=True)
        
        st.divider()
        
        # Scenario Analysis
        st.subheader("🎯 Scenario Analysis")
        
        scenario_data = {
            'scenarios': {
                'baseline': forecast['savings_projection']['average_monthly_savings'],
                'high_expenses_scenario': forecast['savings_projection']['average_monthly_savings'] * 0.7,
                'optimistic_scenario': forecast['savings_projection']['average_monthly_savings'] * 1.3,
            }
        }
        
        scenario_chart = create_scenario_chart(scenario_data)
        st.plotly_chart(scenario_chart, use_container_width=True)
        
        st.divider()
        
        # Detailed Breakdown
        st.subheader("💾 Monthly Breakdown")
        
        savings_data = forecast['savings_projection']['monthly_savings']
        breakdown_df = pd.DataFrame(savings_data)
        breakdown_df['month'] = pd.to_datetime(breakdown_df['month']).dt.strftime('%B %Y')
        
        # Format as currency
        for col in ['income', 'expenses', 'savings', 'cumulative_balance']:
            breakdown_df[col] = breakdown_df[col].apply(lambda x: f"₹{x:,.0f}")
        
        st.dataframe(
            breakdown_df,
            column_config={
                'month': 'Month',
                'income': 'Income',
                'expenses': 'Expenses',
                'savings': 'Savings',
                'cumulative_balance': 'Cumulative Balance'
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        
        # Recommendations
        st.subheader("💡 Recommendations")
        
        avg_savings = forecast['savings_projection']['average_monthly_savings']
        avg_expenses = forecast['summary']['average_monthly_expenses']
        
        recommendations = []
        
        if avg_savings < 10000:
            recommendations.append("📌 Your savings are below ₹10,000/month. Consider reducing expenses or increasing income.")
        elif avg_savings > 30000:
            recommendations.append("✅ Excellent savings rate! Consider investing the surplus amount.")
        
        if forecast['savings_projection']['savings_trend'] == 'declining':
            recommendations.append("⚠️ Your savings trend is declining. Monitor your spending patterns.")
        else:
            recommendations.append("🎉 Your savings trend is positive!")
        
        if avg_expenses > 40000:
            recommendations.append("🔍 Consider categorizing and analyzing your expenses to identify areas for reduction.")
        
        for rec in recommendations:
            st.info(rec)
        
        # Data export
        st.divider()
        st.subheader("📥 Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = breakdown_df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name="forecast_data.csv",
                mime="text/csv"
            )
        
        with col2:
            json_data = json.dumps(forecast, indent=2, default=str)
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name="forecast_data.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()
