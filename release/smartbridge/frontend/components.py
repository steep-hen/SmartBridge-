"""Reusable UI components for Streamlit dashboard."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import json


def metric_card(label: str, value: Any, suffix: str = "", format_str: str = None, color: str = None):
    """Display a metric card.
    
    Args:
        label: Label text
        value: Metric value
        suffix: Optional suffix (e.g., "%", "₹")
        format_str: Optional format string (e.g., ",.2f")
        color: Optional color (info, success, warning, error)
    """
    # Format value
    if isinstance(value, (int, float)):
        if format_str:
            formatted_value = f"{value:{format_str}}"
        elif isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
    else:
        formatted_value = str(value)
    
    if suffix:
        formatted_value = f"{formatted_value}{suffix}"
    
    col = st.metric(label=label, value=formatted_value)
    return col


def summary_cards(metrics: Dict[str, Any]):
    """Display a grid of summary metric cards.
    
    Args:
        metrics: Dict of metric_name -> value
    """
    cols = st.columns(4)
    
    card_configs = [
        ("Monthly Income", "monthly_income", "₹", ",.0f"),
        ("Monthly Expenses", "monthly_expenses", "₹", ",.0f"),
        ("Savings Balance", "savings_balance", "₹", ",.0f"),
        ("Total Debt", "total_debt", "₹", ",.0f"),
        ("Savings Rate", "savings_rate", "%", ".1f"),
        ("Debt-to-Income", "debt_to_income", "", ".2%"),
        ("Emergency Fund", "emergency_fund_months", " months", ".1f"),
        ("Health Score", "financial_health_score", "/100", ".0f"),
    ]
    
    for idx, (label, key, suffix, fmt) in enumerate(card_configs):
        col = cols[idx % 4]
        value = metrics.get(key, 0)
        
        with col:
            if isinstance(value, float) and "%" in suffix:
                # Already a ratio, format as percentage
                metric_card(label, value, f"{suffix}", None)
            else:
                metric_card(label, value, suffix, fmt)


def advice_action_card(action: Dict[str, Any]):
    """Display a single advice action card.
    
    Args:
        action: Dict with 'title', 'priority', 'rationale'
    """
    priority = action.get("priority", 0)
    colors = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "🔵"}
    color_icon = colors.get(priority, "⚪")
    
    st.write(f"**{color_icon} {action['title']}** (Priority: {priority}/5)")
    st.caption(action.get("rationale", ""))


def advice_instrument_card(instrument: Dict[str, Any]):
    """Display a single instrument recommendation card.
    
    Args:
        instrument: Dict with 'name', 'type', 'allocation_pct', 'rationale'
    """
    name = instrument.get("name", "Unknown")
    type_label = instrument.get("type", "UNKNOWN")
    allocation = instrument.get("allocation_pct", 0)
    rationale = instrument.get("rationale", "")
    
    st.write(f"**{name}** ({type_label})")
    st.write(f"Allocation: **{allocation:.1f}%**")
    st.caption(rationale)


def chart_income_vs_expenses(monthly_income: float, monthly_expenses: float):
    """Bar chart: Income vs Expenses.
    
    Args:
        monthly_income: Monthly income value
        monthly_expenses: Monthly expenses value
    """
    data = {
        "Category": ["Income", "Expenses"],
        "Amount": [monthly_income, monthly_expenses],
    }
    
    fig = px.bar(
        data,
        x="Category",
        y="Amount",
        title="Monthly Income vs Expenses",
        labels={"Amount": "₹"},
        color="Category",
        color_discrete_map={"Income": "#2E7D32", "Expenses": "#C62828"},
    )
    
    fig.update_layout(
        height=300,
        showlegend=False,
        hovermode="x unified",
    )
    
    st.plotly_chart(fig, use_container_width=True)


def chart_spending_categories(monthly_expenses: float, expense_breakdown: Optional[Dict[str, float]] = None):
    """Pie chart: Spending categories.
    
    Args:
        monthly_expenses: Total monthly expenses
        expense_breakdown: Dict of category -> amount (if not provided, creates dummy)
    """
    # Use provided breakdown or create a reasonable demo breakdown
    if not expense_breakdown or not expense_breakdown.items():
        expense_breakdown = {
            "Housing": monthly_expenses * 0.3,
            "Food": monthly_expenses * 0.2,
            "Transportation": monthly_expenses * 0.15,
            "Utilities": monthly_expenses * 0.15,
            "Entertainment": monthly_expenses * 0.1,
            "Other": monthly_expenses * 0.1,
        }
    
    fig = px.pie(
        names=list(expense_breakdown.keys()),
        values=list(expense_breakdown.values()),
        title="Spending Categories",
    )
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def chart_goal_projection(goal_name: str, goal_target: float, goal_current: float, projection_samples: List[Dict] = None):
    """Line chart: Goal projection over time.
    
    Args:
        goal_name: Name of the goal
        goal_target: Target amount
        goal_current: Current progress
        projection_samples: List of {'month': int, 'projected_balance': float}
    """
    if not projection_samples:
        # Create dummy projection
        projection_samples = [
            {"month": 0, "projected_balance": goal_current},
            {"month": 6, "projected_balance": goal_current + (goal_target - goal_current) * 0.3},
            {"month": 12, "projected_balance": goal_current + (goal_target - goal_current) * 0.6},
            {"month": 24, "projected_balance": goal_target},
        ]
    
    data = {
        "Month": [s.get("month", 0) for s in projection_samples],
        "Projected Balance": [s.get("projected_balance", 0) for s in projection_samples],
    }
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data["Month"],
        y=data["Projected Balance"],
        mode='lines+markers',
        name='Projection',
        line=dict(color='#1976D2', width=3),
        marker=dict(size=6),
    ))
    
    # Add target line
    fig.add_hline(
        y=goal_target,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Target: ₹{goal_target:,.0f}",
    )
    
    fig.update_layout(
        title=f"{goal_name} Projection",
        xaxis_title="Months",
        yaxis_title="₹",
        height=300,
        hovermode="x unified",
    )
    
    st.plotly_chart(fig, use_container_width=True)


def chart_holdings_allocation(holdings: List[Dict[str, Any]]):
    """Donut chart: Holdings allocation.
    
    Args:
        holdings: List of {'ticker', 'allocation_pct', 'current_value', ...}
    """
    if not holdings:
        st.info("No holdings to display")
        return
    
    labels = [h.get("ticker", "Unknown") for h in holdings]
    values = [h.get("allocation_pct", 0) for h in holdings]
    
    fig = px.pie(
        names=labels,
        values=values,
        title="Portfolio Allocation",
        hole=0.4,  # Donut
    )
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def assumptions_section(initial_assumptions: Dict[str, float] = None):
    """Interactive assumptions editor with sliders.
    
    Args:
        initial_assumptions: Dict of assumption_name -> value
        
    Returns:
        dict: Updated assumptions
    """
    if initial_assumptions is None:
        initial_assumptions = {
            "expected_annual_return": 0.06,
            "inflation": 0.03,
            "monthly_expenses_override": None,
        }
    
    st.subheader("📊 Adjust Assumptions")
    
    updated = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        updated["expected_annual_return"] = st.slider(
            "Expected Annual Return (%)",
            min_value=0.0,
            max_value=0.20,
            value=initial_assumptions.get("expected_annual_return", 0.06),
            step=0.01,
            format="%.2f",
            help="Expected return on investments (0-20% p.a.)",
        ) / 100  # Convert to ratio
    
    with col2:
        updated["inflation"] = st.slider(
            "Inflation Rate (%)",
            min_value=0.0,
            max_value=0.10,
            value=initial_assumptions.get("inflation", 0.03),
            step=0.005,
            format="%.2f",
            help="Expected inflation rate (0-10% p.a.)",
        )
    
    return updated


def risk_warning_box(risk_warning: str):
    """Display risk warning in a highlighted box.
    
    Args:
        risk_warning: Warning text
    """
    st.warning(f"⚠️ **Risk Warning**\n\n{risk_warning}")


def disclaimer_box():
    """Display disclaimer box."""
    st.info(
        "**📋 Disclaimer**\n\n"
        "This dashboard provides **educational and demonstration purposes only**. "
        "The financial advice and projections are not personalized recommendations. "
        "We are not registered financial advisors. "
        "Please consult a qualified financial professional before making investment decisions."
    )


def consent_checkbox(key: str = "consent") -> bool:
    """Display consent checkbox for data handling.
    
    Args:
        key: Streamlit state key
        
    Returns:
        bool: Whether user has consented
    """
    consent = st.checkbox(
        "I understand and consent to analyze my financial data with this tool.",
        key=key,
        help="Check this box to proceed with dashboard analysis."
    )
    return consent


def export_button_json(data: Dict[str, Any], filename: str = "financial_plan.json") -> bool:
    """Download button for JSON export.
    
    Args:
        data: Data to export
        filename: Download filename
        
    Returns:
        bool: Whether download was triggered
    """
    json_str = json.dumps(data, indent=2, default=str)
    
    st.download_button(
        label="📥 Download as JSON",
        data=json_str,
        file_name=filename,
        mime="application/json",
        key="json_download",
    )
    return True


def export_button_pdf(html_content: str, filename: str = "financial_plan.pdf") -> bool:
    """Download button for PDF export (requires reportlab).
    
    Args:
        html_content: HTML content to convert to PDF
        filename: Download filename
        
    Returns:
        bool: Whether export was successful
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
        from io import BytesIO
        
        # Create PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(0.5 * inch, 10.5 * inch, "Financial Plan & Advice Report")
        
        # Add timestamp
        from datetime import datetime
        c.setFont("Helvetica", 10)
        c.drawString(0.5 * inch, 10.2 * inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add disclaimer
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5 * inch, 9.8 * inch, "Disclaimer:")
        c.setFont("Helvetica", 9)
        
        y_pos = 9.6 * inch
        disclaimer_text = (
            "This report is for educational purposes only. "
            "Not a registered financial advisor. "
            "Consult a professional before making investment decisions."
        )
        
        # Wrap text
        for line in disclaimer_text.split(". "):
            c.drawString(0.7 * inch, y_pos, line + ".")
            y_pos -= 0.2 * inch
        
        c.save()
        buffer.seek(0)
        
        st.download_button(
            label="📄 Download as PDF",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/pdf",
            key="pdf_download",
        )
        return True
        
    except ImportError:
        st.warning("reportlab not installed. Use JSON export instead.")
        return False


def loading_spinner(text: str = "Loading..."):
    """Context manager for loading spinner.
    
    Usage:
        with loading_spinner("Fetching data"):
            # Do work
    """
    return st.spinner(text)
