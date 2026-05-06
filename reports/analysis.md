# Test Failure Analysis Report

**Date:** 2026-05-06  
**Test Run:** pytest with coverage  
**Total Tests:** 50 | **Passed:** 45 | **Failed:** 5 | **Skipped:** 0

---

## Summary Table

| Defect ID | Symptoms | Severity | Module |
|-----------|----------|----------|--------|
| DEF-001 | 5 test failures (Saturday/Sunday weekday logic inverted) | **Critical** | `salik/tariff.py` |

---

## Defect 1: Saturday/Sunday Weekday Check Inverted

### Root Cause Class
**logic-bug** — Incorrect weekday constant in conditional statement

### Severity: Critical

**Justification (Toll Revenue + Driver Fairness):**

**Revenue Impact:**
- **Saturday drivers:** Currently charged AED 0 (free) instead of AED 4-6 → **100% revenue loss** on Saturdays
- **Sunday drivers:** Currently charged AED 4-6 instead of AED 0 (free) → **Unfair overcharging** on Sundays
- **Financial exposure:** Cannot be quantified from this analysis — requires production traffic data. Loss structure: uncollected Saturday tolls + refund liability for incorrectly charged Sunday tolls.

**Driver Fairness:**
- **Saturday drivers:** Receive unintended free passes (benefit but creates precedent/expectation issues)
- **Sunday drivers:** Wrongly charged for what should be a free day (direct financial harm + reputational damage)
- **Legal/Regulatory Risk:** Violates published RTA tariff schedule; potential refunds, penalties, and loss of public trust

**Operational Impact:**
- Affects 2 out of 7 days (28.6% of the week)
- High-visibility defect (weekend traffic patterns are well-known to drivers)

### Symptoms

All 5 failures stem from the same root cause (line 30 in `salik/tariff.py`):

1. **tests/test_generated_tariff.py:43** — `test_saturday_is_offpeak_all_day`
   - **Scenario ID:** T-H10
   - **Expected:** Saturday (weekday=5) should return OFFPEAK_TOLL (AED 4.00)
   - **Actual:** Returns FREE (AED 0.00)
   - **Assertion:** `assert toll_for(SAT.replace(hour=8)) == OFFPEAK_TOLL`

2. **tests/test_generated_tariff.py:49** — `test_sunday_free_during_peak_hours`
   - **Scenario ID:** T-H11
   - **Expected:** Sunday (weekday=6) should return FREE (AED 0.00) even during peak hours
   - **Actual:** Returns OFFPEAK_TOLL (AED 4.00)
   - **Assertion:** `assert toll_for(SUN.replace(hour=7)) == FREE`

3. **tests/test_generated_tariff.py:76** — `test_weekday_rules[5-7-expected5]`
   - **Scenario ID:** T-H10 (parametrized)
   - **Expected:** Saturday at 07:00 should return OFFPEAK_TOLL (AED 4.00)
   - **Actual:** Returns FREE (AED 0.00)
   - **Assertion:** `assert toll_for(dt) == expected` where `dt = 2026-05-09 07:00` (Saturday)

4. **tests/test_generated_tariff.py:76** — `test_weekday_rules[6-7-expected6]`
   - **Scenario ID:** T-H11 (parametrized)
   - **Expected:** Sunday at 07:00 should return FREE (AED 0.00)
   - **Actual:** Returns OFFPEAK_TOLL (AED 4.00)
   - **Assertion:** `assert toll_for(dt) == expected` where `dt = 2026-05-10 07:00` (Sunday)

5. **tests/test_tariff.py:18** — `test_sunday_is_free_all_day`
   - **Scenario ID:** (existing test, pre-dates test plan)
   - **Expected:** Sunday at 08:00 and 18:00 should return 0 (free)
   - **Actual:** Returns Decimal('4.00')
   - **Assertion:** `assert toll_for(SUN.replace(hour=8)) == 0`

### Suggested Fix

**File:** `salik/tariff.py`  
**Line:** 30

```diff
--- a/salik/tariff.py
+++ b/salik/tariff.py
@@ -27,7 +27,7 @@ def toll_for(when: datetime) -> Decimal:
     if FREE_WINDOW[0] <= t < FREE_WINDOW[1]:
         return FREE
     # Sunday is a free day. Python: Monday=0 … Sunday=6.
-    if when.weekday() == 5:
+    if when.weekday() == 6:
         return FREE
     if when.weekday() < 5:
         for start, end in PEAK_WINDOWS:
```

**Explanation:**
- Python's `datetime.weekday()` returns: Monday=0, Tuesday=1, ..., Saturday=5, **Sunday=6**
- The bug changed the check from `== 6` (Sunday) to `== 5` (Saturday)
- This causes Saturday to be treated as the free day instead of Sunday

### Coverage Impact

**Lines Exercised by Failing Tests:**

From `reports/coverage.xml`, the defect is in `salik/tariff.py`:

- **Line 30:** `if when.weekday() == 5:` (branch condition)
  - Coverage: 100% (both branches exercised)
  - **Branch 1 (True):** Exercised by Saturday tests (incorrectly returns FREE)
  - **Branch 2 (False):** Exercised by all non-Saturday tests

**Branch Coverage Analysis:**
- The failing tests exercise **line 30, branch true** (when weekday == 5, i.e., Saturday)
- This branch is now incorrectly returning FREE instead of falling through to off-peak logic
- The correct Sunday check (weekday == 6) is never reached, causing Sunday to fall through to off-peak/peak logic

**Coverage Metrics (from coverage.xml):**
- `salik/tariff.py`: 100% line coverage, 100% branch coverage
- **Note:** High coverage does NOT guarantee correctness — all branches are exercised, but the logic is wrong

**Lines/Branches Affected:**
- **Line 27:** Free window check (not affected, still works correctly)
- **Line 30:** **DEFECT HERE** — Weekday check (Saturday/Sunday inverted)
- **Line 32-35:** Weekday peak window logic (affected downstream — Sunday incorrectly enters this block)
- **Line 36:** Off-peak return (affected downstream — Sunday incorrectly returns off-peak toll)

### Test Plan Validation

**Tests that caught the defect:**
- ✅ **T-H10** (Saturday is off-peak all day) — Caught Saturday being treated as free
- ✅ **T-H11** (Sunday free even during peak hours) — Caught Sunday being charged

**Why the defect was caught:**
- The test plan explicitly included HIGH-risk scenarios for weekend edge cases (T-H10, T-H11)
- Parametrized tests provided additional coverage across all weekdays
- Existing baseline test (`test_sunday_is_free_all_day`) also caught the issue

**Effectiveness:**
- **5 out of 50 tests failed** (10% failure rate)
- All failures trace to a **single line of code** (line 30)
- **Detection time:** Immediate (first test run after bug introduction)
- **No false positives:** All failures are legitimate defects

---

## Recommendations

1. **Immediate Action:** Revert line 30 in `salik/tariff.py` from `== 5` to `== 6`
2. **Verification:** Re-run full test suite to confirm all 50 tests pass
3. **Root Cause:** Investigate how this change was introduced (code review gap, merge conflict, typo)
4. **Prevention:** Add pre-commit hook to run weekend-specific tests before allowing commits to tariff logic
5. **Monitoring:** Add production monitoring for Saturday/Sunday toll patterns to detect similar issues in deployed code

---

## Appendix: Test Execution Details

**Command:**
```bash
.venv/bin/pytest -q --junitxml=reports/junit.xml \
  --cov=salik --cov-report=xml:reports/coverage.xml --cov-branch
```

**Exit Code:** 1 (test failures)

**Reports Generated:**
- `reports/junit.xml` — JUnit XML test results
- `reports/coverage.xml` — Cobertura XML coverage report
- `reports/analysis.md` — This document