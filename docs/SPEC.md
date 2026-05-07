# Salik Toll System — Business Rules Specification

This document is the **authoritative source of truth** for Salik tolling and violation rules. The implementation in `salik/` must conform to this specification. Any discrepancy between this document and the code is a defect in the code.

---

## 1. Tariff Rules

### 1.1 Time windows

| Window | Time range | Days |
|---|---|---|
| Free window | 01:00 ≤ t < 06:00 | Every day |
| Morning peak | 06:00 ≤ t < 10:00 | Monday – Friday only |
| Evening peak | 16:00 ≤ t < 20:00 | Monday – Friday only |
| Off-peak | all other hours | Weekdays + Saturday |

### 1.2 Tariff amounts (AED per gantry pass)

| Window | Amount |
|---|---|
| Peak | 6.00 |
| Off-peak | 4.00 |
| Free | 0.00 |

### 1.3 Weekend rules

- **Saturday** (`weekday() == 5`): off-peak rate applies all day outside the free window. **Saturday is NOT a free day.**
- **Sunday** (`weekday() == 6`): **free all day**, regardless of time. No tolls are charged on Sundays.

---

## 2. Violation Rules

### 2.1 Fine schedule (per plate, per offence)

| Offence number | Fine (AED) |
|---|---|
| 1st | 100 |
| 2nd | 200 |
| 3rd and subsequent | 400 |

### 2.2 Annual cap

- Maximum total fines per plate per calendar year: **AED 10,000**
- When recording a violation that would exceed the cap, the fine is clamped so total never exceeds AED 10,000.
- Once the cap is reached, subsequent violations within the same year incur AED 0.

---

## 3. Out-of-scope (this specification does not cover)

- Account management, top-ups, low-balance alerts
- Vehicle registration / Emirates ID validation
- Performance, scalability, security
- User interfaces (CLI, web, mobile)
- Reporting and analytics

These areas may exist in the codebase but are not under test for this lifecycle.
