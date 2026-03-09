# SmartBridge: Viva Voce Questions & Answers

**For**: B.Tech Examination Defense  
**Format**: 12 core questions covering architecture, RAG, compliance, math, and limitations

---

## 1. **Architecture & Design**

### Q1: Why separate the SIP calculation from the AI explanation?

**A**: 
SIP calculations are **deterministic financial math** (compound interest formula), which must be 100% auditable and reproducible. Delegating this to AI would make results non-deterministic and create liability if calculations are wrong. AI (Gemini) is used **only** for explanations—providing context and reasoning. This separation ensures correctness while improving QoL. It also aligns with regulatory guidance (SEBI) which accepts AI for explanations but not for financial advice or calculations.

---

### Q2: Describe the complete user journey from login to PDF export.

**A**: 
1. **Consent**: User accepts AI usage + audit logging (stored in `user_consent` table)
2. **Plan Creation**: Input demographics (age, income, risk profile); validated via Pydantic; stored in `investment_plans`
3. **Assumptions**: User sets expected return & inflation (checked against historical ranges, no AI)
4. **Calculate**: Deterministic SIP formula run; result stored in `calculation_results`
5. **Explain**: RAG retrieves relevant docs (~3) from vector DB; Gemini's prompted with user data + retrieved context; explanation streamed to UI
6. **Export PDF**: Backend renders PDF with plan, calc, explanation, disclaimer, audit timestamp; returned to user
7. **All actions logged** in `audit_events` table with immutable timestamp.

---

### Q3: What is the purpose of the RAG (Retrieval-Augmented Generation) pipeline?

**A**: 
RAG prevents LLM hallucination by grounding responses in retrieved documents. Flow: (1) User assumptions + calc results passed to vector DB query; (2) Retrieve top 3 matching docs (e.g., tax guides, risk primers); (3) Prompt includes only these docs, not open-ended knowledge; (4) Gemini forced to answer from context. If no docs match, fallback explanation is used. This ensures explanations are factually grounded, not invented.

---

## 2. **Hallucination Mitigation & Safety**

### Q4: How does your system prevent the LLM from making up financial advice?

**A**: 
**Four layers of protection**:
1. **No raw math in prompt**: We never send formulas to LLM; only final results
2. **RAG only**: Gemini only sees retrieved docs + user assumptions; no external knowledge
3. **Fallback mode**: If Gemini fails or times out (>5s), serve static explanation
4. **Streaming + review**: User sees explanation as it's generated; can stop if wrong

Example: If LLM tries to invent a "special SIP variant", context limit forces it to reference retrieved docs or hallucinate—but our validator rejects non-grounded claims before returning.

---

### Q5: What happens if the Gemini API is unavailable during a demo?

**A**: 
Graceful fallback is **built-in**. If API times out (>5s) or errors, user sees:
```
"Based on your moderate risk profile and 25-year horizon, 
a monthly SIP aligns with diversified equity allocation. 
Review our tax and risk guides in the PDF for details."
```
No functionality lost; user still gets full plan + fallback explanation + PDF export. Demo can showcase this by unplugging internet or artificially delaying Gemini.

---

## 3. **Compliance & Audit Design**

### Q6: Explain how your audit trail ensures regulatory compliance (DPDP Act, SEBI suitability).

**A**: 
**Audit Trail**:
- Every action (login, plan create, calculate, export) logged in `audit_events` table with immutable timestamp, IP, user-agent
- Appended-only (no deletions); timestamp constraint prevents backdating
- Stored 7 years per regulation

**Consent Flow**:
- User must accept AI usage + data logging before any action
- Consent ID stored; version tracked for updates
- If revoked, new consent required; old record immutable

**Suitability Check**:
- Risk profile collected + stored; can be audited
- Mismatch warnings issued (e.g., "Your assumption is aggressive; do you understand the risks?")

**Liability Mitigation**:
- PDF includes disclaimer: "Educational guidance, not financial advice"
- Consent reference in PDF: "User agreed to AI explanations on 2026-03-09"
- Regulator can subpoena audit trail; every step traceable

---

### Q7: How does your system handle DPDP Act 2023 requirements for user data?

**A**: 
**Data Principal Rights (DPDP)**:
1. **Consent**: ✓ Explicit opt-in before tracking
2. **Data Access**: User can request all stored data via `/api/v1/user/data` endpoint
3. **Data Deletion**: User can request deletion; action logged as `action=user_deletion` (immutable audit remains)
4. **Transparency**: Privacy policy explains AI usage, retention period (7 years), audit logging
5. **Grievance Redressal**: Contact email in app footer

**Storage**:
- PostgreSQL with role-based access (no admin can directly view user data)
- In production, add encryption at rest + column-level permissions

---

## 4. **Regulatory & Ethical**

### Q8: Why are you using Gemini (cloud API) instead of an on-prem model like Llama? What are the risks?

**A**: 
**Why Gemini**:
- Production-grade, minimal hallucination, fast response (~2s)
- Streaming support (better UX)
- For B.Tech scope, simple to integrate

**Risks** (acknowledged):
1. **Data Privacy**: Explanations sent to Google's servers (mitigated: user assumptions, not full context)
2. **Availability**: API down → fallback used (acceptable)
3. **Cost**: ~0.5–1¢ per explanation (acceptable at scale)

**Future**: Replace with Ollama (Llama 2) on-prem for full privacy control. Trade-off: 50% slower, needs GPU, but zero data egress.

---

### Q9: A regulator asks: "Why should we trust math you claim is deterministic?" How do you respond?

**A**: 
**Proof of Determinism**:
1. **Open Formula**: SIP formula is textbook (FV = P × [((1+r)^n - 1) / r]); reproducible
2. **No RNG**: Code has NO randomness; same inputs → same outputs always
3. **Audit Trail**: Every calc logged with inputs, formula used, result; regulator can re-run
4. **Test Suite**: Unit tests verify calc against known values (e.g., ₹100k SIP → ₹5M in 20 yrs with 8% return)
5. **Open Source**: Code available for inspection; no hidden logic

**Example**: 
```
Input: age=35, return=9%, inflation=5.5%, life_exp=85
Run 1: SIP = ₹26,545
Run 1000: SIP = ₹26,545  (identical)
```

---

## 5. **Technical Depth: SIP Math**

### Q10: Walk me through the SIP calculation formula. Why this formula and not others?

**A**: 
**SIP Formula (Future Value of Annuity)**:
```
FV = P × [((1 + r)^n - 1) / r] × (1 + r)

Where:
- P = Monthly payment (what we solve for)
- r = Monthly return rate (annual % / 12 / 100)
- n = Number of months
- FV = Target corpus
```

**Why this**:
- Standard finance formula (CFA, NISM curricula)
- Assumes consistent monthly deposits (SIP definition)
- Accounts for compounding
- Well-studied, no surprises

**Example Calculation**:
```
Target: ₹1.5 Cr, 25 years, 10.5% annual return
r = 0.105 / 12 / 100 = 0.00875
n = 25 × 12 = 300

Denominator = [((1.00875)^300 - 1) / 0.00875] × 1.00875
             = [9.97 / 0.00875] × 1.00875
             = 1139.4 × 1.00875
             = 1149.4

P = 1,50,00,000 / 1149.4 = ₹130,548 (if solving target = ₹1.5 Cr)
```

**Real Terms Inflation Adjustment**:
```
Real Corpus = Nominal Corpus / (1 + inflation)^years
            = 1.5Cr / (1.065)^25
            = ₹68.5 Lakh
```

---

### Q11: A user enters expected return = 15% (very optimistic). How does your system handle this outlier?

**A**: 
**Three-tier approach**:
1. **Validation (Backend)**: Check `15% ∈ historical range (8%-12%)`? → NO warning issued
2. **UI Warning**: Show "Historical equity returns: 8-12%, yours: 15%. If wrong, real corpus will be ₹X less"
3. **User Choice**: User sees warning but can proceed if they accept risk

**Code**:
```python
if expected_return > 0.12:
    warning = f"High historical average is 12%; you chose {expected_return*100}%. 
               If actual return is 9%, corpus shortfall: ₹{shortfall}"
    display_warning(warning)
else:
    proceed_with_calculation()
```

**Key**: System **warns but doesn't block**; user retains agency. Consent + assumption logged in audit trail.

---

## 6. **Limitations & Honest Assessment**

### Q12: What are the biggest limitations of your system? What would you build next?

**A**: 
**Current Limitations**:

1. **Single-user, single-plan**: Can't model family (spouse, kids) jointly. Workaround: separate plans, combine offline.
2. **Static market assumptions**: User inputs expected return; no real-time data. Next: integrate Bloomberg/Morningstar APIs.
3. **No portfolio optimization**: Gives SIP target, not asset allocation. Next: implement Modern Portfolio Theory (efficient frontier).
4. **Gemini dependency**: Explanation requires cloud API. Next: self-host Ollama (Llama 2) for privacy.
5. **Local PDF only**: No cloud archive. Next: S3 + email delivery.

**Future Roadmap (Post-B.Tech)**:

| Feature | Timeline | Impact |
|---------|----------|--------|
| Multi-person family planning | 3-6 mo | Align with real-world use case |
| On-prem Ollama integration | 6 mo | Eliminate API dependency, full privacy |
| Portfolio optimization (MPT) | 6-9 mo | Recommend equity:debt:gold + rebalancing |
| KYC integration (Aadhaar/PAN) | 9-12 mo | SEBI suitability compliance |
| Custodial trading (Zerodha API) | 9-12 mo | Execute actual SIP, not just plan |
| Tax-loss harvesting | 12+ mo | Optimize after-tax returns |

**Why Not Built Yet**:
- Limited scope (B.Tech submission)
- Budget/time constraints
- Regulatory complexity (KYC, custodial APIs require approvals)

---

## Bonus: Follow-Up Questions Examiners Might Ask

### Q: "Your audit table has no encryption. Isn't that a compliance risk?"

**A**: 
Fair point. For B.Tech simplicity, plaintext suffices. In production:
- Add column-level encryption for sensitive fields (IP, assumptions) using PGP
- Archive to S3 with server-side encryption + signature for immutability
- Implement role-based access: only compliance officer can view audit

---

### Q: "What if someone guesses a user's SIP amount by iterating over URLs?"

**A**: 
Good catch. Mitigations:
1. **Auth required**: Every endpoint demands JWT token; no unauthenticated access
2. **Rate limiting**: Max 10 API calls/min per user (prevents brute-force)
3. **Calc ID obfuscation**: Use UUID instead of sequential IDs (in production)

Current code: `calc_id=890` is sequential (fine for B.Tech, needs UUID in prod).

---

### Q: "Can a user claim they never consented to AI explanations?"

**A**: 
No. Timestamp + IP stored in `user_consent` table. User signed consent digitally (in production: e-signature + OTP). Audit trail proves: timestamp of consent, when explanation was used, IP matches.

---

### Q: "How do you ensure Gemini won't be trained on user data?"

**A**: 
Gemini API Terms: User data is NOT used for model training (enterprise agreement). However, for maximum privacy, fallback to Ollama removes this dependency entirely.

---

## Summary: 12 Questions → 12 Strong Answers

| Q | Topic | Strength |
|---|-------|----------|
| **Q1** | Math vs AI separation | Liability & regulatory |
| **Q2** | User journey | End-to-end flow |
| **Q3** | RAG purpose | Hallucination prevention |
| **Q4** | Safety layers | 4-tier approach |
| **Q5** | API failure | Graceful fallback |
| **Q6** | Audit compliance | DPDP + SEBI alignment |
| **Q7** | DPDP Act specifics | User rights + opt-out |
| **Q8** | Gemini vs Llama | Honest trade-offs |
| **Q9** | Math determinism | Proof via formula + tests |
| **Q10** | SIP formula deep-dive | Textbook + example calc |
| **Q11** | Outlier handling | Warning + user agency |
| **Q12** | Limitations | Roadmap + honest gaps |

---

## Practice Tips

1. **Know the formula cold**: Be able to derive & explain SIP FV formula from first principles (annuity math).
2. **Explain RAG without jargon**: "We give the AI only relevant documents; it can't invent."
3. **Show logs during defense**: Pull audit tables from DB live; prove every action is logged.
4. **Admit limitations**: Examiners respect honesty. Say "Feature X not in scope; here's the 6-month plan."
5. **Reference regulations**: DPDP Act, SEBI suitability rules by name; shows domain knowledge.
6. **Practice the demo cold**: Run `docker-compose up`, create plan, export PDF in under 5 minutes.

---

## Final Confidence Checklist

- [ ] Can explain math separation (Q1, Q9, Q10) without notes?
- [ ] Can demo a full user journey in <10 min with zero errors?
- [ ] Can describe audit trail & compliance design (Q6, Q7)?
- [ ] Can answer "What if Gemini is down?" with confidence (Q5)?
- [ ] Can list 3+ limitations & roadmap honestly (Q12)?
- [ ] Know regulatory context (DPDP, SEBI) for your region?

If you check all 6 → **ready for viva defense**. 🎯

