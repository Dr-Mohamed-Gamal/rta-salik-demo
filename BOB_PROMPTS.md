# IBM Bob — RTA QA Lifecycle Demo Prompts

System under test: the Salik emulator in this repo. Spec: `docs/SPEC.md`. Bug planted permanently in `salik/tariff.py` line 30.

---

## Stage 0 — One-time setup (terminal, already done)

```bash
PROJECT=/Users/mohamedgamal/Downloads/RTA_SAMPLE_CODE
REPO=Dr-Mohamed-Gamal/rta-salik-demo
cd $PROJECT

brew install gh                      # if missing
gh auth login                        # interactive
python3 -m venv .venv
.venv/bin/pip install pytest pytest-cov

gh repo create $REPO --public --source=. --push   # skip if already populated

gh label create "severity:critical" --repo $REPO --color b60205 --description "Critical severity"
gh label create "area:tariff"       --repo $REPO --color 0075ca --description "Tariff module"
gh label create "bob-generated"     --repo $REPO --color a2eeef --description "Filed by IBM Bob"

sed -i '' 's/when.weekday() == 6:/when.weekday() == 5:/' salik/tariff.py
grep -n "weekday() ==" salik/tariff.py
```

---

## Stage 1 — Code mode

```
You are a senior QA lead.

FIRST, read docs/SPEC.md — this is the AUTHORITATIVE business specification.
THEN read the salik/ package for implementation details.

Your test plan asserts what SPEC.md says, not what the code currently does.
The implementation may have defects; tests are how we discover them.

Save to docs/test_plan.md as markdown with:
- In-scope files (paths)
- Risk-ranked scenarios (HIGH/MEDIUM/LOW), each with scenario ID
  (T-H1, V-M2, etc.), one-line rationale, and the spec rule under test
- Coverage targets (statement + branch percentages)
- Out-of-scope (call out explicitly)

Focus on tariff time-window edges, fine escalation, and the annual cap.
Do NOT generate test code. Do NOT modify files outside docs/test_plan.md.

After writing, run THESE shell commands and paste the output verbatim:
  ls -la docs/test_plan.md
  wc -l docs/test_plan.md
  head -20 docs/test_plan.md
  echo "Byte count: $(wc -c < docs/test_plan.md)"

If byte count is 0, you have not finished — try again.

Then STOP. Do NOT generate test code. Do NOT switch modes. Wait.
```

---

## Stage 2 — Code mode

```
Using docs/test_plan.md, generate pytest cases for every HIGH and MEDIUM
scenario into:
  tests/test_generated_tariff.py
  tests/test_generated_violations.py

READ salik/tariff.py and salik/violations.py FIRST. Use the exact
constant names and rules from the source — do not guess or abbreviate.

Constraints:
- File names MUST start with `test_`.
- Use @pytest.mark.parametrize for tabular cases. Don't keep BOTH
  individual and parametrized versions.
- Each test docstring references its plan scenario ID (e.g. "Covers T-H3").
- Import ONLY from salik. Use EXACT export names from the source.
- Targets: ~12 tests for tariff, ~10 for violations.
- NO defensive tests. NO sub-minute time precision tests.

WEEKDAY TESTS — never hardcode a calendar date with a weekday name in a
comment. Either:
  (a) compute the date with timedelta from a known Monday anchor, OR
  (b) assert dt.weekday() == N immediately before calling toll_for(dt).

FINE TOTAL ASSERTIONS — express expected totals as formulas using
FINE_SCHEDULE elements, NOT hardcoded numbers. Example:
  expected = FINE_SCHEDULE[0] + FINE_SCHEDULE[1] + FINE_SCHEDULE[2]
  assert registry.total_for(plate) == expected

Before writing: show me the FULL file contents verbatim in two fenced
code blocks. Wait for my approval, then write.

After writing, smoke-test:
  .venv/bin/pytest tests/test_generated_*.py --collect-only -q 2>&1 | tail -3
  .venv/bin/pytest tests/test_generated_*.py --no-header -rN 2>&1 | grep -E "NameError|ImportError|SyntaxError" | head -5

First command must show "N tests collected". Second must return nothing.
Then STOP. Wait.
```

---

## Stage 3 — Advanced mode

```
Run in the shell:
  mkdir -p reports
  .venv/bin/pytest -q --junitxml=reports/junit.xml \
    --cov=salik --cov-report=xml:reports/coverage.xml --cov-branch

If pytest-cov is missing: .venv/bin/pip install pytest-cov, then re-run.

Then verify and report numbers only — do NOT analyse failures yet:
  ls -la reports/junit.xml reports/coverage.xml
  TOTAL=$(.venv/bin/pytest --collect-only -q tests/ 2>/dev/null | tail -1 | grep -oE "[0-9]+")
  FAILS=$(grep -oE 'failures="[0-9]+"' reports/junit.xml | grep -oE "[0-9]+" | head -1)
  ERRORS=$(grep -oE 'errors="[0-9]+"' reports/junit.xml | grep -oE "[0-9]+" | head -1)
  echo "Collected: $TOTAL  Failures: $FAILS  Errors: $ERRORS"

ERRORS must be 0. If TOTAL is suspiciously low or ERRORS > 0, STOP.

Then STOP. Do NOT analyse failures. Wait.
```

---

## Stage 4 — Code mode

```
Read reports/junit.xml and reports/coverage.xml.

CRITICAL — Group failures into defects, not one defect per failure.
Symptoms ≠ defects. If 5 tests fail because of one line of code, that is
ONE defect with five symptoms.

Write reports/analysis.md with:

  ## Summary table
  | Defect ID | Symptoms (count) | Severity | Module |

  ## Defect <ID>: <one-line title>
  - Root cause class: {logic-bug | spec-ambiguity | flaky-test | env-issue}
  - Severity: Critical/High/Med/Low — justify using a toll-revenue +
    driver-fairness rubric (who pays wrongly? who escapes paying?)
  - Symptoms: each failing test with file:line, scenario ID from docstring,
    and the assertion verbatim
  - Suggested fix as a unified diff (do NOT apply)
  - Coverage impact

DO NOT invent numbers. No fabricated AED amounts, crossing volumes, or
monthly losses. Describe loss STRUCTURE mathematically and write
"requires production data to quantify."

Do not edit any source files. Only write reports/analysis.md.

After writing, run these self-checks and paste the output verbatim:
  grep -nE "AED [0-9]|crossings/month|estimated.*loss" reports/analysis.md
  wc -l reports/analysis.md

The grep MUST return nothing.

Then STOP. Wait.
```

---

## Stage 5 — Advanced mode

```
gh IS installed at /opt/homebrew/bin/gh — your shell PATH does not include
/opt/homebrew/bin. Verify with:
  /opt/homebrew/bin/gh --version

Now read reports/analysis.md and file ONE GitHub issue per defect.

REPO=Dr-Mohamed-Gamal/rta-salik-demo
GH=/opt/homebrew/bin/gh

PRE-FLIGHT — run ALL and report results before doing anything:
  $GH auth status
  $GH repo view $REPO --json defaultBranchRef --jq .defaultBranchRef.name
  $GH label list --repo $REPO | grep -E "^(bug|severity:critical|area:tariff|bob-generated)\b"
  $GH issue list --repo $REPO --state open --search "Saturday Sunday weekday"

STOP and report if: not auth'd, repo missing, ANY required label missing,
or duplicate issue found.

If all checks pass, file the issue using `$GH issue create` with:
- Title:  [BOB][<severity>] <one-line title from analysis.md>
- Labels: bug,bob-generated,severity:<level>,area:<module>
- Body sections: Repro / Expected / Actual / Suggested fix (diff) /
  Symptoms (N tests, file:line, scenario IDs) / Impact / Artifacts
  (use FULL https://github.com/$REPO/blob/main/... URLs, not bare paths)

The Repro pytest -k filter MUST be precise — use exact failing test names,
not broad `or test_weekday_rules` patterns that match passing cases too.

After creation, verify ALL four labels landed:
  ISSUE_NUM=<number from URL>
  $GH issue view $ISSUE_NUM --repo $REPO --json labels --jq '.labels[].name'

Output must list bug, bob-generated, severity:<level>, area:<module>.
If any are missing, STOP and report — do not retry silently.
```

---

## Between-run cleanup (terminal)

```bash
REPO=Dr-Mohamed-Gamal/rta-salik-demo
GH=/opt/homebrew/bin/gh
cd /Users/mohamedgamal/Downloads/RTA_SAMPLE_CODE

for n in $($GH issue list --repo $REPO --state open --json number --jq '.[].number'); do
  $GH issue close $n --repo $REPO --comment "Demo reset"
done

rm -f reports/junit.xml reports/coverage.xml reports/analysis.md reports/issues_to_file.sh
rm -f tests/test_generated_*.py
rm -f docs/test_plan.md
```
