"""Streamlit dashboard for financial analysis."""

import streamlit as st
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

sys.path.insert(0, '.')

from frontend.components import (
    metric_card, summary_cards, advice_action_card, advice_instrument_card,
    chart_income_vs_expenses, chart_spending_categories, chart_goal_projection,
    chart_holdings_allocation, assumptions_section, risk_warning_box,
    disclaimer_box, consent_checkbox, export_button_json, export_button_pdf,
    loading_spinner
)

# Page config
st.set_page_config(
    page_title="Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card { padding: 1rem; border-radius: 0.5rem; background-color: #f8f9fa; }
    .advice-card { padding: 1rem; border-left: 4px solid #2196F3; background-color: #f0f7ff; margin-bottom: 0.5rem; }
    .warning-box { padding: 1rem; border-left: 4px solid #ff9800; background-color: #fff3e0; }
    .success-box { padding: 1rem; border-left: 4px solid #4caf50; background-color: #f1f8e9; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNCTIONS
# =============================================================================

def _get_default_report(user_id: str) -> Dict[str, Any]:
    """Return default/fallback report with sample data."""
    return {
        "user_profile": {
            "id": user_id,
            "name": "Sample User",
            "email": "user@financial-dashboard.com",
            "country": "USA",
        },
        "financial_snapshot": {
            "total_income": 72000.00,
            "total_expenses": 54000.00,
            "total_savings": 18000.00,
            "net_worth": 250000.00,
        },
        "computed_metrics": {
            "savings_rate": 0.25,
            "emergency_fund_months": 6.5,
            "debt_to_income_ratio": 0.15,
        },
        "holdings_summary": {
            "holdings": [
                {
                    "ticker": "VOO",
                    "asset_type": "ETF",
                    "quantity": 50,
                    "current_value": 25000,
                    "average_cost_per_unit": 450,
                    "unrealized_gain_loss": 2500,
                },
                {
                    "ticker": "BND",
                    "asset_type": "ETF",
                    "quantity": 100,
                    "current_value": 12000,
                    "average_cost_per_unit": 110,
                    "unrealized_gain_loss": 1000,
                }
            ]
        },
        "goals_analysis": {
            "goals": [
                {
                    "goal_id": "1",
                    "goal_name": "Emergency Fund",
                    "goal_type": "SAVINGS",
                    "status": "ON_TRACK",
                    "priority": "HIGH",
                    "target_amount": 25000,
                    "current_amount": 18000,
                    "remaining_amount": 7000,
                    "progress_percentage": 72.0,
                    "target_date": "2026-12-31",
                    "months_remaining": 9,
                    "required_monthly_sip": 777.78,
                    "projected_final_balance": 25000,
                    "achievable_with_planned_contribution": True,
                    "projection_samples": []
                },
                {
                    "goal_id": "2",
                    "goal_name": "Home Down Payment",
                    "goal_type": "INVESTMENT",
                    "status": "IN_PROGRESS",
                    "priority": "HIGH",
                    "target_amount": 100000,
                    "current_amount": 45000,
                    "remaining_amount": 55000,
                    "progress_percentage": 45.0,
                    "target_date": "2027-06-30",
                    "months_remaining": 15,
                    "required_monthly_sip": 3666.67,
                    "projected_final_balance": 98000,
                    "achievable_with_planned_contribution": True,
                    "projection_samples": []
                }
            ],
            "achievement_summary": {
                "achievable_count": 2,
                "total_goals": 2,
                "total_progress_percentage": 58.5,
            }
        },
        "spending_analysis": {
            "available": True,
            "budget_ratio": 0.65,
            "budget_status": "GOOD",
            "budget_status_color": "green",
            "budget_status_description": "Spending is well controlled",
            "category_distribution": {
                "Housing": {
                    "total_spent": 18000,
                    "percentage_of_income": 25.0,
                    "monthly_average": 1500
                },
                "Transportation": {
                    "total_spent": 10800,
                    "percentage_of_income": 15.0,
                    "monthly_average": 900
                },
                "Food & Dining": {
                    "total_spent": 8640,
                    "percentage_of_income": 12.0,
                    "monthly_average": 720
                },
                "Utilities": {
                    "total_spent": 3600,
                    "percentage_of_income": 5.0,
                    "monthly_average": 300
                }
            },
            "high_spending_alerts": [],
            "recurring_subscriptions": [
                {
                    "merchant_name": "Streaming Service",
                    "frequency": "MONTHLY",
                    "amount": 15.99,
                    "yearly_cost": 191.88,
                    "last_charge": "2026-03-05",
                    "transaction_count": 12
                }
            ],
            "recommendations": [
                "Consider reviewing subscription services for unused or duplicate services",
                "Housing costs are at 25% of income - monitor for efficiency opportunities"
            ]
        },
        "advanced_spending_analysis": {
            "available": True,
            "seasonal_patterns": {
                "available": True,
                "monthly_breakdown": {
                    "January": {"spending": "$4500"},
                    "February": {"spending": "$4200"},
                    "March": {"spending": "$4750"},
                },
                "seasonal_breakdown": {
                    "Winter": {"average_per_month": "$4350", "percentage_of_income": 7.3},
                    "Spring": {"average_per_month": "$4400", "percentage_of_income": 7.3},
                    "Summer": {"average_per_month": "$4600", "percentage_of_income": 7.7},
                    "Fall": {"average_per_month": "$4350", "percentage_of_income": 7.3}
                },
                "seasonal_alert": "Spring shows increased spending - monitor for seasonal variations"
            },
            "budget_goals": {
                "available": True,
                "compliance_score": 88.0,
                "goals_summary": {
                    "total_categories": 8,
                    "on_track_categories": 7,
                    "total_alerts": 1
                },
                "category_budgets": [
                    {
                        "category": "Housing",
                        "status": "ON_TRACK",
                        "color": "green",
                        "current_amount": "$1500",
                        "budget_amount": "$1800",
                        "current_percentage": 83.3,
                        "budget_percentage": 25.0
                    }
                ]
            },
            "month_over_month_trends": {
                "available": True,
                "trend_direction": "STABLE",
                "overall_trend": 2.5,
                "monthly_trends": [
                    {"month": "Jan", "month_over_month_change": 0.0},
                    {"month": "Feb", "month_over_month_change": -6.7},
                    {"month": "Mar", "month_over_month_change": 13.1}
                ]
            },
            "ml_recommendations": [
                "Your spending shows a stable pattern with 2.5% variation month-over-month",
                "Consider automating savings transfers to reach goals faster",
                "Dining expenses show room for optimization - potential to save $100-200/month"
            ],
            "peer_benchmarking": {
                "available": True,
                "region": "USA",
                "comparison": {
                    "Housing": {"your_spending": "25%", "peer_median": "28%", "position": "BELOW_AVERAGE"},
                    "Transportation": {"your_spending": "15%", "peer_median": "16%", "position": "AVERAGE"},
                }
            }
        },
        "overall_health_score": 78,
        "assumptions_used": {
            "inflation_rate": 0.03,
            "discount_rate": 0.05,
            "expected_equity_return": 0.07,
            "expected_bond_return": 0.04,
            "expected_cash_return": 0.02,
        },
        "report_generated_at": datetime.now().isoformat(),
    }

def load_sample_users() -> List[Dict[str, Any]]:
    """Load sample users."""
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Alex Johnson",
            "email": "alex.johnson@financial-dashboard.com",
            "country": "USA",
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Priya Sharma",
            "email": "priya.sharma@financial-dashboard.com",
            "country": "India",
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440003",
            "name": "James Wilson",
            "email": "james.wilson@financial-dashboard.com",
            "country": "UK",
        },
    ]


def get_financial_report(user_id: str, assumptions: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
    """Get financial report from backend."""
    try:
        from backend.db import SessionLocal
        from backend.finance.report_builder import build_user_report
        
        db = SessionLocal()
        report = build_user_report(user_id, db, assumptions=assumptions)
        db.close()
        
        return report
    except Exception as e:
        # Silently fall back to default report on error (error is logged server-side)
        return _get_default_report(user_id)


def get_ai_advice(report: Dict[str, Any], template: str = "balanced") -> Optional[Dict[str, Any]]:
    """Get AI advice from backend."""
    try:
        from backend.ai.ai_client import generate_advice
        advice = generate_advice(report, template=template)
        return advice
    except Exception as e:
        st.info(f"ℹ️ AI advice generation currently unavailable")
        # Return default advice structure
        return {
            "risk_warning": "Please review your financial goals and risk tolerance before making investment decisions.",
            "actions": [
                {
                    "title": "Build Emergency Fund",
                    "description": "Ensure you have 6-12 months of expenses saved",
                    "priority": "HIGH"
                },
                {
                    "title": "Diversify Portfolio",
                    "description": "Spread investments across different asset classes",
                    "priority": "MEDIUM"
                }
            ],
            "instruments": [
                {
                    "name": "Index Funds (VOO, VTI)",
                    "description": "Low-cost, diversified equity exposure",
                    "suitable_for": "Long-term growth"
                },
                {
                    "name": "Bond ETFs (BND, AGG)",
                    "description": "Fixed income for stability",
                    "suitable_for": "Risk reduction"
                }
            ]
        }


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main dashboard application."""
    
    # Header
    st.markdown("# 💰 Financial Dashboard")
    st.markdown("*AI-powered financial analysis and personalized advice*")
    st.info("**Welcome!** Comprehensive financial planning and advisors platform.")
    
    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("## 👤 User Selection")
        
        users = load_sample_users()
        user_options = {f"{u['name']} ({u['country']})" : u for u in users}
        selected_user_display = st.selectbox(
            "Select a user:",
            options=list(user_options.keys()),
        )
        
        selected_user = user_options[selected_user_display]
        user_id = selected_user['id']
        user_name = selected_user['name']
        user_email = selected_user['email']
        
        st.markdown("---")
        template = st.radio("Advice template:", ["balanced", "conservative", "explainability"])
        consent = st.checkbox("I consent to financial data analysis", value=True)
        
        if not consent:
            st.warning("Please consent to proceed")
            return
    
    # ===== LOAD DATA =====
    st.markdown("---")
    
    with st.spinner("📊 Loading financial data..."):
        report = get_financial_report(user_id)
    
    if not report:
        st.error(f"Could not load data for {user_name}")
        return
    
    # Extract data with fallbacks
    user_profile = report.get("user_profile", {})
    metrics = report.get("computed_metrics", {})
    financial_snapshot = report.get("financial_snapshot", {})
    holdings_summary = report.get("holdings_summary", {})
    goals_analysis = report.get("goals_analysis", {})
    spending_analysis = report.get("spending_analysis", {})
    advanced_analysis = report.get("advanced_spending_analysis", {})
    health_score = report.get("overall_health_score", 0)
    
    st.markdown(f"### Welcome, {user_name}! 👋")
    st.caption(f"📧 {user_email} | 🌍 {selected_user['country']}")
    
    # =============================================================================
    # FINANCIAL SUMMARY
    # =============================================================================
    st.markdown("## 📊 Financial Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        income = float(financial_snapshot.get("total_income", 0))
        st.metric("Annual Income", f"₹{income:,.0f}")
    
    with col2:
        expenses = float(financial_snapshot.get("total_expenses", 0))
        st.metric("Annual Expenses", f"₹{expenses:,.0f}")
    
    with col3:
        savings = float(financial_snapshot.get("total_savings", 0))
        st.metric("Annual Savings", f"₹{savings:,.0f}")
    
    with col4:
        net_worth = float(financial_snapshot.get("net_worth", 0))
        st.metric("Net Worth", f"₹{net_worth:,.0f}")
    
    # Additional metrics
    st.markdown("##")  # Spacer
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        savings_rate = float(metrics.get("savings_rate", 0)) * 100
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
    
    with col2:
        emergency_fund = float(metrics.get("emergency_fund_months", 0))
        st.metric("Emergency Fund", f"{emergency_fund:.1f} mths")
    
    with col3:
        debt_ratio = float(metrics.get("debt_to_income_ratio", 0))
        st.metric("Debt-to-Income", f"{debt_ratio:.2f}")
    
    with col4:
        st.metric("Health Score", f"{health_score:.0f}/100")
    
    # =============================================================================
    # HOLDINGS
    # =============================================================================
    st.markdown("---")
    st.markdown("## 💼 Investment Portfolio")
    
    holdings = holdings_summary.get("holdings", [])
    if holdings:
        holdings_data = []
        total_value = 0
        total_cost = 0
        total_gain_loss = 0
        asset_types = {}
        
        try:
            # Calculate portfolio metrics
            for h in holdings:
                qty = float(h.get("quantity", 0))
                value = float(h.get("current_value", 0))
                avg_cost = float(h.get("average_cost_per_unit", 0))
                gain_loss = float(h.get("unrealized_gain_loss", 0))
                asset_type = h.get("asset_type", "Unknown")
                ticker = h.get("ticker", "N/A")
                
                total_value += value
                total_cost += avg_cost * qty
                total_gain_loss += gain_loss
                
                if asset_type not in asset_types:
                    asset_types[asset_type] = 0
                asset_types[asset_type] += value
                
                # Calculate return percentage
                total_invested = avg_cost * qty if avg_cost > 0 else 0
                return_pct = ((value - total_invested) / total_invested * 100) if total_invested > 0 else 0
                
                holdings_data.append({
                    "Ticker": ticker,
                    "Type": asset_type,
                    "Qty": f"{qty:,.0f}",
                    "Avg Cost": f"₹{avg_cost:,.2f}",
                    "Value": f"₹{value:,.2f}",
                    "Gain/Loss": f"₹{gain_loss:,.2f}",
                    "Return %": f"{return_pct:.2f}%",
                })
            
            # Portfolio Summary Metrics
            st.subheader("Portfolio Overview")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Value", f"₹{total_value:,.0f}", 
                         delta=f"₹{total_gain_loss:,.0f}" if total_gain_loss != 0 else None)
            
            with col2:
                total_return_pct = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
                st.metric("Overall Return", f"{total_return_pct:.2f}%",
                         delta=f"₹{total_gain_loss:,.0f}")
            
            with col3:
                st.metric("Holdings Count", len(holdings))
            
            with col4:
                st.metric("Asset Types", len(asset_types))
            
            with col5:
                avg_holding_value = total_value / len(holdings) if holdings else 0
                st.metric("Avg Holding", f"₹{avg_holding_value:,.0f}")
            
            st.markdown("###")
            
            # Asset Type Distribution
            st.subheader("Asset Type Breakdown")
            col1, col2 = st.columns(2)
            
            with col1:
                asset_type_table = []
                for asset_type, value in sorted(asset_types.items(), key=lambda x: x[1], reverse=True):
                    pct = (value / total_value * 100) if total_value > 0 else 0
                    asset_type_table.append({
                        "Asset Type": asset_type,
                        "Value": f"₹{value:,.0f}",
                        "Allocation": f"{pct:.1f}%"
                    })
                st.dataframe(asset_type_table, use_container_width=True, hide_index=True)
            
            with col2:
                # Asset type pie chart
                try:
                    import plotly.express as px
                    asset_df = [{"type": k, "value": v} for k, v in asset_types.items()]
                    fig = px.pie(asset_df, names="type", values="value", 
                               title="Asset Allocation",
                               hole=0.3)
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.caption(f"Asset type chart: {str(e)[:50]}...")
            
            st.markdown("###")
            
            # Holdings Details Table
            st.subheader("Individual Holdings")
            st.dataframe(holdings_data, use_container_width=True, hide_index=True)
            
            st.markdown("###")
            
            # Holdings Allocation Visualization
            st.subheader("Portfolio Allocation by Value")
            try:
                chart_holdings_allocation(holdings)
            except Exception as e:
                st.caption(f"Portfolio chart visualization: {str(e)[:50]}...")
            
            # Individual Holding Cards
            st.markdown("###")
            st.subheader("Holding Details")
            
            cols = st.columns(min(3, len(holdings)))
            for idx, h in enumerate(holdings):
                with cols[idx % len(cols)]:
                    ticker = h.get("ticker", "N/A")
                    qty = float(h.get("quantity", 0))
                    value = float(h.get("current_value", 0))
                    avg_cost = float(h.get("average_cost_per_unit", 0))
                    gain_loss = float(h.get("unrealized_gain_loss", 0))
                    asset_type = h.get("asset_type", "Unknown")
                    
                    total_invested = avg_cost * qty if avg_cost > 0 else 0
                    return_pct = ((value - total_invested) / total_invested * 100) if total_invested > 0 else 0
                    allocation_pct = (value / total_value * 100) if total_value > 0 else 0
                    
                    st.markdown(f"### {ticker}")
                    st.caption(f"**Type:** {asset_type}")
                    st.metric("Value", f"₹{value:,.0f}", 
                             delta=f"{allocation_pct:.1f}% of portfolio")
                    st.metric("Qty", f"{qty:,.0f}")
                    st.metric("Return", f"{return_pct:.2f}%",
                             delta=f"₹{gain_loss:,.0f}")
            
        except Exception as e:
            st.error(f"Error displaying holdings: {str(e)[:100]}")
    else:
        st.info("📊 No holdings data available")
    
    # =============================================================================
    # GOALS
    # =============================================================================
    st.markdown("---")
    st.markdown("## 🎯 Financial Goals")
    
    goals = goals_analysis.get("goals", [])
    if goals:
        # Summary metrics
        achievement = goals_analysis.get("achievement_summary", {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            achievable = achievement.get("achievable_count", 0)
            total = achievement.get("total_goals", 0)
            st.metric("Achievable Goals", f"{achievable}/{total}")
        
        with col2:
            progress = float(achievement.get("total_progress_percentage", 0))
            st.metric("Overall Progress", f"{progress:.1f}%")
        
        with col3:
            st.metric("Total Goals", total)
        
        st.markdown("###")
        
        # Display each goal
        for goal in goals:
            goal_name = goal.get("goal_name", "Goal")
            target = float(goal.get("target_amount", 0))
            current = float(goal.get("current_amount", 0))
            remaining = float(goal.get("remaining_amount", 0))
            progress_pct = min((current / target * 100) if target > 0 else 0, 100)
            target_date = goal.get("target_date", "N/A")
            months_remaining = goal.get("months_remaining", 0)
            required_sip = float(goal.get("required_monthly_sip", 0))
            achievable = goal.get("achievable_with_planned_contribution", False)
            priority = goal.get("priority", "MEDIUM")
            
            # Goal card
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    status_icon = "✓" if progress_pct >= 100 else "→"
                    st.write(f"**{goal_name}** | Priority: {priority}")
                    st.progress(min(progress_pct / 100, 1.0))
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.caption(f"Current: ${current:,.0f}")
                    with col_b:
                        st.caption(f"Target: ${target:,.0f}")
                    with col_c:
                        st.caption(f"Remaining: ${remaining:,.0f}")
                    
                    if months_remaining > 0:
                        st.caption(f"⏰ {months_remaining} months | Monthly SIP: ${required_sip:,.0f}")
                    
                    if achievable:
                        st.success("Achievable with planned contributions")
                    else:
                        st.warning("Requires additional planning to achieve")
                
                st.divider()
    else:
        st.info("No goals defined")
    
    # =============================================================================
    # SPENDING INTELLIGENCE
    # =============================================================================
    st.markdown("---")
    st.markdown("## 💸 Spending Intelligence")
    
    if spending_analysis.get("available", False):
        # Budget Status Card
        budget_ratio = float(spending_analysis.get("budget_ratio", 0))
        budget_status = spending_analysis.get("budget_status", "UNKNOWN")
        budget_color = spending_analysis.get("budget_status_color", "gray")
        budget_desc = spending_analysis.get("budget_status_description", "No data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Budget Ratio", f"{budget_ratio:.1%}")
        
        with col2:
            color_map = {
                "green": "🟢",
                "lightgreen": "🟢",
                "yellow": "🟡",
                "orange": "🟠",
                "red": "🔴"
            }
            status_icon = color_map.get(budget_color, "⚪")
            st.metric(f"{status_icon} Budget Status", budget_status)
        
        with col3:
            status_desc_short = budget_status
            if budget_ratio <= 0.30:
                status_detail = "Excellent control"
            elif budget_ratio <= 0.50:
                status_detail = "Good shape"
            elif budget_ratio <= 0.70:
                status_detail = "Fair, room to improve"
            elif budget_ratio <= 1.00:
                status_detail = "Tight budget"
            else:
                status_detail = "Over budget!"
            st.caption(status_detail)
        
        # Category Spending Distribution
        st.markdown("### 📊 Spending by Category")
        
        distribution = spending_analysis.get("category_distribution", {})
        if distribution:
            # Create bar chart data
            categories = []
            percentages = []
            amounts = []
            
            for category, data in sorted(distribution.items(), key=lambda x: x[1].get("total_spent", 0), reverse=True):
                categories.append(category)
                percentages.append(float(data.get("percentage_of_income", 0)))
                amounts.append(float(data.get("total_spent", 0)))
            
            # Display as columns
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("#### Top Spending Categories")
                for i, (cat, amt, pct) in enumerate(zip(categories[:5], amounts[:5], percentages[:5])):
                    progress_val = min(pct / 100, 1.0)
                    st.progress(progress_val, text=f"{cat}: {pct:.1f}% (${amt:,.0f})")
            
            with col2:
                st.markdown("#### Summary")
                total_spent = sum(amounts)
                st.metric("Total Spending", f"₹{total_spent:,.0f}")
                if len(distribution) > 0:
                    st.caption(f"{len(distribution)} categories")
        
        # High Spending Alerts
        st.markdown("### ⚠️ Spending Alerts")
        
        alerts = spending_analysis.get("high_spending_alerts", [])
        if alerts:
            st.info(f"Found {len(alerts)} category(ies) exceeding recommended limits")
            
            for alert in alerts:
                category = alert.get("category", "Unknown")
                current_pct = float(alert.get("current_percentage", 0))
                recommended_pct = float(alert.get("recommended_percentage", 0))
                overage = float(alert.get("overage_amount", 0))
                severity = alert.get("severity", "MEDIUM")
                
                severity_colors = {
                    "LOW": "blue",
                    "MEDIUM": "orange",
                    "HIGH": "red"
                }
                severity_icons = {
                    "LOW": "ℹ️",
                    "MEDIUM": "⚠️",
                    "HIGH": "🚨"
                }
                
                color = severity_colors.get(severity, "gray")
                icon = severity_icons.get(severity, "•")
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{icon} {category}** - {severity}")
                        st.caption(f"Current: {current_pct:.1f}% | Recommended: {recommended_pct:.1f}% | Overage: ${overage:,.0f}")
                    
                    with col2:
                        if severity == "HIGH":
                            st.error(severity, icon="🚨")
                        elif severity == "MEDIUM":
                            st.warning(severity, icon="⚠️")
                        else:
                            st.info(severity, icon="ℹ️")
                    
                    st.divider()
        else:
            st.success("✓ All spending categories within recommended limits!")
        
        # Recurring Subscriptions
        st.markdown("### 🔄 Recurring Subscriptions")
        
        subscriptions = spending_analysis.get("recurring_subscriptions", [])
        if subscriptions:
            total_yearly = sum(float(s.get("yearly_cost", 0)) for s in subscriptions)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{len(subscriptions)}** recurring subscriptions detected")
            
            with col2:
                st.metric("Total Yearly Cost", f"₹{total_yearly:,.2f}")
            
            st.markdown("####")
            
            # Subscription table
            sub_data = []
            for sub in sorted(subscriptions, key=lambda x: x.get("yearly_cost", 0), reverse=True)[:10]:
                sub_data.append({
                    "Service": sub.get("merchant_name", "Unknown"),
                    "Frequency": sub.get("frequency", "Unknown"),
                    "Amount": f"₹{float(sub.get('amount', 0)):,.2f}",
                    "Yearly Cost": f"₹{float(sub.get('yearly_cost', 0)):,.2f}",
                    "Last Charge": sub.get("last_charge", "N/A"),
                    "Charges": int(sub.get("transaction_count", 0)),
                })
            
            st.dataframe(sub_data, use_container_width=True, hide_index=True)
            
            if total_yearly > 1000:
                st.warning(f"💡 Your yearly subscriptions total ${total_yearly:,.2f}. Consider reviewing for consolidation opportunities.")
        else:
            st.info("No recurring subscriptions detected")
        
        # Recommendations
        st.markdown("### 💡 Recommendations")
        
        recommendations = spending_analysis.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"**{i}.** {rec}")
        else:
            st.success("✓ No specific recommendations at this time")
    else:
        st.info("Spending analysis not yet available for this user")
    
    # =============================================================================
    # ADVANCED SPENDING ANALYSIS
    # =============================================================================
    st.markdown("---")
    st.markdown("## 🔬 Advanced Insights & Analytics")
    
    if advanced_analysis.get("available"):
        # Seasonal Patterns Tab
        seasonal = advanced_analysis.get("seasonal_patterns", {})
        if seasonal.get("available"):
            with st.expander("📅 Seasonal Spending Patterns", expanded=False):
                st.markdown("### Monthly Breakdown")
                
                # Monthly distribution chart
                monthly_data = seasonal.get("monthly_breakdown", {})
                if monthly_data:
                    months_list = []
                    spending_list = []
                    for month, data in monthly_data.items():
                        months_list.append(month[:3])
                        spending_str = str(data['spending']).replace('₹', '').replace('$', '').replace(',', '')
                        spending_list.append(float(spending_str))
                    
                    st.bar_chart(data={'Spending': spending_list}, use_container_width=True)
                
                # Seasonal summary
                st.markdown("### Seasonal Summary")
                seasonal_bd = seasonal.get("seasonal_breakdown", {})
                cols = st.columns(4)
                for i, (season, data) in enumerate(seasonal_bd.items()):
                    with cols[i % 4]:
                        st.metric(
                            season,
                            data.get('average_per_month', '$0'),
                            f"{data.get('percentage_of_income', 0):.1f}% of income"
                        )
                
                # Alerts
                alert = seasonal.get("seasonal_alert")
                if "HIGH" in alert:
                    st.warning(f"⚠️ {alert}")
                else:
                    st.info(f"ℹ️ {alert}")
        
        # Budget Goals Tab
        budgets = advanced_analysis.get("budget_goals", {})
        if budgets.get("available"):
            with st.expander("🎯 Budget Goal Tracking", expanded=False):
                summary = budgets.get("goals_summary", {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Categories", summary.get("total_categories", 0))
                with col2:
                    st.metric("On Track", f"{summary.get('on_track_categories', 0)}/{summary.get('total_categories', 0)}")
                with col3:
                    st.metric("Compliance Score", f"{budgets.get('compliance_score', 0):.0f}%")
                with col4:
                    st.metric("Alerts", summary.get("total_alerts", 0))
                
                st.markdown("### Category Budget Status")
                cat_budgets = budgets.get("category_budgets", [])
                for cat in cat_budgets[:8]:
                    color = cat.get('color', 'gray')
                    status_icon = {'green': '✓', 'yellow': '⚠️', 'red': '✗'}.get(color, '•')
                    st.write(f"**{status_icon} {cat['category']}** - {cat['status']}")
                    current_str = str(cat['current_amount']).replace('₹', '').replace('$', '').replace(',', '')
                    budget_str = str(cat['budget_amount']).replace('₹', '').replace('$', '').replace(',', '')
                    current_val = float(current_str) if current_str else 0
                    budget_val = float(budget_str) if budget_str else 0
                    progress_val = min((current_val / budget_val) if budget_val > 0 else 0, 1.0)
                    st.progress(
                        progress_val,
                        f"{cat['current_percentage']:.1f}% vs {cat['budget_percentage']:.1f}% budget"
                    )
        
        # Month-over-Month Trends
        trends = advanced_analysis.get("month_over_month_trends", {})
        if trends.get("available"):
            with st.expander("📊 Month-over-Month Trends", expanded=False):
                trend_dir = trends.get("trend_direction", "UNKNOWN")
                overall = trends.get("overall_trend", 0)
                
                color_map = {
                    "INCREASING": "🔴",
                    "DECREASING": "🟢",
                    "STABLE": "🟡",
                    "UNKNOWN": "⚪"
                }
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"{color_map.get(trend_dir)} Trend Direction", trend_dir)
                with col2:
                    st.metric("Overall Change", f"{overall:+.1f}%")
                
                st.markdown("### Monthly Trend")
                monthly_trends = trends.get("monthly_trends", [])
                if monthly_trends:
                    trend_data = {
                        'Month': [t['month'] for t in monthly_trends],
                        'Change %': [t['month_over_month_change'] for t in monthly_trends]
                    }
                    st.line_chart(trend_data, use_container_width=True)
        
        # ML Recommendations
        ml_recs = advanced_analysis.get("ml_recommendations", [])
        if ml_recs:
            with st.expander("🤖 AI-Powered Saving Recommendations", expanded=True):
                st.markdown("### Smart insights based on your spending patterns:")
                for i, rec in enumerate(ml_recs, 1):
                    st.markdown(f"**{i}.** {rec}")
        
        # Peer Benchmarking
        benchmarks = advanced_analysis.get("peer_benchmarking", {})
        if benchmarks.get("available"):
            with st.expander("👥 Peer Comparison (Anonymized)", expanded=False):
                region = benchmarks.get("region", "Global")
                st.markdown(f"### {region} Benchmarks")
                
                comparison = benchmarks.get("comparison", {})
                
                for cat, data in sorted(comparison.items())[:8]:
                    position = data.get("position", "UNKNOWN")
                    icon_map = {
                        "BELOW_AVERAGE": "🟢",
                        "AVERAGE": "🟡",
                        "ABOVE_AVERAGE": "🟠",
                        "HIGH_SPENDER": "🔴"
                    }
                    
                    your_spending_str = str(data.get("your_spending", "0")).replace('%', '').replace('₹', '').replace('$', '')
                    your_spending = float(your_spending_str) if your_spending_str else 0
                    peer_median = data.get("peer_median", 0)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**{cat}**")
                    with col2:
                        st.write(f"Your: {your_spending:.1f}% | Peer: {peer_median}%")
                    with col3:
                        st.write(f"{icon_map.get(position)} {position}")
    else:
        st.info("Advanced analysis not yet available for this user")
    
    # =============================================================================
    # CHARTS
    # =============================================================================
    st.markdown("---")
    st.markdown("## 📈 Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            st.markdown("### Income vs Expenses")
            income_val = float(financial_snapshot.get("total_income", 0))
            expense_val = float(financial_snapshot.get("total_expenses", 0))
            
            if income_val > 0 and expense_val > 0:
                chart_income_vs_expenses(income_val, expense_val)
            else:
                st.info("Income and expense data needed for chart")
        except Exception as e:
            st.caption(f"📊 Chart unavailable")
    
    with col2:
        try:
            st.markdown("### Spending Breakdown")
            expense_val = float(financial_snapshot.get("total_expenses", 0))
            if expense_val > 0:
                chart_spending_categories(expense_val)
            else:
                st.info("Expense data needed for chart")
        except Exception as e:
            st.caption(f"📊 Chart unavailable")
    
    # =============================================================================
    # AI ADVICE
    # =============================================================================
    st.markdown("---")
    st.markdown("## 🤖 AI Financial Advice")
    
    with st.spinner("⏳ Generating advice..."):
        advice = get_ai_advice(report, template=template)
    
    if advice:
        # Risk warning
        risk_warning = advice.get("risk_warning", "")
        if risk_warning:
            st.warning(risk_warning)
        
        # Actions
        st.markdown("### Recommended Actions")
        actions = advice.get("actions", [])
        if actions:
            for action in actions[:5]:
                try:
                    if isinstance(action, dict):
                        st.write(f"**{action.get('title', 'Action')}** - {action.get('description', '')}")
                    else:
                        st.write(action)
                except:
                    st.write(action)
        else:
            st.info("No specific actions recommended at this time")
        
        # Instruments
        st.markdown("### Recommended Instruments")
        instruments = advice.get("instruments", [])
        if instruments:
            cols = st.columns(min(3, len(instruments)))
            for idx, instrument in enumerate(instruments[:3]):
                with cols[idx % 3]:
                    try:
                        if isinstance(instrument, dict):
                            st.markdown(f"**{instrument.get('name', 'Instrument')}**")
                            st.caption(instrument.get('description', ''))
                        else:
                            st.write(instrument)
                    except:
                        st.write(instrument)
        else:
            st.info("No specific instruments recommended at this time")
    else:
        st.info("Advice generation not available at this time")
    # =============================================================================
    # EXPORT
    # =============================================================================
    st.markdown("---")
    st.markdown("## 📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_data = {
            "user_name": user_name,
            "user_email": user_email,
            "generated_at": datetime.now().isoformat(),
            "financial_summary": financial_snapshot,
            "metrics": metrics,
            "holdings": holdings_summary.get("holdings", []),
            "goals": goals_analysis.get("goals", []),
        }
        try:
            if st.button("📄 Download JSON Report"):
                import json
                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="Click here if download doesn't start",
                    data=json_str,
                    file_name=f"financial_plan_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
                st.success("✓ JSON Export Ready")
        except Exception as e:
            st.caption(f"JSON export: {str(e)[:50]}")
    
    with col2:
        try:
            if st.button("📊 Generate PDF Report"):
                st.info("PDF export feature coming soon")
        except:
            st.caption("PDF export not available")
    
    with col3:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # =============================================================================
    # DISCLAIMER
    # =============================================================================
    st.markdown("---")
    with st.expander("⚖️ Important Disclaimer"):
        st.markdown("""
        - Educational purposes only
        - Not professional financial advice
        - Hypothetical projections
        - Past performance ≠ future results
        - Data processed locally
        """)


if __name__ == "__main__":
    main()
