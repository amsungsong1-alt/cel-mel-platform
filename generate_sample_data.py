"""Generate sample KoboToolbox-style Excel uploads for all 9 SAWA forms — Y1 Q1–Q4.

Run from the project root:
    python generate_sample_data.py

Outputs: sample_data/F1_Enrolment_Register_Y1.xlsx  …  F9_PMU_Knowledge_Test_Y1.xlsx
Each file has 4 sheets: Q1_Jan-Mar2026, Q2_Apr-Jun2026, Q3_Jul-Sep2026, Q4_Oct-Dec2026.
Upload one sheet at a time via Module D → Upload tab, selecting the matching form.
"""
import os
import random
from datetime import date, timedelta

import pandas as pd

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "sample_data")
os.makedirs(OUT_DIR, exist_ok=True)

QUARTERS = [
    ("Q1_Jan-Mar2026", "2026-01-01", "2026-03-31"),
    ("Q2_Apr-Jun2026", "2026-04-01", "2026-06-30"),
    ("Q3_Jul-Sep2026", "2026-07-01", "2026-09-30"),
    ("Q4_Oct-Dec2026", "2026-10-01", "2026-12-31"),
]

ENUMERATORS = ["Abena K.", "Kofi M.", "Akosua D.", "Yaw A.", "Efua N."]
SITES = ["Accra-Tema Hub", "Kumasi Hub", "Takoradi Hub", "Tamale Hub", "Cape Coast Hub"]
ANCHORS = ["R&B Farms", "AgroKings", "Yedent/Naple Betta", "Aglow Farms", "NewAge Agric"]


# ── helpers ───────────────────────────────────────────────────────────────────

def rand_date(start_str: str, end_str: str) -> str:
    s = date.fromisoformat(start_str)
    e = date.fromisoformat(end_str)
    return str(s + timedelta(days=random.randint(0, (e - s).days)))


def common(n: int, start: str, end: str) -> dict:
    return {
        "_id":            list(range(1001, 1001 + n)),
        "date_submitted": [rand_date(start, end) for _ in range(n)],
        "enumerator":     [random.choice(ENUMERATORS) for _ in range(n)],
        "site":           [random.choice(SITES) for _ in range(n)],
    }


def count_col(n: int, target: int):
    """target non-null 'Yes' values out of n rows."""
    vals = ["Yes"] * target + [None] * (n - target)
    random.shuffle(vals)
    return vals


def sum_int_col(total: int, n: int):
    """Distribute integer total across n rows."""
    if total == 0:
        return [None] * n
    base, rem = divmod(total, n)
    vals = [base + (1 if i < rem else 0) for i in range(n)]
    random.shuffle(vals)
    return vals


def sum_float_col(total: float, n: int, decimals: int = 3):
    """Distribute float total across n rows; last row absorbs rounding."""
    if total == 0:
        return [None] * n
    per = round(total / n, decimals)
    vals = [per] * (n - 1)
    vals.append(round(total - sum(vals), decimals))
    random.shuffle(vals)
    return vals


def mean_scores(target_mean: float, n: int = 20) -> list:
    """Generate n scores that average to target_mean (clamped 40–100)."""
    scores = [int(target_mean) + random.randint(-8, 8) for _ in range(n - 1)]
    last = round(target_mean * n - sum(scores))
    scores.append(max(40, min(100, last)))
    diff = round(sum(scores) / n - target_mean)
    scores = [max(40, min(100, s - diff)) for s in scores]
    random.shuffle(scores)
    return scores


def write_form(filename: str, sheets: list[tuple[str, pd.DataFrame]]):
    path = os.path.join(OUT_DIR, filename)
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for sheet_name, df in sheets:
            df.to_excel(w, sheet_name=sheet_name, index=False)
    print(f"  ✓  {filename}  ({len(sheets)} sheets)")


# ── Form 1 — Mobilisation & Enrolment Register ───────────────────────────────
# participant_enrolled (count): Q1=95  Q2=135 Q3=135 Q4=135
# pwd_enrolled         (count): Q1=1   Q2=2   Q3=2   Q4=3

def f1_sheet(q, s, e, enrolled, pwd):
    n = enrolled
    d = common(n, s, e)
    d["participant_name"] = [f"Participant-{i:04d}" for i in range(1, n + 1)]
    d["gender"] = ["Female"] * n
    d["age_group"] = [random.choice(["18-24", "25-35"]) for _ in range(n)]
    d["anchor_partner"] = [random.choice(ANCHORS) for _ in range(n)]
    d["participant_enrolled"] = count_col(n, enrolled)
    d["pwd_enrolled"] = count_col(n, pwd)
    return q, pd.DataFrame(d)

sheets = [
    f1_sheet(*QUARTERS[0], 95,  1),
    f1_sheet(*QUARTERS[1], 135, 2),
    f1_sheet(*QUARTERS[2], 135, 2),
    f1_sheet(*QUARTERS[3], 135, 3),
]
write_form("F1_Enrolment_Register_Y1.xlsx", sheets)


# ── Form 2 — Training Attendance Register ────────────────────────────────────
# bds_session_completed       (count): Q1=95  Q2=135 Q3=135 Q4=135
# gals_focal_person_trained   (count): Q1=0   Q2=0   Q3=15  Q4=10
# coop_training_attended      (sum):   Q1=0   Q2=150 Q3=150 Q4=200
# gender_transformative_attended(sum): Q1=0   Q2=150 Q3=150 Q4=200
# safeguarding_trained        (sum):   Q1=0   Q2=150 Q3=150 Q4=200
# digital_literacy_attended   (sum):   Q1=0   Q2=150 Q3=150 Q4=200

def f2_sheet(q, s, e, bds, gals, coop, gender, safe, digi):
    n = bds
    d = common(n, s, e)
    d["training_type"] = ["BDS"] * n
    d["bds_session_completed"] = count_col(n, bds)
    d["gals_focal_person_trained"] = count_col(n, gals)
    d["coop_training_attended"] = sum_int_col(coop, n)
    d["gender_transformative_attended"] = sum_int_col(gender, n)
    d["safeguarding_trained"] = sum_int_col(safe, n)
    d["digital_literacy_attended"] = sum_int_col(digi, n)
    return q, pd.DataFrame(d)

sheets = [
    f2_sheet(*QUARTERS[0], 95,  0,  0,   0,   0,   0),
    f2_sheet(*QUARTERS[1], 135, 0,  150, 150, 150, 150),
    f2_sheet(*QUARTERS[2], 135, 15, 150, 150, 150, 150),
    f2_sheet(*QUARTERS[3], 135, 10, 200, 200, 200, 200),
]
write_form("F2_Training_Attendance_Y1.xlsx", sheets)


# ── Form 3 — WAN Leadership Events Log ───────────────────────────────────────
# women_attended_forum   (sum):   Q1=0 Q2=0 Q3=300 Q4=200
# bootcamp_or_exchange_held(count): Q1=0 Q2=0 Q3=1   Q4=0

def f3_sheet(q, s, e, women_sum, bootcamp):
    n = max(bootcamp, 3 if women_sum > 0 else 0, 1)
    if women_sum == 0 and bootcamp == 0:
        df = pd.DataFrame(columns=[
            "_id", "date_submitted", "enumerator", "site",
            "event_name", "women_attended_forum", "bootcamp_or_exchange_held",
        ])
        return q, df
    d = common(n, s, e)
    d["event_name"] = [f"WAN Forum {i}" for i in range(1, n + 1)]
    d["women_attended_forum"] = sum_int_col(women_sum, n)
    d["bootcamp_or_exchange_held"] = count_col(n, bootcamp)
    return q, pd.DataFrame(d)

sheets = [
    f3_sheet(*QUARTERS[0], 0,   0),
    f3_sheet(*QUARTERS[1], 0,   0),
    f3_sheet(*QUARTERS[2], 300, 1),
    f3_sheet(*QUARTERS[3], 200, 0),
]
write_form("F3_WAN_Events_Y1.xlsx", sheets)


# ── Form 4 — PWD Mentor Registry ─────────────────────────────────────────────
# pwd_mentor_identified (count): Q1=1  Q2=2  Q3=2  Q4=3

def f4_sheet(q, s, e, mentors):
    n = max(mentors, 1)
    d = common(n, s, e)
    d["mentor_name"] = [f"PWD-Mentor-{i:03d}" for i in range(1, n + 1)]
    d["disability_type"] = [random.choice(["Physical", "Visual", "Hearing"]) for _ in range(n)]
    d["pwd_mentor_identified"] = count_col(n, mentors)
    d["mentee_assigned"] = [random.choice(["Yes", "Pending"]) for _ in range(n)]
    return q, pd.DataFrame(d)

sheets = [
    f4_sheet(*QUARTERS[0], 1),
    f4_sheet(*QUARTERS[1], 2),
    f4_sheet(*QUARTERS[2], 2),
    f4_sheet(*QUARTERS[3], 3),
]
write_form("F4_PWD_Mentor_Registry_Y1.xlsx", sheets)


# ── Form 5 — Tool 3 Cooperative & Governance Registry ────────────────────────
# cooperative_registered     (count): Q1=0 Q2=0 Q3=15 Q4=10
# governance_framework_adopted(count): Q1=0 Q2=0 Q3=15 Q4=10

def f5_sheet(q, s, e, coops, govs):
    n = max(coops, govs, 1)
    if coops == 0 and govs == 0:
        df = pd.DataFrame(columns=[
            "_id", "date_submitted", "enumerator", "site",
            "cooperative_name", "cooperative_registered", "governance_framework_adopted",
        ])
        return q, df
    d = common(n, s, e)
    d["cooperative_name"] = [f"Women's Coop {i:02d}" for i in range(1, n + 1)]
    d["anchor_partner"] = [random.choice(ANCHORS) for _ in range(n)]
    d["cooperative_registered"] = count_col(n, coops)
    d["governance_framework_adopted"] = count_col(n, govs)
    return q, pd.DataFrame(d)

sheets = [
    f5_sheet(*QUARTERS[0], 0,  0),
    f5_sheet(*QUARTERS[1], 0,  0),
    f5_sheet(*QUARTERS[2], 15, 15),
    f5_sheet(*QUARTERS[3], 10, 10),
]
write_form("F5_Cooperative_Registry_Y1.xlsx", sheets)


# ── Form 6 — Safeguarding Monitoring Form ────────────────────────────────────
# campaign_roadshow_held (count): Q1=0 Q2=0 Q3=0 Q4=3
# site_certified         (count): Q1=0 Q2=0 Q3=0 Q4=2

def f6_sheet(q, s, e, campaigns, sites_cert):
    n = max(campaigns, sites_cert, 1)
    if campaigns == 0 and sites_cert == 0:
        df = pd.DataFrame(columns=[
            "_id", "date_submitted", "enumerator", "site",
            "campaign_roadshow_held", "site_certified",
        ])
        return q, df
    d = common(n, s, e)
    d["safeguarding_officer"] = [f"Officer-{i:02d}" for i in range(1, n + 1)]
    d["campaign_roadshow_held"] = count_col(n, campaigns)
    d["site_certified"] = count_col(n, sites_cert)
    return q, pd.DataFrame(d)

sheets = [
    f6_sheet(*QUARTERS[0], 0, 0),
    f6_sheet(*QUARTERS[1], 0, 0),
    f6_sheet(*QUARTERS[2], 0, 0),
    f6_sheet(*QUARTERS[3], 3, 2),
]
write_form("F6_Safeguarding_Monitor_Y1.xlsx", sheets)


# ── Form 7 — PWD Production & Revenue Tracker ────────────────────────────────
# fish_volume_mt_pwd (sum): Q1=1.0  Q2=2.0  Q3=2.0  Q4=3.0
# revenue_usd_pwd    (sum): Q1=2083 Q2=4167 Q3=4167 Q4=6250

def f7_sheet(q, s, e, fish, rev):
    n = 2  # 2 PWD farms per quarter
    d = common(n, s, e)
    d["pwd_farmer_id"] = [f"PWD-F-{i:03d}" for i in range(1, n + 1)]
    d["fish_species"] = [random.choice(["Tilapia", "Catfish"]) for _ in range(n)]
    d["pond_count"] = [random.randint(1, 5) for _ in range(n)]
    d["fish_volume_mt_pwd"] = sum_float_col(fish, n)
    d["revenue_usd_pwd"] = sum_int_col(rev, n)
    return q, pd.DataFrame(d)

sheets = [
    f7_sheet(*QUARTERS[0], 1.0, 2083),
    f7_sheet(*QUARTERS[1], 2.0, 4167),
    f7_sheet(*QUARTERS[2], 2.0, 4167),
    f7_sheet(*QUARTERS[3], 3.0, 6250),
]
write_form("F7_PWD_Production_Y1.xlsx", sheets)


# ── Form 8 — Value-Addition Enterprise Tracker ───────────────────────────────
# value_addition_jobs (sum): Q1=0  Q2=40     Q3=30     Q4=30
# fish_volume_mt_va   (sum): Q1=0  Q2=46.3   Q3=34.7   Q4=34.7
# revenue_usd_va      (sum): Q1=0  Q2=83333  Q3=62500  Q4=62500

def f8_sheet(q, s, e, jobs, fish, rev):
    if jobs == 0:
        df = pd.DataFrame(columns=[
            "_id", "date_submitted", "enumerator", "site",
            "enterprise_name", "value_addition_jobs", "fish_volume_mt_va", "revenue_usd_va",
        ])
        return q, df
    n = 5  # 5 enterprises
    d = common(n, s, e)
    d["enterprise_name"] = [f"VA-Enterprise-{i:02d}" for i in range(1, n + 1)]
    d["enterprise_type"] = [random.choice(["Processing", "Trading", "Both"]) for _ in range(n)]
    d["value_addition_jobs"] = sum_int_col(jobs, n)
    d["fish_volume_mt_va"] = sum_float_col(fish, n)
    d["revenue_usd_va"] = sum_int_col(rev, n)
    return q, pd.DataFrame(d)

sheets = [
    f8_sheet(*QUARTERS[0], 0,  0.0,  0),
    f8_sheet(*QUARTERS[1], 40, 46.3, 83333),
    f8_sheet(*QUARTERS[2], 30, 34.7, 62500),
    f8_sheet(*QUARTERS[3], 30, 34.7, 62500),
]
write_form("F8_Value_Addition_Y1.xlsx", sheets)


# ── Form 9 — PMU Pre/Post Knowledge Test ─────────────────────────────────────
# post_test_score (mean): Q1=70 Q2=72 Q3=78 Q4=82

def f9_sheet(q, s, e, mean_score):
    n = 20
    d = common(n, s, e)
    d["participant_id"] = [f"PMU-{i:03d}" for i in range(1, n + 1)]
    d["training_type"] = ["Gender Transformative"] * n
    scores = mean_scores(mean_score, n)
    d["pre_test_score"] = [max(30, sc - random.randint(10, 20)) for sc in scores]
    d["post_test_score"] = scores
    return q, pd.DataFrame(d)

sheets = [
    f9_sheet(*QUARTERS[0], 70),
    f9_sheet(*QUARTERS[1], 72),
    f9_sheet(*QUARTERS[2], 78),
    f9_sheet(*QUARTERS[3], 82),
]
write_form("F9_PMU_Knowledge_Test_Y1.xlsx", sheets)


# ── summary ───────────────────────────────────────────────────────────────────
print(f"\nAll 9 sample files written to:\n  {OUT_DIR}\n")
print("Upload instructions:")
print("  1. Open Module D → Upload tab")
print("  2. Select the matching form from the dropdown")
print("  3. Upload the correct quarterly sheet (copy it to a separate file first,")
print("     or rename the sheet to strip the quarter prefix if needed)")
print("  4. Click 'Apply mapping & write to Module E'")
print("\nQuarterly targets encoded in each file:")
print("  Form  | Indicator  | Q1    | Q2    | Q3    | Q4")
print("  ------+------------+-------+-------+-------+-------")
print("  F1    | PI.1       |  95   | 135   | 135   | 135")
print("  F1    | PII.R5     |   1   |   2   |   2   |   3")
print("  F2    | PI.3       |  95   | 135   | 135   | 135")
print("  F2    | PI.9       |   0   |   0   |  15   |  10")
print("  F2    | PI.17      |   0   | 150   | 150   | 200")
print("  F2    | PI.19      |   0   | 150   | 150   | 200")
print("  F2    | PI.20      |   0   | 150   | 150   | 200")
print("  F2    | PIV.5      |   0   | 150   | 150   | 200")
print("  F3    | PI.11      |   0   |   0   | 300   | 200")
print("  F3    | PI.12      |   0   |   0   |   1   |   0")
print("  F4    | PI.13      |   1   |   2   |   2   |   3")
print("  F5    | PIII.6     |   0   |   0   |  15   |  10")
print("  F5    | PI.18      |   0   |   0   |  15   |  10")
print("  F6    | PI.22      |   0   |   0   |   0   |   3")
print("  F6    | PI.23      |   0   |   0   |   0   |   2")
print("  F7    | PII.R6 MT  | 1.0   | 2.0   | 2.0   | 3.0")
print("  F7    | PII.R7 USD |2,083  |4,167  |4,167  |6,250")
print("  F8    | PIII.R1    |   0   |  40   |  30   |  30")
print("  F8    | PIII.R2 MT |   0   |46.3   |34.7   |34.7")
print("  F8    | PIII.R3 USD|   0   |83,333 |62,500 |62,500")
print("  F9    | PI.19 mean |  70%  |  72%  |  78%  |  82%")
