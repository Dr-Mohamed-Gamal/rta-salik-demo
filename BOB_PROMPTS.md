# IBM Bob — RTA QA Lifecycle Demo Prompts

Hardened five-stage prompt set for demoing IBM Bob (bob.ibm.com) to RTA Dubai. Distilled from a full live-fire run on 2026-05-06: every correction, drop, and recovery is baked in.

System under test: the Salik emulator in this repo (`salik/` package).

---

## Stage 0 — One-time setup (manual, before demo)

Run in terminal. Don't ask Bob.

```bash
PROJECT=/Users/mohamedgamal/Downloads/RTA_SAMPLE_CODE
REPO=Dr-Mohamed-Gamal/rta-salik-demo
cd $PROJECT

# Tooling
brew install gh                      # if missing
gh auth login                        # interactive
python3 -m venv .venv
.venv/bin/pip install pytest pytest-cov

# Push code so artifact links in the GitHub issue resolve
gh repo create $REPO --public --source=. --push  # skip if repo already populated

# Pre-create labels (Bob silently drops missing ones)
gh label create "severity:critical" --repo $REPO --color b60205 --description "Critical severity"
gh label create "area:tariff"       --repo $REPO --color 0075ca --description "Tariff module"
gh label create "bob-generated"     --repo $REPO --color a2eeef --description "Filed by IBM Bob"

# Plant the demo bug ONCE (it lives permanently in the code).
# The spec lives in docs/SPEC.md and is what Bob reads in Stage 1.
# Tests assert the spec; the buggy code disagrees with the spec; tests fail.
sed -i '' 's/when.weekday() == 6:/when.weekday() == 5:/' salik/tariff.py
grep -n "weekday() ==" salik/tariff.py    # must show "== 5"
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

Then STOP. Do NOT generate test code. Do NOT switch modes. Do NOT touch
tests/. Wait for my next instruction.
```

**Success criterion:** `docs/test_plan.md` exists, is non-empty, head shows real plan content; Sunday=free and Saturday=off-peak appear in the plan (matching SPEC.md, not the buggy code).

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
  (b) assert dt.weekday() == N immediately before calling toll_for(dt),
      so a wrong-date assumption fails loudly instead of silently passing.

FINE TOTAL ASSERTIONS — express expected totals as formulas using
FINE_SCHEDULE elements, NOT hardcoded numbers. Example:
  expected = FINE_SCHEDULE[0] + FINE_SCHEDULE[1] + FINE_SCHEDULE[2]
  assert registry.total_for(plate) == expected
This makes the math self-documenting and removes hand-calculation errors.

Before writing: show me the FULL file contents verbatim in two fenced
code blocks. Wait for my approval, then write.

After writing, smoke-test:
  .venv/bin/pytest tests/test_generated_*.py --collect-only -q 2>&1 | tail -3
  .venv/bin/pytest tests/test_generated_*.py --no-header -rN 2>&1 | grep -E "NameError|ImportError|SyntaxError" | head -5

First command must show "N tests collected". Second must return nothing.
Then STOP. Wait.
```

**Success criterion:** files exist, smoke test shows N tests collected with zero NameError/ImportError/SyntaxError; weekday assertions and FINE_SCHEDULE formulas present.

---

## Stage 3 — Advanced mode (or Code if shell works there)

```
Run in the shell:
  mkdir -p reports
  .venv/bin/pytest -q --junitxml=reports/junit.xml \
    --cov=salik --cov-report=xml:reports/coverage.xml --cov-branch

If pytest-cov is missing: .venv/bin/pip install pytest-cov, then re-run.

Then verify with pytest's own count (more reliable than grep) and report
numbers only — do NOT analyse failures yet:
  ls -la reports/junit.xml reports/coverage.xml
  TOTAL=$(.venv/bin/pytest --collect-only -q tests/ 2>/dev/null | tail -1 | grep -oE "[0-9]+")
  FAILS=$(grep -oE 'failures="[0-9]+"' reports/junit.xml | grep -oE "[0-9]+" | head -1)
  ERRORS=$(grep -oE 'errors="[0-9]+"' reports/junit.xml | grep -oE "[0-9]+" | head -1)
  echo "Collected: $TOTAL  Failures: $FAILS  Errors: $ERRORS"

ERRORS must be 0 — any non-zero means a test file has a code bug
(NameError, ImportError, syntax). If ERRORS > 0, STOP and report.

If TOTAL is suspiciously low or 0, STOP and report — pytest may have
failed to discover the generated files.

Then STOP. Do NOT analyse failures. Wait for my next instruction.
```

**Success criterion:** TOTAL ≈ 50, FAILS ≈ 5 (with planted bug), both XML files non-empty.

---

## Stage 4 — Ask mode

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
monthly losses. If you don't have production data, describe the loss
STRUCTURE mathematically and write "requires production data to quantify."

Do not edit any source files. Only write reports/analysis.md.

After writing, run these self-checks and paste the output verbatim:
  grep -nE "AED [0-9]|crossings/month|estimated.*loss" reports/analysis.md
  wc -l reports/analysis.md
The grep MUST return nothing. If it returns lines, you invented numbers —
remove them before reporting "Task Completed".
```

**Success criterion:** one defect (not five), grep returns no hits, fix shown as unified diff, source files untouched.

---

## Stage 5 — Advanced mode

```
Read reports/analysis.md. For each defect in the summary table, file ONE
GitHub issue. Most runs produce exactly one issue.

REPO=Dr-Mohamed-Gamal/rta-salik-demo
GH=/opt/homebrew/bin/gh   # Bob's shell often lacks Homebrew in PATH; use full path

PRE-FLIGHT — run ALL of these and report results before doing anything:
  $GH auth status
  $GH repo view $REPO --json defaultBranchRef --jq .defaultBranchRef.name
  $GH label list --repo $REPO | grep -E "^(bug|severity:critical|area:tariff|bob-generated)\b"
  $GH issue list --repo $REPO --state open --search "<defect title from analysis.md>"

STOP and report if: gh not auth'd, repo missing, ANY required label
missing, or duplicate issue found. Do NOT silently work around any failure.

If all checks pass, file the issue using `$GH issue create` with:
- Title:  [BOB][<severity>] <one-line title>
- Labels: bug,bob-generated,severity:<level>,area:<module>
- Body sections: Repro / Expected / Actual / Suggested fix (diff) /
  Symptoms (N tests, file:line, scenario IDs) / Impact (no invented
  numbers) / Artifacts (use FULL https://github.com/$REPO/blob/main/...
  URLs, not bare paths)

The Repro pytest -k filter MUST be precise — `or test_weekday_rules`
catches passing cases too. Use `or "test_weekday_rules[5-" or
"test_weekday_rules[6-"` to isolate just the failing parametrized cases.

After creation, verify ALL four labels landed:
  ISSUE_NUM=<number from URL>
  $GH issue view $ISSUE_NUM --repo $REPO --json labels --jq '.labels[].name'

Output must list bug, bob-generated, severity:<level>, area:<module>.
If any are missing, STOP and report — do not retry silently.
```

**Success criterion:** issue at a real URL, all four labels visible via gh CLI (browser may cache), artifact links resolve.

---

## Cross-stage rules — the meta-lesson

1. **"Show file contents verbatim in fenced code blocks."** Never "show the diff" — Bob returns summaries.
2. **Append a shell verification step to every action prompt** (`grep`, `wc -l`, `gh issue view`, `bash -n`). Bob can't fake shell output.
3. **Pre-flight checks with explicit "stop and report" branches.** Bob honors guards. Without them it silently works around problems.
4. **Forbid invented numbers.** Especially financial impact. Tell Bob to describe loss structure mathematically when it lacks data.
5. **Read existing artifacts first.** Generated tests skip what existing tests cover. Generated issues check for duplicates.

---

## Between-run cleanup

```bash
/opt/homebrew/bin/gh issue close <N> --repo $REPO --comment "Demo reset"
sed -i '' 's/when.weekday() == 6:/when.weekday() == 5:/' salik/tariff.py
rm -f reports/{junit,coverage}.xml reports/analysis.md reports/issues_to_file.sh
rm -f tests/test_generated_*.py
rm -f docs/test_plan.md
```

---

## Demo-day talking points (use as the human-in-the-loop story)

Real Bob mistakes from the live run on 2026-05-06, all caught by human verification — these ARE the pitch:

1. Bob said "show the diff" but returned a summary → demanded verbatim contents
2. Bob generated 73 tests for ~70 LOC → capped to ~22
3. Bob invented "defensive" tests for behavior the code didn't claim → forbidden
4. Bob's pytest run reported 19/19 pass when 50 tests existed → discovery missed `generated_*.py` files; renamed to `test_*.py`
5. Bob said "coverage not reported" while coverage.xml sat on disk → trust artifacts, not summaries
6. Bob fabricated AED 200k–500k loss estimates → replaced with "requires production data"
7. Bob marked Stage 4 "Task Completed" without editing the file → grep verification forced real edit
8. Bob silently dropped 3 of 4 labels when one missing → pre-create labels in setup

Each catch is a separate demo moment. Don't hide them.
