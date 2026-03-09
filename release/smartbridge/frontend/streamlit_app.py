"""Streamlit dashboard for financial analysis and AI advice.

This dashboard integrates with the backend financial analysis engine to:
- Display financial metrics and summaries
- Show AI-generated financial advice
- Allow interactive assumption adjustments
- Export financial plans as JSON or PDF
"""

import streamlit as st
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

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
    page_title="SmartBridge Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
    .advice-card {
        padding: 1rem;
        border-left: 4px solid #2196F3;
        background-color: #f0f7ff;
        margin-bottom: 0.5rem;
        border-radius: 0.25rem;
    }
    .warning-box {
        padding: 1rem;
        border-left: 4px solid #ff9800;
        background-color: #fff3e0;
        border-radius: 0.25rem;
    }
    .success-box {
        padding: 1rem;
        border-left: 4px solid #4caf50;
        background-color: #f1f8e9;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# STATE & CACHING
# =============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_sample_users() -> List[Dict[str, Any]]:
    """Load sample users from backend.
    
    API Endpoint: GET /users (or /users?limit=10)
    Sample Response:
    [
        {
            "id": "uuid-1",
            "email": "user1@example.com",
            "name": "User One",
            "country": "USA"
        },
        ...
    ]
    """
    try:
        # For demo, create mock users since backend might not have /users endpoint yet
        return [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Demo User One",
                "email": "demo1@smartbridge.com",
                "country": "USA",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Demo User Two",
                "email": "demo2@smartbridge.com",
                "country": "India",
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "name": "Demo User Three",
                "email": "demo3@smartbridge.com",
                "country": "UK",
            },
        ]
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        return []


def get_financial_report(
    user_id: str,
    assumptions: Optional[Dict[str, float]] = None,
) -> Optional[Dict[str, Any]]:
    """Get financial report from backend.
    
    API Endpoint: GET /reports/{user_id}[?assumptions=...]
    Sample Request:
    GET /reports/550e8400-e29b-41d4-a716-446655440001?assumptions={"expected_annual_return": 0.07}
    
    Sample Response:
    {
        "report_id": "...",
        "report_generated_at": "2024-01-01T12:00:00Z",
        "user_profile": {...},
        "financial_snapshot": {...},
        "computed_metrics": {...},
        "holdings_summary": {...},
        "goals_analysis": {...},
        "overall_health_score": 72,
        "assumptions_used": {...}
    }
    """
    try:
        # Create mock report for demo (replace with actual API call when backend ready)
        from backend.finance.report_builder import build_user_report
        from backend.db import SessionLocal
        
        db = SessionLocal()
        report = build_user_report(user_id, db, assumptions=assumptions)
        db.close()
        
        return report
    except Exception as e:
        st.error(f"Failed to load report: {e}")
        return None


@st.cache_data(ttl=300)
def get_ai_advice(
    report: Dict[str, Any],
    template: str = "balanced",
) -> Optional[Dict[str, Any]]:
    """Get AI advice from backend.
    
    API Endpoint: POST /advice or call local function
    Sample Request:
    {
        "report": {...},  # Financial report
        "template": "balanced"  # conservative, balanced, explainability
    }
    
    Sample Response:
    {
        "actions": [...],
        "instruments": [...],
        "risk_warning": "...",
        "assumptions": {...},
        "sources": [...]
    }
    """
    try:
        with loading_spinner("Generating AI advice..."):
            from backend.ai.ai_client import generate_advice
            
            advice = generate_advice(report, template=template)
            return advice
    except Exception as e:
        st.error(f"Failed to generate advice: {e}")
        return None


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main dashboard application."""
    
    # Header
    st.markdown("# 💰 SmartBridge Financial Dashboard")
    st.markdown("*AI-powered financial analysis and personalized advice*")
    
    # Disclaimer bar
    st.info(
        "**Welcome!** This is a demo dashboard for financial education. "
        "View our full disclaimer below."
    )
    
    # Sidebar: User selection
    with st.sidebar:
        st.markdown("## 👤 User Selection")
        
        users = load_sample_users()
        if not users:
            st.error("No sample users available")
            return
        
        user_options = {f"{u['name']} ({u['email']})" : u for u in users}
        selected_user_display = st.selectbox(
            "Select a user to analyze:",
            options=list(user_options.keys()),
            help="Choose a user to load their financial data"
        )
        
        selected_user = user_options[selected_user_display]
        user_id = selected_user['id']
        user_name = selected_user['name']
        
        st.markdown("---")
        st.markdown("## ⚙️ Settings")
        
        # Template selection
        template = st.radio(
            "Advice template:",
            ["balanced", "conservative", "explainability"],
            help="Choose the style of financial advice"
        )
        
        # Consent checkbox
        st.markdown("### 📋 Data Consent")
        consent = consent_checkbox(key="main_consent")
        
        if not consent:
            st.warning("Please check the consent box to proceed")
            return
    
    # Clear cache on user change (to force reload)
    if 'last_user_id' in st.session_state and st.session_state.last_user_id != user_id:
        get_financial_report.clear()
        get_ai_advice.clear()
    st.session_state.last_user_id = user_id
    
    # Load report with default assumptions
    report = get_financial_report(user_id)
    
    if not report:
        st.error(f"Could not load financial data for user. User ID: {user_id[:6]}...")
        return
    
    # Extract initial data
    user_profile = report.get("user_profile", {})
    metrics = report.get("computed_metrics", {})
    financial_snapshot = report.get("financial_snapshot", {})
    holdings_summary = report.get("holdings_summary", {})
    goals_analysis = report.get("goals_analysis", {})
    current_assumptions = report.get("assumptions_used", {})
    
    st.markdown(f"### Welcome, {user_name}! 👋")
    st.caption(f"Analyzing financial data for: {user_profile.get('email', 'N/A')}")
    
    # =============================================================================
    # SUMMARY METRICS SECTION
    # =============================================================================
    st.markdown("---")
    st.markdown("## 📊 Financial Summary")
    
    # Format metrics for display
    display_metrics = {
        "monthly_income": financial_snapshot.get("total_income", 0),
        "monthly_expenses": financial_snapshot.get("total_expenses", 0),
        "savings_balance": financial_snapshot.get("total_savings", 0),
        "total_debt": 0,  # Not in report, could be calculated
        "savings_rate": metrics.get("savings_rate", 0),
        "debt_to_income": metrics.get("debt_to_income_ratio", 0),
        "emergency_fund_months": metrics.get("emergency_fund_months", 0),
        "financial_health_score": report.get("overall_health_score", 0),
    }
    
    summary_cards(display_metrics)
    
    # =============================================================================
    # CHARTS SECTION
    # =============================================================================
    st.markdown("---")
    st.markdown("## 📈 Financial Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chart_income_vs_expenses(
            financial_snapshot.get("total_income", 0),
            financial_snapshot.get("total_expenses", 0),
        )
    
    with col2:
        chart_spending_categories(
            financial_snapshot.get("total_expenses", 0),
        )
    
    # Holdings allocation
    holdings = holdings_summary.get("holdings", [])
    if holdings:
        chart_holdings_allocation(holdings)
    
    # Goal projections
    goals = goals_analysis.get("goals", [])
    if goals:
        st.markdown("### Goal Projections")
        goal_tabs = st.tabs([g.get("goal_name", "Goal") for g in goals[:3]])  # Limit to 3 tabs
        for tab, goal in zip(goal_tabs, goals[:3]):
            with tab:
                chart_goal_projection(
                    goal.get("goal_name", "Goal"),
                    goal.get("target_amount", 0),
                    goal.get("current_amount", 0),
                    goal.get("projection_samples", []),
                )
    
    # =============================================================================
    # ASSUMPTIONS & RECALCULATION SECTION
    # =============================================================================
    st.markdown("---")
    st.markdown("## 🎚️ Interactive Assumptions")
    
    # Display current assumptions and allow adjustment
    with st.expander("Edit Assumptions (changes will recalculate metrics)", expanded=False):
        updated_assumptions = assumptions_section(current_assumptions)
        
        # Check if assumptions changed
        assumptions_changed = False
        for key, value in updated_assumptions.items():
            if key in current_assumptions:
                if abs(current_assumptions[key] - value) > 0.0001:
                    assumptions_changed = True
                    break
        
        if assumptions_changed:
            st.info("⚠️ Assumptions have changed. Recalculating...")
            
            # Recalculate with new assumptions
            updated_report = get_financial_report(user_id, assumptions=updated_assumptions)
            
            if updated_report:
                # Clear cache and reload
                report = updated_report
                metrics = report.get("computed_metrics", {})
                financial_snapshot = report.get("financial_snapshot", {})
                current_assumptions = updated_assumptions
                
                st.success("✅ Metrics updated with new assumptions")
    
    # Display current assumptions
    st.markdown("### Current Assumptions")
    assumptions_cols = st.columns(3)
    
    assumption_items = [
        ("Expected Annual Return", "expected_annual_return"),
        ("Inflation Rate", "inflation"),
        ("Expected Equity Return", "expected_equity_return"),
    ]
    
    for idx, (label, key) in enumerate(assumption_items):
        col = assumptions_cols[idx % 3]
        value = current_assumptions.get(key, 0)
        with col:
            if isinstance(value, float) and value <= 1:
                st.metric(label, f"{value:.2%}")
            else:
                st.metric(label, f"{value:.2f}")
    
    # =============================================================================
    # AI ADVICE SECTION
    # =============================================================================
    st.markdown("---")
    st.markdown("## 🤖 AI Financial Advice")
    
    with loading_spinner("Generating personalized advice..."):
        advice = get_ai_advice(report, template=template)
    
    if advice:
        # Risk warning
        risk_warning = advice.get("risk_warning", "")
        if risk_warning:
            risk_warning_box(risk_warning)
        
        # Actions/Recommendations
        st.markdown("### 📋 Recommended Actions")
        actions = advice.get("actions", [])
        for action in actions[:5]:  # Limit to 5
            with st.container():
                st.markdown('<div class="advice-card">', unsafe_allow_html=True)
                advice_action_card(action)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Instruments
        st.markdown("### 💼 Recommended Instruments")
        instruments = advice.get("instruments", [])
        instr_cols = st.columns(min(3, len(instruments)))
        for idx, instrument in enumerate(instruments[:3]):  # Limit to 3 columns
            with instr_cols[idx % 3]:
                advice_instrument_card(instrument)
        
        # Assumptions used
        st.markdown("### 📐 Assumptions Used in Advice")
        advice_assumptions = advice.get("assumptions", {})
        assumptions_cols = st.columns(2)
        with assumptions_cols[0]:
            st.metric("Expected Annual Return", f"{advice_assumptions.get('expected_annual_return', 0):.2%}")
        with assumptions_cols[1]:
            st.metric("Inflation Rate", f"{advice_assumptions.get('inflation', 0):.2%}")
        
        # Sources
        sources = advice.get("sources", [])
        if sources:
            with st.expander("📚 Sources & References"):
                for source in sources:
                    st.write(f"**{source.get('id', 'Source')}**: {source.get('text_snippet', '')}")
    
    # =============================================================================
    # EXPORT SECTION
    # =============================================================================
    st.markdown("---")
    st.markdown("## 📥 Export Your Plan")
    
    # Prepare export data
    export_data = {
        "report_id": report.get("report_id", ""),
        "generated_at": datetime.now().isoformat(),
        "user_name": user_name,
        "user_email": user_profile.get("email", ""),
        "financial_summary": financial_snapshot,
        "metrics": metrics,
        "advice": advice if advice else {},
        "assumptions": current_assumptions,
    }
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        export_button_json(
            export_data,
            filename=f"financial_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
    
    with export_col2:
        # Prepare HTML for PDF
        html_content = f"""
        <h1>Financial Plan & Advice Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>User: {user_name} ({user_profile.get('email', 'N/A')})</p>
        
        <h2>Financial Summary</h2>
        <ul>
            <li>Monthly Income: ₹{financial_snapshot.get('total_income', 0):,.0f}</li>
            <li>Monthly Expenses: ₹{financial_snapshot.get('total_expenses', 0):,.0f}</li>
            <li>Savings Rate: {metrics.get('savings_rate', 0):.1f}%</li>
            <li>Financial Health Score: {report.get('overall_health_score', 0)}/100</li>
        </ul>
        
        <h2>Risk Warning</h2>
        <p>{advice.get('risk_warning', 'N/A') if advice else 'N/A'}</p>
        """
        
        export_button_pdf(
            html_content,
            filename=f"financial_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    
    with export_col3:
        st.button("🔄 Refresh Data", key="refresh_btn", help="Clear cache and reload all data")
    
    # =============================================================================
    # FOOTER & DISCLAIMERS
    # =============================================================================
    st.markdown("---")
    st.markdown("## ⚖️ Important Information")
    
    disclaimer_box()
    
    st.markdown("""
    ### About This Dashboard
    - **Intended Use**: Educational and demonstration purposes only
    - **No Professional Advice**: We are not registered financial advisors
    - **Hypothetical**: Projections are based on assumptions and historical data
    - **Performance**: Past performance does not guarantee future results
    - **Data Privacy**: Your data is processed locally and not shared
    
    ### Contact & Support
    For questions or support, please contact our team through the main SmartBridge platform.
    """)
    
    # Debug info (collapsed)
    with st.expander("🔧 Debug Information"):
        st.write(f"**User ID**: {user_id[:6]}...")
        st.write(f"**Report ID**: {report.get('report_id', 'N/A')[:30]}...")
        st.write(f"**Generated At**: {report.get('report_generated_at', 'N/A')}")
        st.write(f"**Session State Keys**: {list(st.session_state.keys())}")


if __name__ == "__main__":
    main()
