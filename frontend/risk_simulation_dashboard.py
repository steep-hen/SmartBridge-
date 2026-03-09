"""Streamlit Dashboard for Monte Carlo Risk Simulation.

Interactive visualization of portfolio risk analysis with Monte Carlo simulations.

Run with: streamlit run frontend/risk_simulation_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.insert(0, '.')

try:
    from backend.finance.risk_simulation import (
        run_monte_carlo_simulation,
        calculate_portfolio_percentiles,
        calculate_drawdown_analysis,
        calculate_probability_of_loss,
        calculate_time_to_goal,
        compare_scenarios,
    )
except ImportError:
    st.error("❌ Error: Could not import risk_simulation module. Please ensure it's properly installed.")
    st.stop()


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Monte Carlo Risk Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(amount):
    """Format amount as Indian currency."""
    if amount >= 1_00_00_000:
        return f"₹{amount/1_00_00_000:.2f}Cr"
    elif amount >= 1_00_000:
        return f"₹{amount/1_00_000:.2f}L"
    else:
        return f"₹{amount:,.0f}"


def create_distribution_chart(final_values, total_invested):
    """Create interactive distribution chart of final portfolio values."""
    
    fig = go.Figure()
    
    # Histogram of outcomes
    fig.add_trace(go.Histogram(
        x=final_values,
        nbinsx=50,
        name='Portfolio Distribution',
        marker_color='rgb(31, 119, 180)',
        opacity=0.7,
        hovertemplate='<b>Portfolio Value Range</b><br>₹%{x:,.0f}<br><b>Frequency:</b> %{y}<extra></extra>'
    ))
    
    # Add percentile lines
    percentiles = {
        5: 'rgb(255, 0, 0)',
        25: 'rgb(255, 127, 14)',
        50: 'rgb(0, 128, 0)',
        75: 'rgb(127, 0, 255)',
        95: 'rgb(0, 255, 255)'
    }
    
    for p, color in percentiles.items():
        value = np.percentile(final_values, p)
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            line_width=2,
            annotation_text=f"P{p}<br>₹{value/1_00_000:.1f}L",
            annotation_position="top right"
        )
    
    # Add initial investment line
    fig.add_vline(
        x=total_invested,
        line_dash="solid",
        line_color="red",
        line_width=3,
        annotation_text=f"Total Invested<br>₹{total_invested/1_00_000:.1f}L",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title="<b>Portfolio Value Distribution (1000 Simulations)</b>",
        xaxis_title="Final Portfolio Value (₹)",
        yaxis_title="Frequency",
        hovermode='x unified',
        height=500,
        showlegend=False,
        template='plotly_white',
        xaxis_tickformat="₹,.0f"
    )
    
    return fig


def create_percentile_chart(final_values):
    """Create percentile range visualization."""
    
    percentiles = range(1, 100, 1)
    values = [np.percentile(final_values, p) for p in percentiles]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(percentiles),
        y=values,
        fill='tozeroy',
        name='Percentile Curve',
        line_color='rgb(31, 119, 180)',
        fillcolor='rgba(31, 119, 180, 0.3)',
        hovertemplate='<b>Percentile:</b> %{x}%<br><b>Value:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    # Highlight key percentiles
    key_percentiles = [5, 10, 25, 50, 75, 90, 95]
    key_values = [np.percentile(final_values, p) for p in key_percentiles]
    
    fig.add_trace(go.Scatter(
        x=key_percentiles,
        y=key_values,
        mode='markers+text',
        name='Key Percentiles',
        marker=dict(size=10, color='red'),
        text=[f"P{p}" for p in key_percentiles],
        textposition="top center",
        hovertemplate='<b>Percentile:</b> %{x}%<br><b>Value:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="<b>Portfolio Value - Percentile Curve</b>",
        xaxis_title="Percentile (%)",
        yaxis_title="Portfolio Value (₹)",
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    return fig


def create_paths_chart(portfolio_paths, num_paths=100):
    """Create portfolio trajectory visualization."""
    
    total_months = portfolio_paths.shape[1]
    months = np.arange(0, total_months)
    
    fig = go.Figure()
    
    # Plot sample paths (every nth path for clarity)
    step = max(1, portfolio_paths.shape[0] // num_paths)
    for i in range(0, portfolio_paths.shape[0], step):
        fig.add_trace(go.Scatter(
            x=months,
            y=portfolio_paths[i, :],
            mode='lines',
            name=f'Simulation {i+1}',
            line=dict(width=0.5, color='lightblue'),
            hoverinfo='skip',
            showlegend=False
        ))
    
    # Add median path (bold)
    median_path = np.median(portfolio_paths, axis=0)
    fig.add_trace(go.Scatter(
        x=months,
        y=median_path,
        mode='lines',
        name='Median Path',
        line=dict(width=3, color='darkblue'),
        hovertemplate='<b>Month:</b> %{x}<br><b>Median Value:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    # Add percentile bands
    p5 = [np.percentile(portfolio_paths[:, m], 5) for m in range(total_months)]
    p95 = [np.percentile(portfolio_paths[:, m], 95) for m in range(total_months)]
    
    fig.add_trace(go.Scatter(
        x=months,
        y=p95,
        fill=None,
        mode='lines',
        line_color='rgba(0,0,0,0)',
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=p5,
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,0,0,0)',
        name='90% Confidence Band (P5-P95)',
        fillcolor='rgba(0,128,255,0.2)',
        hovertemplate='<b>Month:</b> %{x}<br><b>5th Percentile:</b> ₹%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="<b>Portfolio Growth Trajectories</b><br><sub>1000 simulated paths with 90% confidence band</sub>",
        xaxis_title="Months",
        yaxis_title="Portfolio Value (₹)",
        hovermode='x unified',
        height=550,
        template='plotly_white'
    )
    
    return fig


def create_return_distribution_chart(portfolio_paths, total_invested):
    """Create return percentage distribution."""
    
    final_values = portfolio_paths[:, -1]
    returns = (final_values - total_invested) / total_invested * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=returns,
        nbinsx=50,
        name='Return Distribution',
        marker_color='rgb(44, 160, 44)',
        opacity=0.7,
        hovertemplate='<b>Return Range</b><br>%{x:.1f}%<br><b>Count:</b> %{y}<extra></extra>'
    ))
    
    # Add mean line
    mean_return = np.mean(returns)
    fig.add_vline(
        x=mean_return,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"Mean<br>{mean_return:.1f}%"
    )
    
    # Add zero return line
    fig.add_vline(
        x=0,
        line_dash="solid",
        line_color="black",
        line_width=2,
        annotation_text="Break-even"
    )
    
    fig.update_layout(
        title="<b>Return Distribution (%)</b>",
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    return fig


def create_scenario_comparison_chart(scenarios_results):
    """Create scenario comparison bar chart."""
    
    scenario_names = list(scenarios_results.keys())
    
    metrics = {
        'Median Return (%)': [scenarios_results[s]['median_return'] for s in scenario_names],
        'Best Case (₹L)': [scenarios_results[s]['best_case']/1_00_000 for s in scenario_names],
        'Worst Case (₹L)': [scenarios_results[s]['worst_case']/1_00_000 for s in scenario_names],
    }
    
    x = np.arange(len(scenario_names))
    width = 0.25
    
    fig = go.Figure()
    
    colors = ['blue', 'green', 'red']
    for i, (metric_name, values) in enumerate(metrics.items()):
        fig.add_trace(go.Bar(
            name=metric_name,
            x=scenario_names,
            y=values,
            marker_color=colors[i],
            hovertemplate='<b>%{x}</b><br>' + metric_name + ': %{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title="<b>Scenario Comparison</b>",
        xaxis_title="Scenario",
        yaxis_title="Value",
        barmode='group',
        height=500,
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def main():
    """Main dashboard application."""
    
    st.title("📊 Monte Carlo Portfolio Risk Simulator")
    st.markdown("Analyze portfolio risk with 1000+ simulation paths")
    
    # Sidebar inputs
    with st.sidebar:
        st.header("⚙️ Simulation Parameters")
        
        tab1, tab2, tab3 = st.tabs(["Basic", "Advanced", "Multiple Scenarios"])
        
        with tab1:
            st.subheader("Investment Parameters")
            initial_investment = st.number_input(
                "Initial Investment (₹)",
                min_value=0,
                value=100000,
                step=10000,
                help="Lump sum investment to start with"
            )
            
            monthly_sip = st.number_input(
                "Monthly SIP (₹)",
                min_value=0,
                value=5000,
                step=1000,
                help="Monthly Systematic Investment Plan"
            )
            
            st.subheader("Market Assumptions")
            expected_return = st.slider(
                "Expected Annual Return (%)",
                min_value=0.0,
                max_value=30.0,
                value=12.0,
                step=1.0,
                help="Historical equity returns: 10-14%"
            ) / 100
            
            volatility = st.slider(
                "Annual Volatility (%)",
                min_value=0.0,
                max_value=50.0,
                value=15.0,
                step=1.0,
                help="Market volatility (standard deviation)"
            ) / 100
            
            years = st.slider(
                "Investment Period (Years)",
                min_value=1,
                max_value=40,
                value=10,
                step=1
            )
        
        with tab2:
            st.subheader("Advanced Settings")
            num_simulations = st.select_slider(
                "Number of Simulations",
                options=[100, 500, 1000, 2000, 5000],
                value=1000,
                help="More simulations = more accurate but slower"
            )
            
            risk_free_rate = st.slider(
                "Risk-Free Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=5.0,
                step=0.5,
                help="Government bond yield"
            ) / 100
            
            inflation = st.slider(
                "Inflation Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=6.0,
                step=0.5,
                help="Expected inflation rate"
            ) / 100
            
            goal_amount = st.number_input(
                "Financial Goal (₹) [Optional]",
                min_value=0,
                value=0,
                step=100000,
                help="Target portfolio value"
            )
        
        with tab3:
            st.subheader("Scenario Analysis")
            enable_scenarios = st.checkbox(
                "Compare Multiple Scenarios",
                value=False
            )


    # Main content area
    if st.sidebar.button("▶️ Run Simulation", use_container_width=True):
        with st.spinner("🔄 Running 1000+ Monte Carlo simulations..."):
            
            # Run main simulation
            result = run_monte_carlo_simulation(
                initial_investment=initial_investment,
                monthly_sip=monthly_sip,
                expected_return=expected_return,
                volatility=volatility,
                years=years,
                num_simulations=num_simulations,
                risk_free_rate=risk_free_rate,
                inflation=inflation,
                goal_amount=goal_amount if goal_amount > 0 else None
            )
        
        # Display Key Metrics
        st.markdown("---")
        st.header("📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Median Final Value",
                format_currency(result.final_balance),
                f"{result.median_return:+.1f}% return"
            )
        
        with col2:
            st.metric(
                "Best Case (95th %ile)",
                format_currency(result.best_case),
                f"+{(result.best_case - result.total_invested):,.0f}"
            )
        
        with col3:
            st.metric(
                "Worst Case (5th %ile)",
                format_currency(result.worst_case),
                f"{(result.worst_case - result.total_invested):+,.0f}"
            )
        
        with col4:
            st.metric(
                "Success Probability",
                f"{result.success_probability:.1f}%",
                f"Sharpe Ratio: {result.sharpe_ratio:.2f}"
            )
        
        # Additional Statistics
        st.markdown("---")
        st.header("📊 Detailed Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Returns")
            st.write(f"Mean Return: **{result.mean_return:+.1f}%**")
            st.write(f"Std Deviation: **{result.std_return:.1f}%**")
            st.write(f"Min Return: **{result.min_return:+.1f}%**")
            st.write(f"Max Return: **{result.max_return:+.1f}%**")
        
        with col2:
            st.subheader("Risk Metrics")
            st.write(f"Value at Risk (95%): **₹{abs(result.value_at_risk_95):,.0f}**")
            st.write(f"CAGR: **{result.cagr*100:.2f}%**")
            st.write(f"Investment Period: **{years} years**")
            st.write(f"Total Invested: **{format_currency(result.total_invested)}**")
        
        with col3:
            st.subheader("Percentiles")
            st.write(f"P25: **{format_currency(result.percentile_25)}**")
            st.write(f"P50 (Median): **{format_currency(result.final_balance)}**")
            st.write(f"P75: **{format_currency(result.percentile_75)}**")
            st.write(f"P90: **{format_currency(result.percentile_90)}**")
        
        # Charts
        st.markdown("---")
        st.header("📉 Visualizations")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Distribution",
            "Percentile Curve",
            "Growth Paths",
            "Returns",
            "Analysis"
        ])
        
        with tab1:
            st.plotly_chart(
                create_distribution_chart(result.final_values, result.total_invested),
                use_container_width=True
            )
        
        with tab2:
            st.plotly_chart(
                create_percentile_chart(result.final_values),
                use_container_width=True
            )
        
        with tab3:
            st.plotly_chart(
                create_paths_chart(result.portfolio_paths),
                use_container_width=True
            )
        
        with tab4:
            st.plotly_chart(
                create_return_distribution_chart(result.portfolio_paths, result.total_invested),
                use_container_width=True
            )
        
        with tab5:
            # Drawdown analysis
            drawdown_analysis = calculate_drawdown_analysis(result.portfolio_paths)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Drawdown Analysis")
                st.write(f"Average Max Drawdown: **{drawdown_analysis['average_max_drawdown']:.1f}%**")
                st.write(f"Worst Max Drawdown: **{drawdown_analysis['worst_max_drawdown']:.1f}%**")
                st.write(f"Median Max Drawdown: **{drawdown_analysis['median_max_drawdown']:.1f}%**")
            
            with col2:
                st.subheader("Risk Metrics")
                prob_loss = calculate_probability_of_loss(result.final_values, result.total_invested)
                st.write(f"Probability of Loss: **{prob_loss:.1f}%**")
                
                # Time to goal
                if goal_amount > 0:
                    time_analysis = calculate_time_to_goal(
                        result.portfolio_paths,
                        goal_amount,
                        years
                    )
                    st.write(f"Success to Goal: **{time_analysis['success_probability']:.1f}%**")
                    if time_analysis['median_months']:
                        st.write(f"Median Time to Goal: **{time_analysis['median_years']:.1f} years**")
        
        # Export data
        st.markdown("---")
        st.header("📥 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Create results dataframe
            results_df = pd.DataFrame({
                'Metric': [
                    'Median Final Value',
                    'Best Case (95th percentile)',
                    'Worst Case (5th percentile)',
                    'Mean Return (%)',
                    'Median Return (%)',
                    'Sharpe Ratio',
                    'CAGR (%)',
                    'Success Probability (%)',
                    'Value at Risk ₹',
                    'Total Invested ₹',
                    'Investment Period (Years)'
                ],
                'Value': [
                    result.final_balance,
                    result.best_case,
                    result.worst_case,
                    result.mean_return,
                    result.median_return,
                    result.sharpe_ratio,
                    result.cagr * 100,
                    result.success_probability,
                    result.value_at_risk_95,
                    result.total_invested,
                    years
                ]
            })
            
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name="simulation_results.csv",
                mime="text/csv"
            )
        
        with col2:
            # Portfolio paths data
            paths_df = pd.DataFrame(result.portfolio_paths)
            paths_df.columns = [f"Month_{i}" for i in range(paths_df.shape[1])]
            
            csv = paths_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Paths (CSV)",
                data=csv,
                file_name="portfolio_paths.csv",
                mime="text/csv"
            )
    
    else:
        st.info("👈 Configure parameters in the sidebar and click 'Run Simulation' to begin")


if __name__ == "__main__":
    main()
