# Test Plan: Salik Tariff & Violation Modules

**Version:** 1.0  
**Date:** 2026-05-06  
**QA Lead:** Senior QA Team  
**Target Modules:** `salik/tariff.py`, `salik/violations.py`

---

## 1. In-Scope Files

### Primary Test Targets
- [`salik/tariff.py`](../salik/tariff.py) - Tariff calculation logic with time-window rules
- [`salik/violations.py`](../salik/violations.py) - Fine escalation and annual cap enforcement

### Supporting Files (Integration Context)
- [`salik/system.py`](../salik/system.py) - Orchestration layer that invokes tariff and violation logic
- [`salik/models.py`](../salik/models.py) - Domain models (Account, Transaction, Vehicle)
- [`salik/gates.py`](../salik/gates.py) - Gate enumeration (minimal risk)

### Existing Test Files
- [`tests/test_tariff.py`](../tests/test_tariff.py) - Current tariff tests (baseline coverage)
- [`tests/test_violations.py`](../tests/test_violations.py) - Current violation tests (baseline coverage)
- [`tests/test_system.py`](../tests/test_system.py) - Integration tests

---

## 2. Risk-Ranked Test Scenarios

### 2.1 Tariff Module (`salik/tariff.py`)

#### **HIGH RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| T-H1 | **Free window boundary at 01:00:00** | Exact boundary condition; off-by-one errors could charge users incorrectly |
| T-H2 | **Free window boundary at 05:59:59** | Upper boundary of free window; critical for revenue accuracy |
| T-H3 | **Free window boundary at 06:00:00** | Transition from free to peak/off-peak; financial impact if miscalculated |
| T-H4 | **Peak window start at 06:00:00 (weekday)** | Morning rush start; high transaction volume period |
| T-H5 | **Peak window end at 09:59:59 (weekday)** | Last second of morning peak; boundary precision critical |
| T-H6 | **Peak window transition at 10:00:00 (weekday)** | AED 6→4 transition; revenue impact if wrong |
| T-H7 | **Peak window start at 16:00:00 (weekday)** | Evening rush start; high volume period |
| T-H8 | **Peak window end at 19:59:59 (weekday)** | Last second of evening peak |
| T-H9 | **Peak window transition at 20:00:00 (weekday)** | AED 6→4 transition; revenue impact |
| T-H10 | **Saturday transitions (weekday=5)** | Saturday is off-peak all day; boundary between weekday and Sunday rules |
| T-H11 | **Sunday all-day free (weekday=6)** | Entire day should be free; revenue loss if broken |
| T-H12 | **Midnight crossing (23:59:59 → 00:00:00)** | Day boundary; potential timezone or date arithmetic issues |
| T-H13 | **Leap second handling (if applicable)** | Edge case for datetime precision |

#### **MEDIUM RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| T-M1 | **Off-peak midday (10:00-15:59)** | Standard case but needs verification |
| T-M2 | **Off-peak late evening (20:00-00:59)** | Standard case; lower volume period |
| T-M3 | **Friday off-peak (weekday=4)** | Last weekday; ensure peak rules still apply |
| T-M4 | **Monday morning peak (weekday=0)** | First weekday; verify week start logic |
| T-M5 | **Decimal precision for toll amounts** | Ensure no floating-point errors (AED 4.00, 6.00) |
| T-M6 | **Constants validation** | Verify PEAK_TOLL, OFFPEAK_TOLL, FREE values are correct |

#### **LOW RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| T-L1 | **Return type is Decimal** | Type safety; already tested but good to maintain |
| T-L2 | **Function accepts datetime parameter** | Input validation; straightforward |
| T-L3 | **Constants are immutable** | Code quality check |

---

### 2.2 Violation Module (`salik/violations.py`)

#### **HIGH RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| V-H1 | **First violation: AED 100** | Entry point to fine schedule; must be exact |
| V-H2 | **Second violation: AED 200** | Escalation step 1; financial accuracy critical |
| V-H3 | **Third violation: AED 400** | Escalation step 2; highest tier entry |
| V-H4 | **Fourth+ violations: AED 400 (capped)** | Top-tier persistence; ensure no further escalation |
| V-H5 | **Annual cap at AED 9,999.99** | One cent below cap; precision boundary |
| V-H6 | **Annual cap at AED 10,000.00** | Exact cap; must stop charging |
| V-H7 | **Annual cap exceeded (e.g., 9,950 + 400)** | Partial fine scenario; must clamp to remaining allowance (50) |
| V-H8 | **Annual cap already reached** | Zero fine when cap hit; prevent overcharging |
| V-H9 | **Multiple plates isolation** | Ensure plate A's violations don't affect plate B |
| V-H10 | **Concurrent violations for same plate** | Race condition potential if system scales |
| V-H11 | **Registry state persistence** | Counts and totals must survive across operations |
| V-H12 | **Negative fine prevention** | When cap is reached, fine must be 0, not negative |

#### **MEDIUM RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| V-M1 | **10th violation (well past escalation)** | Verify top-tier stability |
| V-M2 | **50th violation (stress test)** | Ensure no integer overflow or unexpected behavior |
| V-M3 | **Annual cap with exact schedule sum** | E.g., 100+200+400+...+400 = 10,000 |
| V-M4 | **Plate with zero violations** | Initial state; should return 0 for total and count |
| V-M5 | **Decimal precision in totals** | Ensure no rounding errors accumulate |
| V-M6 | **Empty plate string handling** | Edge case for plate identifier |
| V-M7 | **Very long plate string** | Stress test for dictionary key handling |

#### **LOW RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| V-L1 | **Return type is Decimal** | Type safety; straightforward |
| V-L2 | **FINE_SCHEDULE is list of 3 Decimals** | Data structure validation |
| V-L3 | **ANNUAL_FINE_CAP is Decimal** | Constant validation |
| V-L4 | **Registry initialization** | Constructor creates empty dicts |

---

### 2.3 Security & Vulnerability Testing

#### **HIGH RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| S-H1 | **Malicious plate string injection (SQL-like patterns)** | Prevent injection attacks via plate identifiers (e.g., "'; DROP TABLE--") |
| S-H2 | **XSS patterns in plate strings** | Prevent script injection (e.g., "<script>alert('xss')</script>") |
| S-H3 | **Extremely long plate strings (>10,000 chars)** | DoS prevention; memory exhaustion attack |
| S-H4 | **Unicode/special characters in plate strings** | Prevent encoding exploits (e.g., null bytes, control chars) |
| S-H5 | **Negative datetime manipulation** | Attempt to pass negative timestamps or dates before epoch |
| S-H6 | **Future datetime exploitation (year 9999+)** | Prevent integer overflow or logic bypass with far-future dates |
| S-H7 | **Direct registry state manipulation** | Attempt to modify `_counts` or `_totals` dictionaries directly |
| S-H8 | **Annual cap bypass via negative fines** | Ensure fine calculation never produces negative values |
| S-H9 | **Integer overflow in violation counts** | Test with extremely high violation counts (>2^31) |
| S-H10 | **Decimal overflow in fine totals** | Test with values exceeding Decimal precision limits |
| S-H11 | **Race condition in concurrent violations** | Multiple simultaneous violations for same plate |
| S-H12 | **Time manipulation attacks** | Attempt to exploit timezone or DST transitions |

#### **MEDIUM RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| S-M1 | **Empty string plate identifier** | Edge case for dictionary key handling |
| S-M2 | **Whitespace-only plate strings** | Input sanitization check |
| S-M3 | **Case sensitivity exploitation** | Ensure "ABC-123" and "abc-123" are treated consistently |
| S-M4 | **Duplicate plate registration attempts** | Verify system prevents double-linking |
| S-M5 | **None/null datetime values** | Type safety for required parameters |
| S-M6 | **Invalid datetime objects** | Malformed datetime handling |
| S-M7 | **Decimal precision manipulation** | Attempt to exploit rounding with extreme precision |

#### **LOW RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| S-L1 | **Type confusion (string vs Decimal)** | Type safety validation |
| S-L2 | **Boolean coercion in conditions** | Ensure explicit comparisons |
| S-L3 | **Dictionary key collision** | Hash collision resistance |

---

### 2.4 Integration Scenarios (Tariff + Violation + System)

#### **HIGH RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| I-H1 | **Insufficient balance during peak → fine escalation** | Combines tariff calculation with violation recording |
| I-H2 | **Insufficient balance during free window → no fine** | Free pass should not trigger violation |
| I-H3 | **Unregistered plate during peak → first fine (100)** | System must invoke violation registry correctly |
| I-H4 | **Repeated insufficient balance → escalating fines** | Multi-step escalation through system layer |
| I-H5 | **Annual cap reached via system transactions** | End-to-end cap enforcement |
| I-H6 | **Account fine tracking vs. registry tracking** | Ensure Account.fines_this_year matches ViolationRegistry |

#### **MEDIUM RISK** Scenarios

| ID | Scenario | Rationale |
|----|----------|-----------|
| I-M1 | **Multiple vehicles on one account** | Ensure violations are per-plate, not per-account |
| I-M2 | **Transaction ledger accuracy** | All toll and fine transactions recorded correctly |
| I-M3 | **Balance deduction during off-peak** | Standard flow verification |

---

## 3. Coverage Targets

### 3.1 Statement Coverage
- **Target:** ≥95% for `salik/tariff.py` and `salik/violations.py`
- **Rationale:** Financial logic requires near-complete coverage; 100% may be impractical due to defensive code

### 3.2 Branch Coverage
- **Target:** ≥90% for both modules
- **Rationale:** All conditional paths (time windows, escalation tiers, cap logic) must be tested

### 3.3 Boundary Coverage
- **Target:** 100% for all time boundaries and fine thresholds
- **Rationale:** Off-by-one errors are the highest risk in this domain

### 3.4 Security Test Coverage
- **Target:** 100% for all HIGH-risk security scenarios (S-H1 through S-H12)
- **Rationale:** Financial systems must be resilient against injection, manipulation, and DoS attacks

### 3.5 Current Coverage Gaps (Based on Existing Tests)

#### `salik/tariff.py` Gaps:
- ❌ Exact boundary at 01:00:00 (free window start)
- ❌ Exact boundary at 05:59:59 (free window end)
- ❌ Exact boundary at 06:00:00 (free→peak transition)
- ❌ Exact boundary at 16:00:00 (off-peak→peak transition)
- ❌ Exact boundary at 19:59:59 (peak end)
- ❌ Exact boundary at 20:00:00 (peak→off-peak transition)
- ❌ Saturday (weekday=5) behavior
- ❌ Midnight crossing scenarios
- ⚠️ Only one peak boundary tested (10:00:00)

#### `salik/violations.py` Gaps:
- ❌ Exact annual cap boundary (9,999.99 vs 10,000.00)
- ❌ Partial fine when approaching cap (e.g., 9,950 + 400 → 50)
- ❌ Zero fine when cap already reached
- ❌ Negative fine prevention logic
- ❌ High violation count (10+, 50+)
- ❌ Edge cases for plate identifiers (empty, very long)
- ⚠️ Only basic escalation tested (1st, 2nd, 3rd, 4th)

---

## 4. Out-of-Scope Items

### 4.1 Explicitly Excluded
- **Performance/Load Testing:** Not in scope for this test plan; requires separate performance test suite
- **Authentication/Authorization Security:** User authentication and role-based access control are handled at system boundary, not in these modules
- **Encryption/Data-at-Rest Security:** Data encryption is handled by infrastructure layer
- **UI/UX Testing:** No user interface in these modules
- **Database Testing:** Modules use in-memory data structures; persistence layer is separate
- **Network/API Testing:** No external API calls in these modules
- **Concurrency/Threading:** Single-threaded operation assumed; concurrent access requires separate plan
- **Timezone Handling:** Assumes all timestamps are in Dubai timezone (UTC+4); timezone conversion is out of scope
- **Historical Data Migration:** Not applicable to new system
- **Regulatory Compliance Audit:** Legal/compliance review is separate from functional testing

### 4.2 Deferred to Future Phases
- **Annual Reset Logic:** How violation counts/totals reset at year boundary (not implemented in current code)
- **Fine Payment Processing:** Payment gateway integration
- **Notification System:** Low balance alerts, fine notifications
- **Reporting/Analytics:** Dashboard and reporting features
- **Multi-Currency Support:** Currently AED only
- **Localization/i18n:** Currently English only

### 4.3 Dependencies (Tested Separately)
- **`salik/gates.py`:** Simple enum; minimal risk; tested via integration tests
- **`salik/models.py`:** Data classes; tested via system tests
- **`salik/cli.py`:** Command-line interface; separate test plan

---

## 5. Test Execution Strategy

### 5.1 Test Phases
1. **Unit Tests:** Isolated testing of `toll_for()` and `ViolationRegistry` methods
2. **Integration Tests:** System-level tests combining tariff + violation + account logic
3. **Boundary Tests:** Focused suite for all time and threshold boundaries
4. **Regression Tests:** Re-run after any code changes

### 5.2 Test Data Requirements
- **Date/Time Fixtures:** Pre-defined datetime objects for each boundary condition
- **Plate Identifiers:** Valid Dubai plate formats (e.g., "DXB-A-12345")
- **Decimal Precision:** All monetary values as `Decimal` to avoid floating-point errors

### 5.3 Tools & Frameworks
- **pytest:** Primary test framework (already configured in `pyproject.toml`)
- **pytest-cov:** Coverage measurement
- **hypothesis:** Property-based testing for boundary exploration (recommended)

### 5.4 Success Criteria
- ✅ All HIGH risk scenarios pass (including security tests)
- ✅ Statement coverage ≥95%
- ✅ Branch coverage ≥90%
- ✅ Zero critical defects in tariff time-window logic
- ✅ Zero critical defects in fine escalation and annual cap logic
- ✅ All boundary conditions explicitly tested
- ✅ All HIGH-risk security vulnerabilities addressed (S-H1 through S-H12)

---

## 6. Risk Mitigation

### 6.1 Identified Risks
1. **Off-by-One Errors in Time Boundaries:** Mitigated by explicit boundary tests (T-H1 through T-H13)
2. **Decimal Precision Loss:** Mitigated by using `Decimal` type throughout
3. **Annual Cap Bypass:** Mitigated by comprehensive cap scenarios (V-H5 through V-H8)
4. **Escalation Logic Errors:** Mitigated by testing all tiers and transitions (V-H1 through V-H4)
5. **Integration Mismatches:** Mitigated by integration test suite (I-H1 through I-H6)
6. **Injection Attacks:** Mitigated by input validation tests (S-H1, S-H2, S-H4)
7. **DoS via Resource Exhaustion:** Mitigated by boundary tests for extreme inputs (S-H3, S-H9, S-H10)
8. **State Manipulation:** Mitigated by encapsulation tests (S-H7, S-H8)
9. **Time-based Exploits:** Mitigated by datetime edge case tests (S-H5, S-H6, S-H12)

### 6.2 Contingency Plans
- If coverage targets not met: Identify untested branches and add specific tests
- If boundary tests fail: Review time comparison logic (`<=` vs `<`) in `toll_for()`
- If cap logic fails: Review arithmetic in `ViolationRegistry.record()`

---

## 7. Test Deliverables

### 7.1 Test Artifacts
- [ ] Expanded `tests/test_tariff.py` with boundary scenarios
- [ ] Expanded `tests/test_violations.py` with cap and escalation scenarios
- [ ] New `tests/test_integration_tariff_violations.py` for integration scenarios
- [ ] New `tests/test_security_vulnerabilities.py` for security/vulnerability scenarios
- [ ] Coverage report (HTML format)
- [ ] Security test execution report
- [ ] Test execution summary report

### 7.2 Documentation
- [x] This test plan document
- [ ] Test case specifications (detailed steps for each scenario)
- [ ] Defect log (if issues found)
- [ ] Vulnerability assessment report
- [ ] Coverage analysis report

---

## 8. Appendix

### 8.1 Tariff Time Windows (Reference)
```python
FREE_WINDOW = (time(1, 0), time(6, 0))          # 01:00-06:00 daily
PEAK_WINDOWS = [
    (time(6, 0), time(10, 0)),                  # 06:00-10:00 weekdays
    (time(16, 0), time(20, 0)),                 # 16:00-20:00 weekdays
]
# Sunday (weekday=6) is free all day
# Saturday (weekday=5) is off-peak all day
```

### 8.2 Fine Schedule (Reference)
```python
FINE_SCHEDULE = [Decimal("100"), Decimal("200"), Decimal("400")]
ANNUAL_FINE_CAP = Decimal("10000")
```

### 8.3 Toll Rates (Reference)
```python
PEAK_TOLL = Decimal("6.00")
OFFPEAK_TOLL = Decimal("4.00")
FREE = Decimal("0.00")
```

---

**Document Status:** Draft for Review  
**Next Steps:** Review with development team, obtain approval, proceed to test implementation phase