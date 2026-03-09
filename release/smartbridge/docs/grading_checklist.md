# SmartBridge: Grading Checklist

Maps project deliverables to typical B.Tech evaluation rubric items.

---

## Rubric Categories & Scoring (100 points total)

### A. **Functionality & Features** (25 points)

- [ ] **10 pts**: SIP calculation works correctly (deterministic, no randomness)
  - **Evidence**: Demo shows consistent results; unit tests pass (`tests/test_calculator.py`)
  - **Acceptance**: Monthly SIP amount correct per FV formula for given inputs

- [ ] **8 pts**: AI explanation generation with RAG (Gemini API)
  - **Evidence**: Streamlit shows streaming explanation; audit table records `action=explain_generated`
  - **Acceptance**: Explanation text visible in PDF export; fallback triggered if API down

- [ ] **5 pts**: PDF export with full metadata (plan, calc, explanation, disclaimer)
  - **Evidence**: `POST /api/v1/export` returns 200, PDF file generated with correct content
  - **Acceptance**: PDF includes SIP amount, inflation adjustment, disclaimer, audit reference

- [ ] **2 pts**: User authentication & session management
  - **Evidence**: Login endpoint works; JWT tokens validated on all protected routes
  - **Acceptance**: Unauthenticated requests return 401/403

### B. **Code Quality & Architecture** (20 points)

- [ ] **7 pts**: Clean architecture (separation of concerns: API, business logic, data)
  - **Evidence**: 
    - `backend/app.py` contains only FastAPI routing
    - `backend/calculator.py` contains SIP math (no API calls)
    - `backend/rag_pipeline.py` handles Gemini integration (isolated)
  - **Acceptance**: Each module <200 lines, single responsibility

- [ ] **5 pts**: Error handling & validation (Pydantic schemas, try-except blocks)
  - **Evidence**: 
    - `POST /api/v1/plans` rejects invalid age/income
    - Gemini timeout caught; fallback explanation served
    - Database errors logged to audit trail
  - **Acceptance**: No unhandled exceptions; all errors logged

- [ ] **5 pts**: Code conventions (naming, docstrings, type hints)
  - **Evidence**: 
    - Functions have docstrings
    - Variables follow snake_case
    - Type hints on all function signatures
  - **Acceptance**: `mypy --strict` passes without errors

- [ ] **3 pts**: DRY (no code duplication)
  - **Evidence**: Fallback explanation in single place; SIP formula called once per calculation
  - **Acceptance**: Find-and-replace confirms <2 copies of any logic

### C. **Testing & Verification** (15 points)

- [ ] **6 pts**: Unit tests for core logic (SIP formula, validators)
  - **Evidence**: `pytest tests/test_calculator.py -v` passes all
  - **Acceptance**: 
    ```bash
    tests/test_calculator.py::test_sip_basic PASSED
    tests/test_calculator.py::test_inflation_adjustment PASSED
    tests/test_calculator.py::test_invalid_inputs PASSED
    ```

- [ ] **5 pts**: Integration tests (API endpoints, database)
  - **Evidence**: `pytest tests/test_api.py -v` passes
  - **Acceptance**:
    ```bash
    tests/test_api.py::test_create_plan POST /api/v1/plans PASSED
    tests/test_api.py::test_calculate POST /api/v1/calculate PASSED
    tests/test_api.py::test_export POST /api/v1/export PASSED
    ```

- [ ] **2 pts**: End-to-end smoke tests (demo script execution)
  - **Evidence**: `./scripts/smoke_test.sh --environment local` returns 0
  - **Acceptance**: All 8 demo steps complete without error

- [ ] **2 pts**: Test coverage (>70% of codebase)
  - **Evidence**: `pytest --cov=backend tests/` shows coverage
  - **Acceptance**: Coverage report ≥70%

### D. **Documentation** (15 points)

- [ ] **5 pts**: Technical specification (architecture, data flow, API)
  - **Evidence**: `docs/tech_spec.md` (6–8 pages equivalent)
  - **Acceptance Criteria**:
    - ✓ Mermaid architecture diagram
    - ✓ Data flow descriptions (user journey)
    - ✓ Database schemas (CREATE TABLE)
    - ✓ API endpoints (POST/GET requests & responses)
    - ✓ Prompt templates (conservative + RAG-only)
    - ✓ SIP formula with example calculation

- [ ] **4 pts**: Demo script (step-by-step with expected outputs)
  - **Evidence**: `docs/demo_script.md` with timing cues
  - **Acceptance Criteria**:
    - ✓ 8 steps (consent → PDF export)
    - ✓ Expected UI state for each step
    - ✓ Backend API calls shown (method, endpoint, request/response)
    - ✓ Audit log verification included
    - ✓ Timing: 00:00, 00:30, 02:00, etc.

- [ ] **3 pts**: Viva preparation (Q&A covering architecture, compliance, limitations)
  - **Evidence**: `docs/viva_questions.md`
  - **Acceptance Criteria**:
    - ✓ 12 questions with 2–4 line answers
    - ✓ Covers: architecture, math, RAG, compliance, limitations
    - ✓ Includes answers to likely follow-ups

- [ ] **2 pts**: API documentation (endpoint reference, curl examples)
  - **Evidence**: `docs/tech_spec.md` section 4 (API Endpoints)
  - **Acceptance Criteria**:
    - ✓ All endpoints listed (auth, consent, plan CRUD, calculate, explain, export)
    - ✓ Sample request/response for each
    - ✓ Status codes documented

- [ ] **1 pt**: README.md with setup instructions
  - **Evidence**: `README.md` or `docs/QUICKSTART.md`
  - **Acceptance**: User can `docker-compose up && streamlit run ...` and see UI in <2 min

### E. **Compliance & Security** (12 points)

- [ ] **4 pts**: Audit logging (immutable append-only logs)
  - **Evidence**: `audit_events` table populated; demo shows audit trail query
  - **Acceptance Criteria**:
    - ✓ Every action logged (consent, plan, calculate, export)
    - ✓ Timestamp + IP + user_agent stored
    - ✓ Audit table constraint prevents deletions/updates

- [ ] **3 pts**: User consent management
  - **Evidence**: `user_consent` table; consent required before tracking
  - **Acceptance Criteria**:
    - ✓ Consent dialog on first login
    - ✓ Version tracking (consent_version column)
    - ✓ User can view & revoke consent via `/api/v1/user/consent`

- [ ] **3 pts**: Input validation & sanitization
  - **Evidence**: Pydantic schemas + SQL injection tests
  - **Acceptance Criteria**:
    - ✓ All user inputs validated (age, income ranges)
    - ✓ Special chars escaped (e.g., "'; DROP TABLE--" rejected)
    - ✓ Invalid inputs return 400 Bad Request with clear message

- [ ] **2 pts**: Privacy & data protection (DPDP Act 2023 aligned)
  - **Evidence**: Privacy policy in docs; data access endpoint
  - **Acceptance Criteria**:
    - ✓ Privacy policy document (in `docs/PRIVACY.md` or similar)
    - ✓ User can request export of their data
    - ✓ User can request deletion (immutable audit trail remains)

### F. **Deployment & Packaging** (8 points)

- [ ] **5 pts**: Reproducible release.zip (code + docs + sample data)
  - **Evidence**: `./scripts/package_release.sh` generates zip
  - **Acceptance Criteria**:
    - ✓ Zip contains full source (no secrets)
    - ✓ Includes sample data (10-20 synthetic plans)
    - ✓ Includes all docs (tech_spec, demo, viva)
    - ✓ Includes `instructions.txt` at root
    - ✓ Can unzip & run per demo script in <10 min on fresh machine

- [ ] **2 pts**: Docker support (docker-compose.prod.yml for local testing)
  - **Evidence**: `docker-compose -f docker-compose.prod.yml up`
  - **Acceptance**: All services start; health checks pass

- [ ] **1 pt**: CI/CD pipeline (GitHub Actions or similar)
  - **Evidence**: `.github/workflows/test.yml` runs on push
  - **Acceptance**: Tests + build pass before merge

### G. **Presentation & Communication** (5 points)

- [ ] **3 pts**: Clear explanation of design choices (README, tech spec)
  - **Evidence**: 
    - Why math is separate from AI? → Listed clearly in `docs/tech_spec.md` section 1 & 3
    - Why Gemini + RAG? → Listed in section 3
    - Why PostgreSQL? → Listed in section 2
  - **Acceptance**: Each major choice has 2–3 line rationale

- [ ] **2 pts**: Demo readiness (practiced flow, handles common issues)
  - **Evidence**: Demo script runs cleanly; fallback shown if Gemini unavailable
  - **Acceptance**: No stuck screens; user sees real-time progress

---

## Grading Formula

```
Total Score = A + B + C + D + E + F + G
           = 25 + 20 + 15 + 15 + 12 + 8 + 5
           = 100 points
```

### Grade Mapping (Typical)
- **90–100**: Excellent (A)
- **80–89**: Very Good (B)
- **70–79**: Good (C)
- **60–69**: Satisfactory (D)
- **<60**: Needs Improvement (F)

---

## Pre-Submission Checklist

Run these commands to verify all grading criteria:

### A. Functionality
```bash
# 1. Test SIP calculation
python -c "from backend.calculator import sip_amount; print(sip_amount(1500000, 25, 0.095, 0.055))"
# Expected: ~26545 (matches demo)

# 2. Run demo locally
docker-compose -f docker-compose.prod.yml up &
streamlit run frontend/streamlit_app.py &
# Navigate browser; complete all 8 steps

# 3. Verify export
ls -lh smartbridge_plan_*.pdf
# Expected: 1+ PDF file(s) >100KB
```

### B. Code Quality
```bash
# 1. Type check
mypy backend/ --strict
# Expected: no errors

# 2. Lint
flake8 backend/ tests/
# Expected: <5 style warnings

# 3. Format
black --check backend/
# Expected: no reformatting needed
```

### C. Testing
```bash
# 1. Unit tests
pytest tests/test_calculator.py -v
# Expected: all tests PASSED

# 2. Integration tests
pytest tests/test_api.py -v
# Expected: all tests PASSED

# 3. Coverage
pytest --cov=backend tests/ --cov-report=term-missing
# Expected: coverage >=70%

# 4. Smoke test
./scripts/smoke_test.sh --environment local
# Expected: exit code 0
```

### D. Documentation
```bash
# 1. Check file existence
ls -l docs/tech_spec.md docs/demo_script.md docs/viva_questions.md
# Expected: 3 files, size >10KB each

# 2. Verify Mermaid diagram
grep -q "mermaid" docs/tech_spec.md
# Expected: no output (command succeeds)

# 3. Count words in tech_spec
wc -w docs/tech_spec.md
# Expected: >3000 words (roughly 6–8 pages)
```

### E. Compliance
```bash
# 1. Check audit table
psql $DATABASE_URL -c "SELECT COUNT(*) FROM audit_events;"
# Expected: >0 rows (demo populated it)

# 2. Check consent table
psql $DATABASE_URL -c "SELECT COUNT(*) FROM user_consent;"
# Expected: >0 rows

# 3. Verify immutability
psql $DATABASE_URL -c "ALTER TABLE audit_events UPDATE timestamp; " 2>&1 | grep ERROR
# Expected: ERROR (good; table is immutable)
```

### F. Packaging
```bash
# 1. Build release
./scripts/package_release.sh --version 1.0.0
# Expected: release.zip created

# 2. Verify contents
unzip -l release.zip | head -20
# Expected: code, docs, data, instructions.txt

# 3. Test extraction
mkdir /tmp/test_release && cd /tmp/test_release
unzip ~/smartbridge/release.zip
cat instructions.txt
# Expected: clear setup steps
```

### G. Presentation
```bash
# 1. Verify README exists
cat README.md | head -20
# Expected: clear problem statement + feature list

# 2. Run demo script
bash docs/demo_script.md  # (pseudocode; manual run)
# Expected: matches expected outputs
```

---

## Examiner's Likely Questions & Responses

### "Why didn't you integrate with real market data APIs?"
**Response**: Out of scope for B.Tech. Roadmap (section in `docs/tech_spec.md`) includes Bloomberg/Yahoo integration for production. Cost + regulatory complexity deferred.

### "Your audit table uses plaintext passwords. Isn't that a risk?"
**Response**: 
- B.Tech simplicity (no passwords hashed yet). 
- In production, implement bcrypt + column-level encryption
- Mentioned in `docs/tech_spec.md` section 8.3

### "Can you prove the SIP calculation is deterministic?"
**Response**: 
- Show `test_calculator.py`: same inputs → same outputs (run 100 times)
- Formula from CFA/NISM textbooks (reproducible)
- Audit log shows every calc with inputs + output

### "How does your system prevent users from exporting others' data?"
**Response**: 
- All endpoints require JWT authentication
- Backend validates user_id in token matches request
- Audit log records every export (with user_id + IP)

---

## Sign-Off

**All checklist items completed**: ✓  
**Total points achieved**: ___/100  
**Examiner**: _________________  
**Date**: _________________  

