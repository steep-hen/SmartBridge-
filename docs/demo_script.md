# SmartBridge Demo Script

**For**: B.Tech Examination & Viva  
**Duration**: ~10 minutes  
**Environment**: Local development with `docker-compose` or Python venv  

---

## Pre-Demo Setup (Run Once)

```bash
# 1. Clone and navigate to project
cd ~/SmartBridge

# 2. Start backend + database
docker-compose -f docker-compose.prod.yml up -d

# OR if using venv:
source .venv/bin/activate
python backend/app.py &

# 3. In another terminal, start Streamlit UI
streamlit run frontend/streamlit_app.py

# Expected output:
#   You can now view your Streamlit app in your browser.
#   Local URL: http://localhost:8501
#   Network URL: http://<your-ip>:8501

# 4. Open in browser: http://localhost:8501
```

---

## Demo Scenario: Create & Export SIP Plan for a User

### **Step 1: Consent Dialog** (30 seconds)

**What happens**:
- Streamlit loads, shows **Consent Dialog** asking to accept AI explanations + audit logging

**Expected Output**:
```
┌─────────────────────────────────────────────────┐
│  SmartBridge: AI-Powered Investment Planning    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ⚠️ Disclaimer & Consent Required               │
│                                                  │
│  This app uses Google Gemini AI to explain     │
│  your investment plan. All actions are         │
│  logged for audit & compliance.                │
│                                                  │
│  💬 Agree?        [ YES ]  [ NO ]              │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Demo Action**:
- Click `[ YES ]`

**Expected System Action** (backend):
```
POST /api/v1/consent
{
  "consent_type": "ai_explanations",
  "accepted": true
}
→ Response: 201 Created, consent_id=123
→ Audit log: INSERT INTO audit_events (user_id, action='consent_given', ...)
```

**Time**: 00:00 – 00:30

---

### **Step 2: Load or Create Investment Plan** (1 minute 30 seconds)

**What happens**:
- After consent, user sees form to create a new investment plan
- Fields: Age, Annual Income, Monthly Expense, Risk Profile, Retirement Age, Life Expectancy

**Demo Action**:
Enter the following values:

```
Age: 35
Annual Income (₹): 1200000
Monthly Expense (₹): 50000
Risk Profile: Moderate
Retirement Age: 60
Life Expectancy: 85
```

**Expected UI State**:
```
╔═════════════════════════════════════════════════╗
║  Create Investment Plan                         ║
╠═════════════════════════════════════════════════╣
║                                                  │
║  Age: [35_________________]                     │
║  Annual Income (₹): [1200000___________]        │
║  Monthly Expense (₹): [50000_________]          │
║                                                  │
║  Risk Profile: [Moderate ⌄]                    │
║  Retirement Age: [60___________]                │
║  Life Expectancy: [85___________]               │
║                                                  │
║                              [ Create Plan ]   │
║                                                  │
╚═════════════════════════════════════════════════╝
```

**Backend API Called**:
```
POST /api/v1/plans
{
  "age": 35,
  "annual_income": 1200000,
  "monthly_expense": 50000,
  "risk_profile": "moderate",
  "retirement_age": 60,
  "life_expectancy": 85
}

→ Response (201 Created):
{
  "plan_id": 567,
  "status": "active",
  "created_at": "2026-03-09T10:30:00Z"
}

→ Audit log: action='plan_created', plan_id=567
```

**Expected Display**:
```
✅ Plan created successfully!
   Plan ID: #567
   Status: Active
```

**Time**: 00:30 – 02:00

---

### **Step 3: Edit Assumptions** (1 minute)

**What happens**:
- User sees a collapsible "Edit Assumptions" section
- Shows expected return, inflation rate as editable sliders/text inputs
- When changed, shows a validation message (warning if outside historical norms)

**Demo Action**:
1. Expand "Edit Assumptions"
2. Change expected annual return: `8.5%` → `10.5%` (optimistic)
3. Change inflation: `5.5%` → `6.5%` (above historical)
4. Observe warning message

**Expected UI State**:
```
╔═════════════════════════════════════════════════╗
║  Edit Assumptions ⌄                            │
╠═════════════════════════════════════════════════╣
║                                                  │
║  Expected Annual Return: [10.5____]%           │
║  ⚠️ Historical range: 8-12%                     │
║     Your choice (10.5%) is within range ✓     │
║                                                  │
║  Inflation Rate: [6.5____]%                    │
║  ⚠️ Historical norms: 4-6%                      │
║     Your choice (6.5%) is above average        │
║     → Real corpus power will be lower          │
║                                                  │
║                         [ Recalculate ]        │
║                                                  │
╚═════════════════════════════════════════════════╝
```

**Backend Validation** (deterministic, no LLM):
```python
# In backend validator
historical_ranges = {
    "expected_return": (0.08, 0.12),
    "inflation": (0.04, 0.06)
}

if 0.105 in historical_ranges["expected_return"]:
    warning = "Within historical range ✓"
else:
    warning = "Outside historical norms - review carefully"
```

**Time**: 02:00 – 03:00

---

### **Step 4: Calculate SIP** (30 seconds)

**What happens**:
- Click "Recalculate" or automatic trigger after assumption change
- Backend performs **deterministic SIP calculation** (no AI)
- Results displayed: Monthly SIP Amount, Corpus at Retirement, Real Terms Corpus

**Demo Action**:
- (Auto-triggers on assumption change) or click **"Calculate Now"** button

**Expected UI State**:
```
╔═════════════════════════════════════════════════╗
║  SIP Calculation Results                       │
╠═════════════════════════════════════════════════╣
║                                                  │
║  💡 To reach your retirement goals:            │
║                                                  │
║    Monthly SIP (Nominal): ₹ 29,847              │
║    Corpus at Retirement: ₹ 1,50,00,000 (1.5 Cr)║
║    Corpus (Real Terms*): ₹ 68,50,000            │
║                                                  │
║    *Adjusted for inflation (6.5% over 25 yrs)  │
║    Investment Horizon: 25 years                 │
║                                                  │
║  Calculation ID: #890                           │
║  Timestamp: 2026-03-09 10:35:00                │
║                                                  │
╚═════════════════════════════════════════════════╝
```

**Backend Calculation** (Deterministic Formula):
```
FV = P × [((1 + r)^n - 1) / r] × (1 + r)
Solving for P (monthly SIP):
r = 10.5% / 12 / 100 = 0.00875
n = 25 × 12 = 300
P = 1,50,00,000 / [((1.00875)^300 - 1) / 0.00875 × 1.00875]
→ P ≈ ₹29,847

Real corpus = 1,50,00,000 / (1.065)^25 ≈ ₹68,50,000
```

**Audit Logged**:
```
INSERT INTO audit_events 
  (user_id, action='calculate', resource_id=890, timestamp=..., ...)
INSERT INTO calculation_results 
  (plan_id=567, expected_return=10.5, ..., calc_id=890, ...)
```

**Time**: 03:00 – 03:30

---

### **Step 5: Generate AI Explanation (Streaming)** (2 minutes)

**What happens**:
- User clicks "Get AI Explanation" button
- Backend:
  1. Retrieves relevant documents from RAG vector DB
  2. Builds prompt with user assumptions + retrieved context
  3. Calls Google Gemini 1.5 with streaming
  4. Streams response character-by-character to Streamlit
  5. Shows fallback if Gemini fails

**Demo Action**:
- Click button: **"Explain with AI"**

**Expected UI (Before)**:
```
┌─────────────────────────────────────────────────────────┐
│  💬 AI-Explanation (Powered by Google Gemini 1.5)      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ⏳ Generating explanation...                           │
│                                                          │
│  📚 Context retrieved: 3 market insights docs matched  │
│  📤 Prompt sent to Gemini API @ 2026-03-09 10:35:42   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Expected UI (During Streaming)**:
```
┌─────────────────────────────────────────────────────────┐
│  💬 AI-Explanation (Powered by Google Gemini 1.5)      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Based on your moderate risk profile and 25-year      │
│  horizon, a monthly SIP of ₹29,847 is well-suited.    │
│  Here's why:                                            │
│                                                          │
│  1️⃣  Risk Profile Match                               │
│      Your moderate risk tolerance aligns with equity  │
│      investments averaging 10% returns historically.   │
│      This provides growth while managing volatility.   │
│                                                          │
│  2️⃣  Inflation Considerations                          │
│      At 6.5% inflation, your real purchasing power... │
│                                                          │
│  ⏸️ [Stop] | ✅ [Accept] | 🔄 [Regenerate] (disabled) │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Backend Flow** (Stream Processing):
```python
# In FastAPI route handler
@app.get("/api/v1/explain/{calc_id}", stream=True)
async def get_explanation(calc_id: int):
    # 1. Load RAG context (3-5 docs)
    rag_context = retrieve_context(calc_id, top_k=3)
    
    # 2. Build prompt
    prompt = build_explanation_prompt(calc_id, rag_context)
    
    # 3. Stream from Gemini
    async for chunk in gemini_api.stream(prompt):
        yield f"data: {chunk}\n\n"
```

**Expected Response** (Server-Sent Events):
```
data: Based on your moderate risk profile...
data: Here's why:
data: ...
data: [DONE]
```

**Audit Logged**:
```
INSERT INTO explanations 
  (calc_id=890, rag_context_used=[doc_123, doc_456, ...], 
   explanation_text='Based on...', generation_time_ms=2400, ...)
INSERT INTO audit_events 
  (action='explanation_generated', resource_id=890, ...)
```

**Time**: 03:30 – 05:30

---

### **Step 6: Edit & Re-explain** (45 seconds)

**What happens**:
- User modifies one assumption (e.g., life expectancy)
- UI shows new SIP calculation immediately
- User re-triggers explanation to see updated context

**Demo Action**:
1. Scroll back up to "Edit Assumptions"
2. Change **Life Expectancy**: `85` → `88`
3. Hit **"Recalculate"**
4. Observe new SIP amount: ~₹26,500 (lower, longer horizon)
5. Hit **"Explain Again"** to see updated explanation

**Expected UI State After Change**:
```
Monthly SIP (Nominal): ₹ 26,545  ← Updated
Corpus at Retirement: ₹ 1,35,00,000
Investment Horizon: 28 years (updated)

💬 Updated Explanation: "With a longer investment horizon..."
```

**Time**: 05:30 – 06:15

---

### **Step 7: Export to PDF** (1 minute)

**What happens**:
- User clicks "Export as PDF"
- Backend:
  1. Renders PDF (plan + calculation + explanation + audit metadata)
  2. Includes disclaimer + consent reference
  3. Stores PDF locally (or to S3 in production)
  4. Returns download link

**Demo Action**:
- Click button: **"Export as PDF"**

**Expected UI (Processing)**:
```
┌─────────────────────────────────────────────────────────┐
│  📄 Export Investment Plan                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ⏳ Generating PDF...                                  │
│     - Rendering plan summary                            │
│     - Including calculation results                     │
│     - Attaching AI explanation                          │
│     - Adding audit trail metadata                       │
│                                                          │
│  Expected time: ~3 seconds                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Expected UI (Success)**:
```
┌─────────────────────────────────────────────────────────┐
│  ✅ PDF Generated Successfully!                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Filename: smartbridge_plan_567_2026-03-09.pdf        │
│  Size: 245 KB                                            │
│  Generated: 2026-03-09 10:40:23                        │
│                                                          │
│  📎 Download Link:                                      │
│  [Download → ]  | [Copy Link] | [Email to Self]        │
│                                                          │
│  📋 PDF Contents:                                       │
│  ✓ Investment Plan Summary                              │
│  ✓ SIP Calculation Details                              │
│  ✓ AI Explanation                                       │
│  ✓ Assumptions & Warnings                               │
│  ✓ Legal Disclaimer                                     │
│  ✓ Audit Trail (Timestamp, Consent Ref)               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**PDF Contents** (Sample excerpt):
```
═══════════════════════════════════════════════════════
  S M A R T B R I D G E
  Your Personal Investment Advisor
═══════════════════════════════════════════════════════

INVESTMENT PLAN SUMMARY
Plan ID: #567 | Created: 2026-03-09 10:30:00

─────────────────────────────────────────────────────
YOUR PROFILE
─────────────────────────────────────────────────────
Age: 35 years
Risk Profile: Moderate
Retirement Age: 60 (25 years away)
Life Expectancy: 88 years

─────────────────────────────────────────────────────
SIP CALCULATION RESULTS
─────────────────────────────────────────────────────
Monthly SIP Amount: ₹ 26,545
Corpus at Retirement (Nominal): ₹ 1,35,00,000
Corpus (Real Terms, 6.5% inflation): ₹ 61,00,000

Expected Return: 10.5% p.a. | Inflation: 6.5% p.a.

─────────────────────────────────────────────────────
AI EXPLANATION
─────────────────────────────────────────────────────

Based on your moderate risk profile and 28-year
investment horizon, a monthly SIP of ₹26,545 is
well-suited. Here's why...

[Full explanation text from Gemini]

─────────────────────────────────────────────────────
ASSUMPTIONS & WARNINGS
─────────────────────────────────────────────────────

⚠️ Market Risk:
Past returns do not guarantee future performance.
Your 10.5% assumption is within historical norms
(8-12%) but is not guaranteed.

⚠️ Inflation Risk:
Real corpus power (₹61 Lakh) is significantly lower
than nominal value (₹1.35 Cr) due to inflation.

⚠️ Longevity Risk:
If you live beyond 88, you may need additional
savings planning.

─────────────────────────────────────────────────────
LEGAL DISCLAIMER
─────────────────────────────────────────────────────

This plan is EDUCATIONAL GUIDANCE, not financial
advice. SmartBridge uses AI (Google Gemini 1.5) for
explanations only, NOT for financial calculations.

Consult a SEBI-registered investment advisor before
committing funds. SmartBridge makes no guarantee of
returns. Invest responsibly.

Consent Accepted: Yes (ID: 123, Date: 2026-03-09)
Audit ID: 567/exp-890 | Generated: 2026-03-09 10:41

═══════════════════════════════════════════════════════
```

**Backend Processing**:
```python
# POST /api/v1/export
response = {
    "status": "completed",
    "pdf_url": "file:///smartbridge_plan_567_2026-03-09.pdf",
    "size_kb": 245,
    "generated_at": "2026-03-09T10:41:00Z"
}
```

**Audit Logged**:
```
INSERT INTO audit_events 
  (action='pdf_exported', resource_id=890, 
   metadata={'file_size_kb': 245, ...}, ...)
```

**Time**: 06:15 – 07:15

---

### **Step 8: Verify Audit Trail** (1 minute)

**What happens** (Backend/Admin view):
- Access audit logs to show all recorded actions

**Demo Action** (as admin/via curl):
```bash
# Query audit events for this user
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/audit-log?user_id=42&limit=10

Expected Response (200 OK):
[
  {
    "audit_id": 1001,
    "user_id": 42,
    "action": "consent_given",
    "resource_type": "consent",
    "timestamp": "2026-03-09T10:30:00Z"
  },
  {
    "audit_id": 1002,
    "user_id": 42,
    "action": "plan_created",
    "resource_id": 567,
    "timestamp": "2026-03-09T10:30:15Z"
  },
  {
    "audit_id": 1003,
    "user_id": 42,
    "action": "calculate",
    "resource_id": 890,
    "timestamp": "2026-03-09T10:35:00Z"
  },
  {
    "audit_id": 1004,
    "user_id": 42,
    "action": "explanation_generated",
    "resource_id": 890,
    "timestamp": "2026-03-09T10:37:30Z"
  },
  {
    "audit_id": 1005,
    "user_id": 42,
    "action": "pdf_exported",
    "resource_id": 890,
    "timestamp": "2026-03-09T10:41:00Z"
  }
]
```

**Display the Audit Log Table**:
```
┌─────────────────────────────────────────────────────────┐
│  Audit Trail - User #42                                │
├────────┬──────────────────┬───────────────────────┤
│ ID     │ Action           │ Timestamp             │
├────────┼──────────────────┼───────────────────────┤
│ 1001   │ consent_given    │ 2026-03-09 10:30:00  │
│ 1002   │ plan_created     │ 2026-03-09 10:30:15  │
│ 1003   │ calculate        │ 2026-03-09 10:35:00  │
│ 1004   │ explain_gen'd    │ 2026-03-09 10:37:30  │
│ 1005   │ pdf_exported     │ 2026-03-09 10:41:00  │
└────────┴──────────────────┴───────────────────────┘

✓ All actions logged immutably in PostgreSQL
✓ Timestamps match wall-clock time
✓ Compliance-ready for audit
```

**Time**: 07:15 – 08:15

---

## Summary of Demo (Total: 8 minutes 15 seconds)

| Step | Action | Time | Key Outcome |
|------|--------|------|------------|
| 1 | Give Consent | 0:30 | Consent ID created, audit logged |
| 2 | Create Plan | 1:30 | Plan #567 active, user input validated |
| 3 | Edit Assumptions | 1:00 | Warnings shown (no AI), recalc triggered |
| 4 | Calculate SIP | 0:30 | ₹26,545/mo, deterministic, logged |
| 5 | AI Explanation | 2:00 | Gemini streams explanation, RAG used, stored |
| 6 | Edit & Re-explain | 0:45 | New assumption → new SIP → new explanation |
| 7 | Export PDF | 1:00 | PDF includes all data + disclaimer + audit ref |
| 8 | Verify Audit | 1:00 | 5 events logged immutably, compliance shown |

---

## Expected Test Outputs (Post-Demo)

### Streamlit Console Output
```
2026-03-09 10:30:00 | Streamlit server started ✓
2026-03-09 10:30:05 | User session created (user_id=42)
2026-03-09 10:30:10 | Consent endpoint called → 201 Created
2026-03-09 10:30:15 | Plan creation endpoint → 201 Created
2026-03-09 10:35:00 | Calculate endpoint → 200 OK
2026-03-09 10:37:30 | Gemini streaming started
2026-03-09 10:37:35 | ...
2026-03-09 10:37:42 | Gemini streaming complete, 2400ms
2026-03-09 10:41:00 | PDF export → 200 OK
```

### Backend API Server Logs
```
INFO:     POST /api/v1/consent - 201 Created
INFO:     POST /api/v1/plans - 201 Created
INFO:     POST /api/v1/calculate - 200 OK
DEBUG:    RAG retrieval for calc_id=890 → 3 docs matched
DEBUG:    Gemini prompt: [system + user context + rag docs]
INFO:     GET /api/v1/explain/890 - Streaming complete
INFO:     POST /api/v1/export - 200 OK
INFO:     Metrics exported to Prometheus
```

### Database Verification
```sql
-- After demo, verify data integrity:
SELECT COUNT(*) FROM users WHERE email LIKE '%user%';  → 1
SELECT COUNT(*) FROM investment_plans WHERE user_id=42; → 1
SELECT COUNT(*) FROM calculation_results WHERE plan_id=567; → 1+
SELECT COUNT(*) FROM explanations WHERE calc_id=890; → 1
SELECT COUNT(*) FROM audit_events WHERE user_id=42; → 5+
SELECT COUNT(*) FROM user_consent WHERE user_id=42; → 1

-- All tables populated, audit trail intact ✓
```

---

## Troubleshooting During Demo

| Issue | Fix |
|-------|-----|
| **Gemini API timeout** | Fallback explanation shown automatically; point out fallback was triggered |
| **Streamlit won't start** | Check port 8501 not in use: `lsof -i :8501` |
| **Backend API 500 error** | Check logs: `docker-compose logs api` |
| **PDF export fails** | Check ReportLab installed: `pip list \| grep reportlab` |
| **Audit trail empty** | Verify PostgreSQL running: `docker-compose logs postgres` |

---

## Key Demo Points to Emphasize

1. **Consent is First**: User must opt-in before any tracking.
2. **Math is Deterministic**: SIP calculation never changes, fully auditable.
3. **AI is Explainer**: Gemini only for explanations, not math.
4. **RAG Prevents Hallucination**: Explanation references retrieved docs, not generic knowledge.
5. **Fallback Works**: If Gemini fails, user gets static explanation (demo by unplugging internet or delaying).
6. **Audit Trail is Immutable**: Every action logged with timestamp, stored append-only.
7. **PDF is Complete**: Export includes disclaimer, audit reference, consent ID.

---

## Questions from Examiners (Likely) & Quick Answers

**Q: Why is math separate from AI?**
A: Because calculations must be 100% auditable and reproducible. If AI calculates wrong, the company is liable. AI for explanations is educational guidance, not advice.

**Q: What happens if Gemini is down?**
A: Demo the fallback—user sees pre-written explanation. No functionality lost.

**Q: How do you prevent hallucination?**
A: RAG ensures LLM only sees retrieved docs. No external knowledge. Answers are grounded in context.

**Q: Is the audit trail tamper-proof?**
A: PostgreSQL append-only + timestamps + immutable column constraint. In production, archive to S3.

**Q: Can users delete their data?**
A: Yes, but audit trail remains (for compliance). Deletion is logged as action=delete_user.

