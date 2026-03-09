# SmartBridge Frontend - Manual Test Plan

## Overview

This document provides a comprehensive manual test plan for the SmartBridge Streamlit financial dashboard. All tests should be executed in sequence to ensure proper functionality of the dashboard.

## Test Environment Setup

### Prerequisites
- Python 3.10+
- Backend services running (FastAPI server on `http://localhost:8000`)
- All dependencies installed: `pip install -r requirements.txt`
- Streamlit installed: `pip install streamlit streamlit-plotly-events`

### Starting the Dashboard
```bash
cd frontend/
streamlit run streamlit_app.py
```

Expected: Streamlit should start on `http://localhost:8501`

## Functional Test Cases

### Test 1: Dashboard Loads Successfully
**Purpose**: Verify that the dashboard loads without errors
**Steps**:
1. Navigate to `http://localhost:8501`
2. Observe the dashboard homepage

**Expected Result**:
- Page title "💰 SmartBridge Financial Dashboard" is visible
- Subtitle "AI-powered financial analysis and personalized advice" is displayed
- Welcome info box is displayed
- No error messages in browser console
- Sidebar is visible with navigation options

**Performance Target**: < 3 seconds
**Status**: [ ] Pass / [ ] Fail

---

### Test 2: User Selection & Consent Flow
**Purpose**: Verify that user selection and consent mechanism works correctly
**Steps**:
1. In sidebar, look for "👤 User Selection" section
2. Click on the "Select a user to analyze" dropdown
3. Observe the list of available demo users
4. Do NOT check consent checkbox yet
5. Try to navigate to different page or wait for data load

**Expected Result**:
- Dropdown displays at least 3 demo users:
  - Demo User One (demo1@smartbridge.com)
  - Demo User Two (demo2@smartbridge.com)
  - Demo User Three (demo3@smartbridge.com)
- Without consent, page shows warning: "Please check the consent box to proceed"
- No financial data is displayed until consent is checked

**Performance Target**: < 1 second
**Status**: [ ] Pass / [ ] Fail

---

### Test 3: Dashboard Populates After Consent & User Selection
**Purpose**: Verify that financial data loads after selecting user and providing consent
**Steps**:
1. In sidebar, select a user from dropdown (e.g., "Demo User One")
2. Check the "I understand and consent..." checkbox
3. Wait for report to load

**Expected Result**:
- Page displays "### Welcome, [User Name]! 👋"
- Email address is shown: "Analyzing financial data for: demo1@smartbridge.com"
- 📊 Financial Summary section appears with 8 metric cards:
  - Monthly Income (₹ format, e.g., "₹1,00,000.00")
  - Monthly Expenses (₹ format)
  - Savings Balance (₹ format)
  - Total Debt (₹ format)
  - Savings Rate (e.g., "45.50%")
  - Debt-to-Income (e.g., "0.25")
  - Emergency Fund (e.g., "6.5 months")
  - Health Score (e.g., "75/100")
- No error messages
- Loading spinner appears and disappears

**Performance Target**: < 3 seconds total load time
**Status**: [ ] Pass / [ ] Fail

---

### Test 4: Summary Metrics Display with Correct Formatting
**Purpose**: Verify that currency and numeric formatting is correct
**Steps**:
1. After dashboard loads with a selected user
2. Examine all metric cards in 📊 Financial Summary section
3. Note the exact values displayed

**Expected Result**:
- All currency values show ₹ symbol
- All currency values formatted with commas: ₹1,00,000.00 (Indian format)
- All percentages show decimal format: X.XX%
- No values show as "NaN", "undefined", or "null"
- Ratios display with appropriate precision

**Example Formatting**:
- Income: ₹60,000.00
- Expenses: ₹30,000.00
- Savings Rate: 50.00%
- Debt-to-Income: 0.15
- Emergency Fund: 6.5 months
- Health Score: 75/100

**Status**: [ ] Pass / [ ] Fail

---

### Test 5: Charts Render Successfully
**Purpose**: Verify that all 4 chart types render without errors
**Steps**:
1. Scroll down to "📈 Financial Visualizations" section
2. Observe all charts
3. Hover over each chart element to verify interactivity

**Expected Result**:
- **Income vs Expenses** (bar chart):
  - Shows two bars: Income (green) and Expenses (red)
  - Values displayed on hover
  - Responsive to window width
  
- **Spending Categories** (pie chart):
  - Shows 6 categories: Housing, Food, Transportation, Utilities, Entertainment, Other
  - Percentages displayed
  - Colors are distinct and readable
  
- **Holdings Allocation** (donut chart, if holdings exist):
  - Shows asset allocation
  - Center is empty (donut style)
  - Hover shows labels and percentages
  
- **Goal Projections** (line chart, if goals exist):
  - Shows projection line with dots for each month
  - Target line displayed as dashed green line
  - Title shows goal name
  - X-axis labeled "Months", Y-axis labeled "₹"

**Status**: [ ] Pass / [ ] Fail

---

### Test 6: Assumptions Editor & Recalculation
**Purpose**: Verify that assumption editor allows changes and triggers recalculation
**Steps**:
1. Scroll to "🎚️ Interactive Assumptions" section
2. Click on "Edit Assumptions (changes will recalculate metrics)" expander
3. Observe sliders for:
   - Expected Annual Return (%) - range 0-20%
   - Inflation Rate (%) - range 0-10%
4. Move "Expected Annual Return" slider from default (6%) to 10%
5. Move "Inflation Rate" slider to 5%
6. Observe if metrics/charts update

**Expected Result**:
- Sliders appear with default values
- Slider values update in real-time as user drags
- When assumption values change (by > 0.01%), a recalculation message appears
- "⚠️ Assumptions have changed. Recalculating..." message displays
- All metrics, charts, and advice update to reflect new assumptions
- Success message "✅ Metrics updated with new assumptions" appears
- Current assumptions section below expander shows updated values

**Performance Target**: < 5 seconds for recalculation
**Status**: [ ] Pass / [ ] Fail

---

### Test 7: AI Advice Section Displays
**Purpose**: Verify that AI-generated advice loads and displays correctly
**Steps**:
1. Scroll to "🤖 AI Financial Advice" section
2. Wait for advice to generate
3. Examine all subsections

**Expected Result**:
- Advice section displays with subsections:
  - **Risk Warning** (if present):
    - Orange/yellow warning box
    - Clear warning text
    - Readable font size
  
  - **📋 Recommended Actions** (at least 1 action):
    - Priority icon and level (🔴🟠🟡🟢🔵)
    - Title of action
    - Rationale/explanation text
    - Left border indicates card style
  
  - **💼 Recommended Instruments** (if available):
    - Shows up to 3 instruments in columns
    - Each shows: Name, Type, Allocation %, Rationale
  
  - **📐 Assumptions Used in Advice**:
    - Expected Annual Return displayed as percentage
    - Inflation Rate displayed as percentage
  
  - **📚 Sources & References** (collapsed expander):
    - Can be expanded to see references
    - Each source shows ID and snippet

**Status**: [ ] Pass / [ ] Fail

---

### Test 8: Export Functionality - JSON Download
**Purpose**: Verify that JSON export downloads correctly
**Steps**:
1. Scroll to "📥 Export Your Plan" section
2. Click "📥 Download as JSON" button
3. Check your Downloads folder
4. Open downloaded file with text editor

**Expected Result**:
- File downloads successfully named: `financial_plan_YYYYMMDD_HHMMSS.json`
- File is valid JSON (can be parsed)
- JSON contains expected fields:
  - `report_id`: Non-empty string
  - `generated_at`: ISO format datetime
  - `user_name`: User name string
  - `user_email`: User email string
  - `financial_summary`: Object with income, expenses, savings keys
  - `metrics`: Object with financial ratios
  - `advice`: Object with actions, instruments, risk_warning
  - `assumptions`: Object with assumption values
- File size > 500 bytes (not empty)

**Example JSON Structure**:
```json
{
  "report_id": "rpt_12345...",
  "generated_at": "2024-01-15T14:30:45.123456",
  "user_name": "Demo User One",
  "user_email": "demo1@smartbridge.com",
  "financial_summary": {
    "total_income": 60000,
    "total_expenses": 30000,
    "total_savings": 15000,
    ...
  },
  "metrics": {...},
  "advice": {...},
  "assumptions": {
    "expected_annual_return": 0.06,
    "inflation": 0.03
  }
}
```

**Status**: [ ] Pass / [ ] Fail

---

### Test 9: Export Functionality - PDF Download
**Purpose**: Verify that PDF export downloads correctly (if reportlab available)
**Steps**:
1. In "📥 Export Your Plan" section
2. Click "📄 Download as PDF" button
3. Check Downloads folder
4. Try to open downloaded file

**Expected Result - If reportlab installed**:
- File downloads successfully named: `financial_plan_YYYYMMDD_HHMMSS.pdf`
- File is valid PDF format
- Can be opened in PDF reader
- Contains:
  - Title: "Financial Plan & Advice Report"
  - Generated date/time
  - User name and email
  - Financial summary section with metrics
  - Risk warning
  - Disclaimer text

**Expected Result - If reportlab NOT installed**:
- PDF button displays warning: "reportlab not installed. Use JSON export instead."
- JSON export still works

**Status**: [ ] Pass / [ ] Fail

---

### Test 10: Sidebar Settings - Template Selection
**Purpose**: Verify that advice template selection works
**Steps**:
1. In sidebar, locate "Advice template:" radio buttons
2. Default selection is "balanced"
3. Click on "conservative" option
4. Observation: Advice section may change in tone
5. Click on "explainability" option
6. Observe any differences in advice

**Expected Result**:
- Radio buttons appear with 3 options: "balanced", "conservative", "explainability"
- Selection persists when switching users
- Advice changes style based on template selection:
  - **balanced**: Moderate risk recommendations
  - **conservative**: Capital preservation focus
  - **explainability**: More detailed reasoning in rationale

**Status**: [ ] Pass / [ ] Fail

---

### Test 11: User Switching
**Purpose**: Verify that switching between users reloads data correctly
**Steps**:
1. Start with "Demo User One" selected and loaded
2. Note the financial summary values
3. Change sidebar selection to "Demo User Two"
4. Observe dashboard updates
5. Change to "Demo User Three"
6. Note that values are different for each user

**Expected Result**:
- All metrics, charts, and advice update for new user
- Dashboard doesn't show old data mixed with new
- No error messages appear
- Page title and email change for each user
- Health score and other metrics are user-specific

**Performance Target**: < 3 seconds per user switch
**Status**: [ ] Pass / [ ] Fail

---

### Test 12: Disclaimer & Accessibility
**Purpose**: Verify that disclaimers are prominent and accessibility features work
**Steps**:
1. Look for disclaimer at top of page (welcome box)
2. Scroll to "⚖️ Important Information" section at bottom
3. Examine disclaimer box
4. Check if all currency symbols (₹) display correctly
5. Test page zoom (Ctrl+Plus) to verify text size is adjustable

**Expected Result**:
- Top info box states: "This is a demo dashboard for financial education"
- Bottom disclaimer box contains:
  - "📋 Disclaimer" heading
  - Text: "Educational and demonstration purposes only"
  - Text: "We are not registered financial advisors"
  - Clear, readable font
- Section "About This Dashboard" lists:
  - Intended Use
  - No Professional Advice
  - Hypothetical projections
  - Performance disclaimer
  - Data Privacy statement
- All ₹ currency symbols render correctly (not as boxes or question marks)
- Page is readable at 150% zoom
- Text maintains proper spacing

**Status**: [ ] Pass / [ ] Fail

---

### Test 13: Debug Information
**Purpose**: Verify that debug info is available for troubleshooting
**Steps**:
1. Scroll to very bottom of page
2. Locate "🔧 Debug Information" expander
3. Click to expand

**Expected Result**:
- Expander contains:
  - **User ID**: Shows first 6 characters of UUID (formatted as "XXX...")
  - **Report ID**: Shows first 30 characters of report ID
  - **Generated At**: Shows ISO format datetime
  - **Session State Keys**: Shows list of Streamlit session keys in use
- All values are non-empty and properly formatted

**Status**: [ ] Pass / [ ] Fail

---

## Edge Case Tests

### Test 14: Handling No User Selected
**Purpose**: Verify graceful handling when no user is selected
**Steps**:
1. Reload page (Ctrl+R)
2. Do NOT select a user
3. Do NOT check consent
4. Wait 2 seconds

**Expected Result**:
- Dashboard shows header and welcome box
- No financial data displayed
- Sidebar shows user selection dropdown (empty initially)
- No error messages
- Page is still interactive

**Status**: [ ] Pass / [ ] Fail

---

### Test 15: Handling Missing Holdings Data
**Purpose**: Verify dashboard still works when user has no holdings
**Steps**:
1. Select a user that may not have holdings portfolio
2. Wait for dashboard to load
3. Look for Holdings Allocation chart section

**Expected Result**:
- If holdings exist: Donut chart displays
- If holdings don't exist: Section either hidden or shows "No holdings to display" message
- No error messages
- Rest of dashboard functions normally (except holdings chart)

**Status**: [ ] Pass / [ ] Fail

---

### Test 16: Handling Missing Goals Data
**Purpose**: Verify dashboard works when user has no savings goals
**Steps**:
1. Select a user with no goals configured
2. Look for Goal Projections section

**Expected Result**:
- If goals exist: Tab-based chart view for each goal
- If goals don't exist: Section is hidden or shows "No goals configured"
- No error messages
- Rest of dashboard functions

**Status**: [ ] Pass / [ ] Fail

---

### Test 17: API Timeout Handling
**Purpose**: Verify graceful error handling if backend API is slow
**Steps**:
1. Stop backend service (kill FastAPI server)
2. Try to load user data or recalculate with assumptions
3. Wait for timeout (default: 5 seconds)

**Expected Result**:
- Error message appears: "Failed to load report: ..." or similar
- Dashboard doesn't hang/freeze
- Page remains interactive
- User can still interact with sidebar settings
- Error message is informative (shows actual API error if available)

**Status**: [ ] Pass / [ ] Fail

---

### Test 18: Multiple Rapid Assumption Changes
**Purpose**: Verify stability under rapid assumption adjustments
**Steps**:
1. Open assumptions editor
2. Quickly drag sliders back and forth 5-10 times
3. Wait for recalculation to complete after each change
4. Observe metrics update

**Expected Result**:
- Dashboard remains responsive
- No duplicate requests (only last change triggers recalc)
- Charts update smoothly without flicker
- No memory leaks or performance degradation
- Success message appears after final calculation

**Status**: [ ] Pass / [ ] Fail

---

### Test 19: Browser Refresh During Load
**Purpose**: Verify stability if user refreshes page
**Steps**:
1. Start loading a user
2. While charts are loading, press Ctrl+R to refresh
3. Let page reload completely

**Expected Result**:
- Page reloads cleanly
- Previously selected user remains selected (due to Streamlit session state)
- All data reloads correctly
- No duplicate requests visible
- No error messages

**Status**: [ ] Pass / [ ] Fail

---

### Test 20: Responsive Design - Mobile View
**Purpose**: Verify dashboard works on mobile screen sizes
**Steps**:
1. Open browser DevTools (F12)
2. Toggle device emulation (Ctrl+Shift+M)
3. Select iPhone 12 or similar mobile device
4. Load dashboard with user selected
5. Scroll through all sections
6. Try interacting with elements

**Expected Result**:
- Layout adapts to narrow screen width
- Metric cards stack vertically (not side-by-side)
- Charts still display and are interactive
- Sidebar collapses or becomes a hamburger menu
- Text is readable (not cut off)
- Buttons and sliders are touchable (large enough targets)
- No horizontal scroll bars (unless chart requires)

**Status**: [ ] Pass / [ ] Fail

---

## Performance Test Cases

### Test 21: Page Load Time
**Purpose**: Verify dashboard loads within acceptable time
**Steps**:
1. Open browser DevTools (F12)
2. Go to Performance tab
3. Select user and check consent
4. Click Reload while recording
5. Stop recording when all content is visible

**Expected Result**:
- Full page load: < 3 seconds
- Time to First Contentful Paint (FCP): < 1 second
- Time to Interactive (TTI): < 2 seconds
- No jank or stuttering during render

**Status**: [ ] Pass / [ ] Fail

---

### Test 22: Assumption Recalculation Time
**Purpose**: Verify assumption changes recalculate quickly
**Steps**:
1. Open assumptions editor
2. Change an assumption value
3. Measure time until success message appears

**Expected Result**:
- Recalculation time: < 5 seconds
- Charts update immediately after calculation
- No lag when dragging sliders
- Success confirmation displayed within 5 seconds

**Status**: [ ] Pass / [ ] Fail

---

### Test 23: Export File Size
**Purpose**: Verify exported files are reasonable size
**Steps**:
1. Export as JSON
2. Export as PDF (if available)
3. Check file sizes in file explorer

**Expected Result**:
- JSON file: 10 KB - 100 KB (reasonable for financial data)
- PDF file: 50 KB - 500 KB (reasonable for report)
- Files are not empty (> 1 KB)
- Files can be transmitted without issues

**Status**: [ ] Pass / [ ] Fail

---

## Browser Compatibility Tests

### Test 24: Chrome Browser
**Steps**:
1. Open dashboard in latest Chrome
2. Run tests 1-13 (all functional tests)

**Expected Result**: All features work correctly

**Status**: [ ] Pass / [ ] Fail

### Test 25: Firefox Browser
**Steps**:
1. Open dashboard in latest Firefox
2. Run tests 1-13

**Expected Result**: All features work correctly

**Status**: [ ] Pass / [ ] Fail

### Test 26: Safari Browser (if on Mac)
**Steps**:
1. Open dashboard in Safari
2. Run tests 1-13

**Expected Result**: All features work correctly

**Status**: [ ] Pass / [ ] Fail

---

## Summary

### Total Tests: 26
- **Functional Tests**: 13 (Tests 1-13)
- **Edge Case Tests**: 7 (Tests 14-20)
- **Performance Tests**: 3 (Tests 21-23)
- **Compatibility Tests**: 3 (Tests 24-26)

### Criteria for Pass:
- **Critical** (Tests 1-3, 8, 21): All must PASS
- **High Priority** (Tests 4-7, 22): At least 85% must PASS
- **Medium Priority** (Tests 9-13): At least 80% must PASS
- **Edge Cases** (Tests 14-20): At least 70% must PASS
- **Compatibility** (Tests 24-26): All supported browsers must PASS

### Notes:
- If a test fails, document the failure in detail:
  - Exact steps to reproduce
  - Expected vs actual behavior
  - Screenshot (if applicable)
  - Browser/device info
- All timestamps should be recorded for trend analysis
- Performance targets assume typical network (20 Mbps download)
- Accessibility tests should include:
  - Text-to-speech (WAI-ARIA labels present?)
  - Keyboard navigation (Tab/Enter works?)
  - Color contrast (readable for colorblind users?)

### Sign-off
- **Tester Name**: _________________________
- **Date**: _________________________
- **Overall Status**: [ ] PASS / [ ] FAIL
- **Notes**: _________________________

---

## Appendix A: Common Issues & Troubleshooting

### Issue: "Failed to load report: ModuleNotFoundError: No module named 'backend'"
**Solution**: Ensure `streamlit_app.py` is run from project root directory, or update `sys.path.insert(0, '.')` to correct path

### Issue: Charts don't display
**Solution**: Check if Plotly is installed (`pip install plotly`)

### Issue: PDF export not working
**Solution**: Install reportlab (`pip install reportlab`) or use JSON export as fallback

### Issue: Page hangs when loading
**Solution**: Check if backend service is running; verify database connections

### Issue: Currency symbols show as boxes
**Solution**: Ensure UTF-8 encoding is set in browser; update browser font settings

---

## Appendix B: API Verification Checklist

Before running tests, verify these API endpoints are working:

- [ ] `GET /health` returns 200
- [ ] `GET /users` returns list of users
- [ ] `GET /reports/{user_id}` returns financial report
- [ ] `GET /reports/{user_id}?assumptions={json}` returns recalculated report (if implemented)
- [ ] All responses contain required fields (report_id, metrics, advice, etc.)

---

## Appendix C: Data Validation

Verify the following for all financial data:

- [ ] All currency values are numeric (not strings)
- [ ] All percentages are between 0 and 1 (or 0-100 depending on convention)
- [ ] All dates are valid ISO format
- [ ] No null/undefined values in critical fields
- [ ] Sum of allocations ≈ 100% (or verify logic)
- [ ] Income > Expenses (for positive savings rate examples)

