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

# Plant the demo bug (Bob doesn't know to do this)
sed -i '' 's/when.weekday() == 6:/when.weekday() == 5:/' salik/tariff.py
grep -n "weekday() ==" salik/tariff.py    # verify line 30 reads "== 5"
```

---

## Stage 1 — Plan mode

```
You are a senior QA lead. Read the salik/ package and produce a test plan
focused on the tariff and violation modules.

Save to docs/test_plan.md as markdown with:
- In-scope files (paths)
- Risk-ranked scenarios (HIGH/MEDIUM/LOW), each with scenario ID
  (T-H1, V-M2, etc.), one-line rationale, and the behavior under test
- Coverage targets (statement + branch percentages)
- Out-of-scope (call out explicitly)

Focus on tariff time-window edges, fine escalation, and the annual cap.
Do NOT generate code. Do NOT modify files outside docs/.

After writing, run `wc -l docs/test_plan.md` and report the line count.
```

**Success criterion:** `docs/test_plan.md` exists; line count >100.

---

## Stage 2 — Code mode

```
Using docs/test_plan.md, generate pytest cases for every HIGH and MEDIUM
scenario into:
  tests/test_generated_tariff.py
  tests/test_generated_violations.py

HARD constraints (not suggestions):
- File names MUST start with `test_` (pytest discovery requirement).
- READ tests/test_tariff.py and tests/test_violations.py FIRST. Skip any
  scenario already covered there.
- One assertion per test where possible. Use @pytest.mark.parametrize for
  tabular cases. Do NOT keep BOTH individual and parametrized versions of
  the same scenarios.
- Each test docstring references its plan scenario ID (e.g. "Covers T-H3").
- Import ONLY from the salik package. Don't access private attributes
  (anything starting with _) unless existing tests already do so.
- Targets: ~12 tests for tariff, ~10 for violations.
- NO defensive tests for behavior the code does not claim (empty strings,
  negative values, very long inputs). NO sub-minute time precision tests
  (tariff uses minute granularity).

Before writing the files: show me the FULL file contents verbatim in two
fenced code blocks. Do NOT show a summary, checklist, or counts — only
the actual code I will be approving. Wait for my approval, then write.

After writing, verify:
  wc -l tests/test_generated_*.py
  grep -c "^def test_" tests/test_generated_*.py
```

**Success criterion:** files exist; counts within ~30% of targets; no `defensive`/`seconds` tests.

---

## Stage 3 — Advanced mode (or Code if shell works there)

```
Run in the shell:
  mkdir -p reports
  .venv/bin/pytest -q --junitxml=reports/junit.xml \
    --cov=salik --cov-report=xml:reports/coverage.xml --cov-branch

If pytest-cov is missing: .venv/bin/pip install pytest-cov, then re-run.

Then verify and report numbers only — do NOT analyse failures yet:
  ls -la reports/junit.xml reports/coverage.xml
  TOTAL=$(grep -c "<testcase" reports/junit.xml)
  FAILS=$(grep -c "<failure" reports/junit.xml)
  echo "Collected: $TOTAL  Failures: $FAILS"

If TOTAL is suspiciously low (e.g. only matches the existing test count,
not generated tests), STOP and report — pytest may have failed to discover
the generated files. Do not proceed to analysis.
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

PRE-FLIGHT — run ALL of these and report results before doing anything:
  gh auth status
  gh repo view $REPO --json defaultBranchRef --jq .defaultBranchRef.name
  gh label list --repo $REPO | grep -E "^(bug|severity:critical|area:tariff|bob-generated)\b"
  gh issue list --repo $REPO --state open --search "<defect title from analysis.md>"

STOP and report if: gh not auth'd, repo missing, ANY required label
missing, or duplicate issue found. Do NOT silently work around any failure.

If all checks pass, file the issue using gh issue create with:
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
  gh issue view $ISSUE_NUM --repo $REPO --json labels --jq '.labels[].name'

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
gh issue close <N> --repo $REPO --comment "Demo reset"
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
