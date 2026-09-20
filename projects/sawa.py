"""SAWA project constants — partners, indicators, targets, budget."""

PROJECT = {
    "name":         "SAWA",
    "donor":        "Mastercard Foundation",
    "budget_total": 39_810_000,   # USD 39.81M
    "start_date":   "2026-01-01",
    "end_date":     "2030-12-31",
}

# ── Partners ──────────────────────────────────────────────────────────────────
PARTNERS = [
    {"name": "R&B Farms",          "role": "Anchor Partner", "tier": "Anchor"},
    {"name": "AgroKings",          "role": "Anchor Partner", "tier": "Anchor"},
    {"name": "Yedent/Naple Betta", "role": "Anchor Partner", "tier": "Anchor"},
    {"name": "Aglow Farms",        "role": "Anchor Partner", "tier": "Anchor"},
    {"name": "NewAge Agric",       "role": "Anchor Partner", "tier": "Anchor"},
]

# ── Module A — Partner Target Funnel ──────────────────────────────────────────
# partner_name=None → Level 2/3/4 (programme-wide, no single partner).
PARTNER_TARGETS = [
    # ── Level 1: Anchor Partner Commitments (source: SAWA Proposal, 28 Nov 2025)
    {"partner_name": "R&B Farms",          "level": 1, "metric_label": "Young women & PWDs",     "target_value": "7,000",   "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": "AgroKings",          "level": 1, "metric_label": "Young women & PWDs",     "target_value": "14,000",  "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": "Yedent/Naple Betta", "level": 1, "metric_label": "Jobs",                   "target_value": "6,000",   "unit": "jobs",          "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": "Yedent/Naple Betta", "level": 1, "metric_label": "SME graduates",          "target_value": "800",     "unit": "graduates",     "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": "Aglow Farms",        "level": 1, "metric_label": "Young women",            "target_value": "3,000",   "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": "NewAge Agric",       "level": 1, "metric_label": "Production jobs",        "target_value": "5,000",   "unit": "jobs",          "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": "NewAge Agric",       "level": 1, "metric_label": "Processing jobs",        "target_value": "1,000",   "unit": "jobs",          "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},

    # ── Level 2: CEL Year 1 Delivery (source: CEL Year 1 Consolidated Workplan)
    {"partner_name": None, "level": 2, "metric_label": "Youth mobilised",               "target_value": "500", "unit": "youth",        "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "BDS trained",                   "target_value": "500", "unit": "participants", "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "Cooperative frameworks",         "target_value": "25",  "unit": "cooperatives", "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "Gender-transformative trained", "target_value": "500", "unit": "participants", "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "Safeguarding trained",          "target_value": "500", "unit": "participants", "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "PWD mentors identified",        "target_value": "8",   "unit": "mentors",      "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},

    # ── Level 3: Year 1 Results (source: CEL Year 1 Consolidated Workplan)
    {"partner_name": None, "level": 3, "metric_label": "Plll.R1  D&F jobs (value addition)",       "target_value": "100",     "unit": "jobs",    "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "Pll.R5   D&F jobs (PWD, programme-wide)",  "target_value": "8",       "unit": "jobs",    "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "Pll.R6   Fish produced by PWDs in D&F",   "target_value": "9.26",    "unit": "MT",      "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "Pll.R7   Revenue, PWDs in D&F",           "target_value": "16,667",  "unit": "USD",     "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "Plll.R2  Fish produced/traded",           "target_value": "115.74",  "unit": "MT",      "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "Plll.R3  Revenue, value-added trading",   "target_value": "208,333", "unit": "USD",     "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan", "source_page": ""},

    # ── Level 4: Programme Impact (source: SAWA Proposal, 28 Nov 2025)
    {"partner_name": None, "level": 4, "metric_label": "Young women & PWDs into D&F work",  "target_value": "60,000+", "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": None, "level": 4, "metric_label": "D&F transition rate",               "target_value": "86",      "unit": "%",             "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": None, "level": 4, "metric_label": "Additional fish production/year",   "target_value": "50,000",  "unit": "MT",            "time_basis": "Annual",            "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": None, "level": 4, "metric_label": "Additional annual revenue",         "target_value": "90M",     "unit": "USD",           "time_basis": "Annual",            "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": None, "level": 4, "metric_label": "Women-led microenterprises funded", "target_value": "2,500",   "unit": "enterprises",   "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
    {"partner_name": None, "level": 4, "metric_label": "Productivity improvement",          "target_value": "≥30",     "unit": "%",             "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025", "source_page": ""},
]

# ── Budget by pillar (source: SAWA Proposal s8.1) ─────────────────────────────
PILLAR_BUDGETS = {
    "Pillar I — Capacity":         2_410_000,
    "Pillar II — Production":     26_780_000,
    "Pillar III — Value Addition":  7_270_000,
    "Pillar IV — Ecosystem":          820_000,
    "Delivery Fee":                 2_580_000,
}

# ── Module B: Theory of Change nodes ─────────────────────────────────────────
# Use `key` / `parent_key` strings; seed_sawa.py resolves these to DB IDs.
TOC_NODES = [
    # ── Impact ────────────────────────────────────────────────────────────────
    {
        "key": "IMP", "parent_key": None, "level": "Impact",
        "statement": (
            "Over 60,000 financially disadvantaged young women and PWDs "
            "engaged in dignified and fulfilling work in Ghana's fisheries "
            "and aquaculture (D&F) sector, with improved income and "
            "long-term economic resilience."
        ),
    },
    # ── Outcomes ──────────────────────────────────────────────────────────────
    {
        "key": "OC1", "parent_key": "IMP", "level": "Outcome",
        "statement": (
            "Young women and PWDs in targeted D&F value chains have "
            "increased employment opportunities and sustained income."
        ),
    },
    {
        "key": "OC2", "parent_key": "IMP", "level": "Outcome",
        "statement": (
            "D&F enterprises supported by SAWA demonstrate sustained "
            "growth and strengthened market access, with inclusive "
            "employment of young women and PWDs."
        ),
    },
    {
        "key": "OC3", "parent_key": "IMP", "level": "Outcome",
        "statement": (
            "D&F livelihoods of young women and PWDs are more "
            "climate-resilient, supported by an enabling policy "
            "and investment ecosystem."
        ),
    },
    # ── Intermediate Outcomes ─────────────────────────────────────────────────
    {
        "key": "IO1", "parent_key": "OC1", "level": "Intermediate Outcome",
        "statement": (
            "Young women and PWDs have the skills, confidence, "
            "networks and initial resources to enter and succeed "
            "in D&F work."
        ),
    },
    {
        "key": "IO2", "parent_key": "OC2", "level": "Intermediate Outcome",
        "statement": (
            "Anchor partner enterprises scale production and value "
            "addition with inclusive hiring practices and strengthened "
            "market linkages."
        ),
    },
    {
        "key": "IO3", "parent_key": "OC3", "level": "Intermediate Outcome",
        "statement": (
            "The D&F sector ecosystem — policy, private investment "
            "and coordination — actively enables inclusive and "
            "sustainable enterprise growth."
        ),
    },
    # ── Outputs ───────────────────────────────────────────────────────────────
    {
        "key": "OP1", "parent_key": "IO1", "level": "Output",
        "statement": (
            "OP1 — Capacity: Youth mobilised; BDS and gender-transformative "
            "training delivered; cooperatives and PWD mentoring established."
        ),
    },
    {
        "key": "OP2", "parent_key": "IO2", "level": "Output",
        "statement": (
            "OP2 — Production: Investment in fishpond and aquaculture "
            "facilities; PWDs integrated into production roles; "
            "fish output and revenue targets met."
        ),
    },
    {
        "key": "OP3", "parent_key": "IO2", "level": "Output",
        "statement": (
            "OP3 — Value Addition: Fish processing and trading "
            "enterprises supported; cold-chain and storage established; "
            "market linkages formalised."
        ),
    },
    {
        "key": "OP4", "parent_key": "IO3", "level": "Output",
        "statement": (
            "OP4 — Ecosystem: Policy and regulatory engagement "
            "conducted; private-sector investment catalysed; "
            "MoUs and cross-learning events delivered."
        ),
    },
    # ── Inputs ────────────────────────────────────────────────────────────────
    {
        "key": "IN1", "parent_key": "OP1", "level": "Input",
        "statement": "CEL programme funding — USD 39.81M (Pillars I–IV + delivery fee)",
    },
    {
        "key": "IN2", "parent_key": "OP2", "level": "Input",
        "statement": "Anchor partner co-investment: facilities, land, supply-chain access",
    },
    {
        "key": "IN3", "parent_key": "OP4", "level": "Input",
        "statement": "Government policy alignment, regulatory frameworks and public infrastructure",
    },
]

# ── Module B: Logframe rows ───────────────────────────────────────────────────
# Three stated SAWA ToC assumptions (assigned to relevant rows).
_A1 = "Demand for D&F products is sustained and grows domestically and regionally"
_A2 = "Private sector and anchor partners continue to invest in the D&F value chain without cessation"
_A3 = "Skills, resources and networks acquired through SAWA convert to sustained employment and enterprise operation"

LOGFRAME_ROWS = [
    # ── Impact ────────────────────────────────────────────────────────────────
    {
        "indicator_code": "PI.1",
        "result_level": "Impact",
        "indicator_statement": "Number of financially disadvantaged young women and PWDs engaged in dignified and fulfilling work in the D&F sector by end of programme",
        "disaggregation": "By sex; PWD/non-PWD; D&F sub-sector (production/value-addition)",
        "baseline_value": "0",
        "target_annual": "500 (Y1)",
        "target_lop": "60,000",
        "means_of_verification": "Programme monitoring database; Annual outcome surveys; Partner progress reports",
        "frequency": "Annual",
        "responsible": "CEL MEAL",
        "critical_assumption": f"{_A1}; {_A3}",
    },
    # ── Output — Pillar I (Capacity) ──────────────────────────────────────────
    {
        "indicator_code": "PI.5",
        "result_level": "Output",
        "indicator_statement": "Number of young women and PWDs mobilised and enrolled in SAWA D&F value chain activities",
        "disaggregation": "By sex; PWD status; region; D&F entry point",
        "baseline_value": "0",
        "target_annual": "500 (Q1: 95; Q2–Q4: 135 each)",
        "target_lop": "—",
        "means_of_verification": "Enrolment registers; Mobilisation partner reports",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.6",
        "result_level": "Output",
        "indicator_statement": "Number of individuals completing accredited Business Development Services (BDS) training",
        "disaggregation": "By sex; PWD status; BDS module completed",
        "baseline_value": "0",
        "target_annual": "500",
        "target_lop": "—",
        "means_of_verification": "Training attendance registers; Certification records",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.7",
        "result_level": "Output",
        "indicator_statement": "Number of cooperative or producer association frameworks established or strengthened",
        "disaggregation": "By region; cooperative type; % women members",
        "baseline_value": "0",
        "target_annual": "25",
        "target_lop": "—",
        "means_of_verification": "Cooperative registration documents; Attendance and governance records",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.8",
        "result_level": "Output",
        "indicator_statement": "Number of individuals receiving gender-transformative training (participants and community champions)",
        "disaggregation": "By sex; role (participant/champion); region",
        "baseline_value": "0",
        "target_annual": "500",
        "target_lop": "—",
        "means_of_verification": "Training attendance registers; Post-training knowledge assessment",
        "frequency": "Quarterly",
        "responsible": "CEL MEAL",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.9",
        "result_level": "Output",
        "indicator_statement": "Number of individuals receiving safeguarding and PSEA awareness training",
        "disaggregation": "By sex; PWD status; partner organisation",
        "baseline_value": "0",
        "target_annual": "500",
        "target_lop": "—",
        "means_of_verification": "Training records; Safeguarding incident log",
        "frequency": "Quarterly",
        "responsible": "CEL MEAL",
        "critical_assumption": "—",
    },
    {
        "indicator_code": "PI.10",
        "result_level": "Output",
        "indicator_statement": "Number of PWD mentors identified, trained and matched with PWD programme participants",
        "disaggregation": "By disability type; sex of mentor; region",
        "baseline_value": "0",
        "target_annual": "8",
        "target_lop": "—",
        "means_of_verification": "Mentor registry; Match records; Mentor progress reports",
        "frequency": "Bi-annual",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.11",
        "result_level": "Output",
        "indicator_statement": "% of programme participants who are women",
        "disaggregation": "By training type; pillar",
        "baseline_value": "—",
        "target_annual": "≥60%",
        "target_lop": "≥60%",
        "means_of_verification": "Disaggregated enrolment and participation data",
        "frequency": "Quarterly",
        "responsible": "CEL MEAL",
        "critical_assumption": "—",
    },
    {
        "indicator_code": "PI.12",
        "result_level": "Output",
        "indicator_statement": "Number of training curricula adapted to include PWD-inclusive delivery methods and content",
        "disaggregation": "By pillar; disability type addressed",
        "baseline_value": "0",
        "target_annual": "4",
        "target_lop": "—",
        "means_of_verification": "Curriculum review documentation; Accessibility assessment reports",
        "frequency": "Annual",
        "responsible": "Programme Team",
        "critical_assumption": "—",
    },
    # ── Outcome — Employment & Enterprise Growth (Pillars II & III) ──────────
    # Outcome 1 (Employment): PII.R5, PIII.R1
    # Outcome 2 (Enterprise Growth): PII.R6, PII.R7, PIII.R2, PIII.R3
    {
        "indicator_code": "PII.R5",
        "result_level": "Outcome",
        "indicator_statement": "Number of D&F employment positions created for PWDs across all production sites (programme-wide)",
        "disaggregation": "By disability type; sex; production site; anchor partner",
        "baseline_value": "0",
        "target_annual": "8",
        "target_lop": "—",
        "means_of_verification": "Employment records; Partner payroll verification; Field spot-checks",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A2,
    },
    {
        "indicator_code": "PII.R6",
        "result_level": "Outcome",
        "indicator_statement": "Metric tonnes of fish produced by PWDs engaged in D&F production activities",
        "disaggregation": "By PWD type; sex; production site; fish species",
        "baseline_value": "0 MT",
        "target_annual": "9.26 MT",
        "target_lop": "—",
        "means_of_verification": "Production logs; Catch data records; Third-party verification",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": f"{_A1}; {_A2}",
    },
    {
        "indicator_code": "PII.R7",
        "result_level": "Outcome",
        "indicator_statement": "Revenue (USD) generated by PWDs employed in D&F production activities",
        "disaggregation": "By sex; disability type; production site",
        "baseline_value": "USD 0",
        "target_annual": "USD 16,667",
        "target_lop": "—",
        "means_of_verification": "Sales receipts; Partner financial records; Income survey",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A1,
    },
    {
        "indicator_code": "PIII.R1",
        "result_level": "Outcome",
        "indicator_statement": "Number of D&F employment positions created in value-addition activities (processing, trading, cold chain)",
        "disaggregation": "By sex; value-addition activity; anchor partner",
        "baseline_value": "0",
        "target_annual": "100",
        "target_lop": "—",
        "means_of_verification": "Employment records; Enterprise HR data; Field verification",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A2,
    },
    {
        "indicator_code": "PIII.R2",
        "result_level": "Outcome",
        "indicator_statement": "Metric tonnes of fish produced or traded through SAWA-supported value-addition channels",
        "disaggregation": "By value-addition type (processed/traded); partner; fish species",
        "baseline_value": "0 MT",
        "target_annual": "115.74 MT",
        "target_lop": "50,000 MT additional/year",
        "means_of_verification": "Trading and processing records; Market assessment data",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A1,
    },
    {
        "indicator_code": "PIII.R3",
        "result_level": "Outcome",
        "indicator_statement": "Revenue (USD) from fish value-added trading activities of SAWA-supported enterprises",
        "disaggregation": "By enterprise; sex of owner; trading route (domestic/export)",
        "baseline_value": "USD 0",
        "target_annual": "USD 208,333",
        "target_lop": "USD 90M additional/year",
        "means_of_verification": "Sales records; Market price monitoring; Financial audits",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A1,
    },
    # ── Output — Pillar III (Value Addition) ──────────────────────────────────
    {
        "indicator_code": "PIII.6",
        "result_level": "Output",
        "indicator_statement": "Number of formalised market linkages established between SAWA enterprises and buyers, aggregators or export channels",
        "disaggregation": "By linkage type (domestic/export); buyer sector; partner",
        "baseline_value": "0",
        "target_annual": "10",
        "target_lop": "—",
        "means_of_verification": "Signed agreements; MoU registry; Market linkage tracking log",
        "frequency": "Bi-annual",
        "responsible": "Programme Team",
        "critical_assumption": f"{_A1}; {_A2}",
    },
    # ── Output — Pillar IV (Ecosystem) ────────────────────────────────────────
    {
        "indicator_code": "PIV.1",
        "result_level": "Output",
        "indicator_statement": "Number of policy and regulatory engagements conducted at national and district level to improve D&F sector governance",
        "disaggregation": "By level (national/district); policy area; outcome (informational/committal)",
        "baseline_value": "0",
        "target_annual": "4",
        "target_lop": "—",
        "means_of_verification": "Meeting minutes; Policy brief dissemination records; MoU sign-off documents",
        "frequency": "Bi-annual",
        "responsible": "CEL MEAL",
        "critical_assumption": _A2,
    },
]

# ── Indicators master list (links logframe to data_points) ────────────────────
INDICATORS: list[dict] = []

# ── Module C: Data Collection Plan ────────────────────────────────────────────
# 11 SAWA baseline instruments.  collection_month/year = first scheduled event;
# the calendar view expands frequency → all events over a rolling 2-year window.
# Quarterly instruments start Feb → cycle hits May, Aug, Nov, Feb …
# Bi-annual instruments start May → cycle hits Nov, May, Nov, May …
# This produces 8 instruments landing in May 2027, demonstrating the overload.
# ── Module D: Raw Data Analysis ───────────────────────────────────────────────
# 20 rows — one per logframe indicator.  indicator_code is the link key;
# seed_sawa.py resolves it to logframe_row_id.
# baseline_collected = 'N' for all: SAWA has no baselines collected yet.
# trigger_value = the threshold below which the indicator is 'not on track'.
RAW_DATA_ANALYSIS: list[dict] = [
    # ── Impact ────────────────────────────────────────────────────────────────
    {
        "indicator_code": "PI.1",
        "data_type": "Performance",
        "target_value": "500 (Y1); 60,000 (LoP)",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 participants engaged in D&F work by Y1 year-end; "
            "LoP trajectory off track"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    # ── Output — Pillar I ─────────────────────────────────────────────────────
    {
        "indicator_code": "PI.5",
        "data_type": "Process",
        "target_value": "500 Y1 (Q1: 95; Q2–Q4: 135 each)",
        "trigger_value": "95",
        "problem_definition": (
            "Q1 mobilisation below 95; Y1 total of 500 at risk; "
            "pipeline for subsequent quarters insufficient"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.6",
        "data_type": "Process",
        "target_value": "500 (Y1)",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 individuals completing accredited BDS training by year-end"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.7",
        "data_type": "Process",
        "target_value": "25 (Y1)",
        "trigger_value": "25",
        "problem_definition": (
            "Fewer than 25 cooperative/producer association frameworks established or strengthened"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.8",
        "data_type": "Process",
        "target_value": "500 (Y1)",
        "trigger_value": "500",
        "problem_definition": (
            "Gender-transformative training coverage below 500; "
            "gender norm change outcomes at risk"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.9",
        "data_type": "Process",
        "target_value": "500 (Y1)",
        "trigger_value": "500",
        "problem_definition": (
            "Safeguarding/PSEA training below 500; duty of care risk materialises"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.10",
        "data_type": "Process",
        "target_value": "8 (Y1)",
        "trigger_value": "8",
        "problem_definition": (
            "Fewer than 8 PWD mentors identified, trained and matched; "
            "disability inclusion pathway not operational"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.11",
        "data_type": "Performance",
        "target_value": "≥60% (Y1)",
        "trigger_value": "60",
        "problem_definition": (
            "Women below 60% of total participants; programme gender-targeting commitment unmet"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.12",
        "data_type": "Process",
        "target_value": "4 (Y1)",
        "trigger_value": "4",
        "problem_definition": (
            "Fewer than 4 curricula adapted for PWD-inclusive delivery; "
            "training accessibility deficit"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    # ── Outcome — Employment & Enterprise Growth (Pillars II & III) ──────────
    # Outcome 1 (Employment): PII.R5, PIII.R1
    # Outcome 2 (Enterprise Growth): PII.R6, PII.R7, PIII.R2, PIII.R3
    {
        "indicator_code": "PII.R5",
        "data_type": "Performance",
        "target_value": "8 (Y1)",
        "trigger_value": "8",
        "problem_definition": (
            "Fewer than 8 D&F employment positions created for PWDs; "
            "disability-inclusive employment commitment unmet"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PII.R6",
        "data_type": "Performance",
        "target_value": "9.26 MT (Y1)",
        "trigger_value": "9.26",
        "problem_definition": (
            "Fish production by PWDs below 9.26 MT; Pillar II production targets off track"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PII.R7",
        "data_type": "Performance",
        "target_value": "USD 16,667 (Y1)",
        "trigger_value": "16667",
        "problem_definition": (
            "PWD revenue below USD 16,667; income impact for disability-inclusive employment "
            "not materialising"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PIII.R1",
        "data_type": "Performance",
        "target_value": "100 (Y1)",
        "trigger_value": "100",
        "problem_definition": (
            "Fewer than 100 value-addition jobs created; Pillar III employment target off track"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PIII.R2",
        "data_type": "Performance",
        "target_value": "115.74 MT (Y1); 50,000 MT/year (LoP)",
        "trigger_value": "115.74",
        "problem_definition": (
            "Fish volume through value-addition channels below 115.74 MT; "
            "processing and trading scale-up delayed"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PIII.R3",
        "data_type": "Performance",
        "target_value": "USD 208,333 (Y1); USD 90M/year (LoP)",
        "trigger_value": "208333",
        "problem_definition": (
            "Value-added trading revenue below USD 208,333; "
            "market integration not generating modelled returns"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    # ── Output — Pillar III (Value Addition) ─────────────────────────────────
    {
        "indicator_code": "PIII.6",
        "data_type": "Process",
        "target_value": "10 (Y1)",
        "trigger_value": "10",
        "problem_definition": (
            "Fewer than 10 formalised market linkages; value chain integration behind schedule"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    # ── Output — Pillar IV ────────────────────────────────────────────────────
    {
        "indicator_code": "PIV.1",
        "data_type": "Process",
        "target_value": "4 (Y1)",
        "trigger_value": "4",
        "problem_definition": (
            "Fewer than 4 policy and regulatory engagements completed; "
            "ecosystem enablement work behind schedule"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
]

# ── Module E: Kobo Form Mappings ──────────────────────────────────────────────
# 5 SAWA forms, 10 field-to-indicator rows.
# asset_uids are PLACEHOLDER values matching the forms described in the SAWA
# instrument set — replace with real UIDs from your KoboToolbox account.
# indicator_code is resolved to logframe_row_id by seed_sawa.py.
KOBO_FORM_MAPPINGS: list[dict] = [
    # ── Market / Field Visit Questionnaire ────────────────────────────────────
    {
        "asset_uid":       "aSAWAMktField2026xx",
        "kobo_form_name":  "Market/Field Visit Questionnaire",
        "kobo_field_name": "num_women_attended",
        "indicator_code":  "PI.1",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWAMktField2026xx",
        "kobo_form_name":  "Market/Field Visit Questionnaire",
        "kobo_field_name": "num_pwd_attended",
        "indicator_code":  "PII.R5",
        "transform":       "sum",
    },
    # ── SAWA Field Visit Markets ───────────────────────────────────────────────
    {
        "asset_uid":       "aSAWAFldMarkets2026x",
        "kobo_form_name":  "SAWA Field Visit Markets",
        "kobo_field_name": "new_linkage_established",
        "indicator_code":  "PIII.6",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWAFldMarkets2026x",
        "kobo_form_name":  "SAWA Field Visit Markets",
        "kobo_field_name": "fish_volume_mt",
        "indicator_code":  "PIII.R2",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWAFldMarkets2026x",
        "kobo_form_name":  "SAWA Field Visit Markets",
        "kobo_field_name": "revenue_usd",
        "indicator_code":  "PIII.R3",
        "transform":       "sum",
    },
    # ── Tool 2 — Financial Literacy ───────────────────────────────────────────
    {
        "asset_uid":       "aSAWATool2FinLit26xx",
        "kobo_form_name":  "Tool 2 Financial Literacy",
        "kobo_field_name": "score_total",
        "indicator_code":  "PI.6",
        "transform":       "latest",
    },
    {
        "asset_uid":       "aSAWATool2FinLit26xx",
        "kobo_form_name":  "Tool 2 Financial Literacy",
        "kobo_field_name": "participant_completed",
        "indicator_code":  "PI.5",
        "transform":       "count",
    },
    # ── Tool 3 — Governance Checklist ─────────────────────────────────────────
    {
        "asset_uid":       "aSAWATool3GovChk26xx",
        "kobo_form_name":  "Tool 3 Governance Checklist",
        "kobo_field_name": "cooperative_registered",
        "indicator_code":  "PI.7",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWATool3GovChk26xx",
        "kobo_form_name":  "Tool 3 Governance Checklist",
        "kobo_field_name": "governance_score",
        "indicator_code":  "PI.7",
        "transform":       "latest",
    },
    # ── PMU Pre/Post Test ─────────────────────────────────────────────────────
    {
        "asset_uid":       "aSAWAPMUPrePost26xxx",
        "kobo_form_name":  "PMU Pre/Post Test",
        "kobo_field_name": "post_test_score",
        "indicator_code":  "PI.8",
        "transform":       "mean",
    },
]

# ── Module F: Review Protocols ────────────────────────────────────────────────
# 7 fixed rows — one per data_type.  next_scheduled_date is the FIRST scheduled
# review; seed_sawa.py inserts these; the UI auto-advances the date after each
# logged review.  Three protocols are seeded as OVERDUE (date < 2026-09-17) to
# demonstrate the platform's red-flag overdue detection out of the box.
REVIEW_PROTOCOLS: list[dict] = [
    # ── Performance ───────────────────────────────────────────────────────────
    {
        "data_type":             "Performance",
        "review_scope":          (
            "All logframe indicators with quarterly data due this period — "
            "PI.1, PI.5, PI.6, PI.7, PI.8, PI.9, PI.10, PI.11, PI.12, "
            "PII.R5, PII.R6, PII.R7, PIII.R1, PIII.R2, PIII.R3, PIII.6, PIV.1"
        ),
        "existing_info_source":  "raw_data_analysis table, Module D; previous quarterly PIR",
        "actual_info_source":    (
            "Kobo sync (Module E) — Field Visit Markets form and Tool 2/3 completion counts; "
            "anchor partner progress reports; field visit verification notes"
        ),
        "issue_definition":      (
            "Any indicator where actual < trigger_value for two consecutive quarters; "
            "or any Q-indicator where no data has been collected by the end of the quarter"
        ),
        "review_frequency":      "Quarterly",
        "reviewer_role":         "MEAL Officer",
        "next_scheduled_date":   "2026-09-01",   # OVERDUE — demonstrate red flag
    },
    # ── Assumption ────────────────────────────────────────────────────────────
    {
        "data_type":             "Assumption",
        "review_scope":          (
            "The 3 stated SAWA ToC assumptions: (A1) demand for D&F products is "
            "sustained and grows; (A2) private sector and anchor partners continue "
            "to invest without cessation; (A3) skills, resources and networks "
            "acquired through SAWA convert to sustained employment"
        ),
        "existing_info_source":  (
            "ToC nodes in Module B; ToC assumption columns in logframe_rows; "
            "Programme Manager assumption-monitoring notes (quarterly)"
        ),
        "actual_info_source":    (
            "Anchor partner progress reports and milestone delivery trackers; "
            "PMU quarterly review minutes; Ghana Fisheries market-price data "
            "(A1 test); Labour market tracking panel (A3 test)"
        ),
        "issue_definition":      (
            "An assumption's own stated test is breached — e.g. anchor partner "
            "delivery below 70% of contracted milestones (A2 test); or D&F "
            "market price index falls >15% quarter-on-quarter (A1 test); "
            "or employment conversion rate <30% at 6-month follow-up (A3 test)"
        ),
        "review_frequency":      "Bi-annual",
        "reviewer_role":         "Programme Manager + MEAL Officer",
        "next_scheduled_date":   "2026-11-01",
    },
    # ── Stakeholder ───────────────────────────────────────────────────────────
    {
        "data_type":             "Stakeholder",
        "review_scope":          (
            "Partner delivery against Module A Level 1 (anchor partner commitments) "
            "and Level 2 (CEL Y1 delivery targets) — all 5 anchor partners: "
            "R&B Farms, AgroKings, Yedent/Naple Betta, Aglow Farms, NewAge Agric"
        ),
        "existing_info_source":  (
            "partner_targets table, Module A; signed MoUs and workplans; "
            "previous partner progress reports"
        ),
        "actual_info_source":    (
            "Partner progress reports submitted to CEL monthly; "
            "field verification visit notes by Partnerships Lead; "
            "financial records spot-check; employment register review"
        ),
        "issue_definition":      (
            "Any anchor partner delivering <80% of their Level 1 committed targets "
            "for the period; or a partner submitting no progress report for two "
            "consecutive months; or a safeguarding or labour-standards concern "
            "raised against a partner site"
        ),
        "review_frequency":      "Quarterly",
        "reviewer_role":         "Partnerships Lead",
        "next_scheduled_date":   "2026-09-10",   # OVERDUE — demonstrate red flag
    },
    # ── Process ───────────────────────────────────────────────────────────────
    {
        "data_type":             "Process",
        "review_scope":          (
            "Delivery milestones and activity completion rates against the SAWA "
            "implementation plan — training sessions delivered (PI.5/PI.6), "
            "Field Market visits completed, governance workshops run (PI.7), "
            "safeguarding training (PI.9), PWD curricula adapted (PI.12)"
        ),
        "existing_info_source":  (
            "Activity tracker in Module A (partner targets Levels 3–4); "
            "CEL Year 1 Consolidated Workplan; previous month's process log"
        ),
        "actual_info_source":    (
            "Field officer weekly activity reports; KoboToolbox Tool 2 (Financial "
            "Literacy) and Tool 3 (Governance Checklist) completion counts via "
            "Module E sync; training register summaries from Programme Team"
        ),
        "issue_definition":      (
            "Fewer than 80% of planned activities completed in the period; "
            "or two consecutive months below target on any output indicator "
            "(PI.5–PI.12); or a Field Market visit not completed as scheduled "
            "with no documented reason"
        ),
        "review_frequency":      "Monthly",
        "reviewer_role":         "Programme Manager",
        "next_scheduled_date":   "2026-09-05",   # OVERDUE — demonstrate red flag
    },
    # ── Problem ───────────────────────────────────────────────────────────────
    {
        "data_type":             "Problem",
        "review_scope":          (
            "The five SAWA barrier categories tracked via the BARRIER_TRACKING "
            "instrument: (1) access to inputs, (2) market linkage, (3) financial "
            "literacy, (4) cooperative governance, (5) post-harvest loss — "
            "disaggregated by sex, PWD status and region"
        ),
        "existing_info_source":  (
            "BARRIER_TRACKING instrument data in Module C and dropout/non-participation "
            "records in Module D (data_type = Problem rows); previous quarterly "
            "barrier summary memo"
        ),
        "actual_info_source":    (
            "Kobo sync of Field Visit Markets form and Market/Field Visit "
            "Questionnaire (Module E); barrier narrative summaries from field "
            "officers; monthly safeguarding incident log; non-continuers "
            "interview data (Barrier Tracking instrument)"
        ),
        "issue_definition":      (
            "A new barrier type appearing in >20% of field reports in the period; "
            "or an existing barrier worsening two consecutive quarters; "
            "or any safeguarding/PSEA finding linked to a structural barrier "
            "(e.g. unsafe travel to training site)"
        ),
        "review_frequency":      "Quarterly",
        "reviewer_role":         "MEAL Officer + Programme Manager",
        "next_scheduled_date":   "2026-10-01",
    },
    # ── Solution ──────────────────────────────────────────────────────────────
    {
        "data_type":             "Solution",
        "review_scope":          (
            "Effectiveness of SAWA's 5 solution pathways: (1) financial literacy "
            "training (Tool 2 pre/post scores), (2) market linkage (PIII.6 "
            "formalised linkages), (3) cooperative governance (PI.7 frameworks), "
            "(4) disability inclusion pathway (PI.10 mentors), "
            "(5) post-harvest technology adoption at enterprise level"
        ),
        "existing_info_source":  (
            "Response-effectiveness indicator PIV.1 in Module D; "
            "Tool 2 and Tool 3 pre/post scores; PMU Pre/Post Test mean scores "
            "(PI.8); logframe actuals for PIII.6, PI.7, PI.10"
        ),
        "actual_info_source":    (
            "Kobo PMU Pre/Post Test results via Module E sync; field visit "
            "observations on solution adoption; partner progress reports on "
            "cooperative and market linkage outcomes; 6-month follow-up "
            "interview data on DFW composite score"
        ),
        "issue_definition":      (
            "Post-test scores show <10% improvement over pre-test for any "
            "training module (Tool 2 or PMU test); or adoption rate for a "
            "solution pathway below 30% at 6-month follow-up; "
            "or PIV.1 policy engagements delivering <50% of committed outcomes"
        ),
        "review_frequency":      "Bi-annual",
        "reviewer_role":         "Technical Lead + MEAL Officer",
        "next_scheduled_date":   "2027-01-01",
    },
    # ── Attribution ───────────────────────────────────────────────────────────
    {
        "data_type":             "Attribution",
        "review_scope":          (
            "Contribution analysis for the three primary SAWA outcomes: "
            "(1) income change — PI.2 transition rate and PIII.R3 revenue; "
            "(2) fish production volumes — PIII.R2 and PII.R6; "
            "(3) women's economic empowerment — PI.1 D&F engagement and PI.5 "
            "enrolment-to-employment conversion"
        ),
        "existing_info_source":  (
            "Logframe actuals in Module D; baseline values from INCOME and "
            "PARTICIPATION instruments (Module C); SAWA ToC and logframe "
            "target narrative (Module B); previous annual evaluation report"
        ),
        "actual_info_source":    (
            "Control-community comparison data from annual outcome survey; "
            "most-significant change stories collected at 6-month follow-up; "
            "external market price indices (Ghana Fisheries Commission data); "
            "anchor partner independently-verified production records"
        ),
        "issue_definition":      (
            "A plausible rival explanation (climate event, seasonal price shock, "
            "competing programme, policy change) can account for >50% of the "
            "observed change without SAWA's contribution; "
            "or the programme theory predicts an outcome that is absent in the "
            "data for two consecutive annual cycles"
        ),
        "review_frequency":      "Annual",
        "reviewer_role":         "Programme Manager + External Evaluator",
        "next_scheduled_date":   "2027-05-01",
    },
]

# ── Module G: Decision Reports ────────────────────────────────────────────────
# One fully worked example for PI.11 — a real SAWA data-quality finding
# investigated and closed before Q1 data collection began.
# This gives every new user a closed-loop example to learn the workflow from.
DECISION_REPORTS: list[dict] = [
    {
        "created_date":         "2026-08-01",
        "created_by":           "MEAL Officer",
        "indicator_code":       "PI.11",   # resolved to logframe_row_id in seed_sawa.py
        "target_value":         "≥90% (draft source table — since corrected)",
        "indicator_definition": (
            "% of programme participants who are women"
        ),
        "assumed_pattern": (
            "The source table records ≥90% as the PI.11 target, but the written "
            "indicator statement also references '≥500 members' — a headcount. "
            "A percentage and a headcount cannot both be correct targets for the "
            "same indicator. If the headcount figure is authoritative, applying "
            "≥90% as the monitoring threshold would systematically understate true "
            "engagement when actual women participants exceed 500 but fall below "
            "90% of total enrolment."
        ),
        "actual_value":         "Not yet collected — SAWA in baseline period (2026 Q1–Q2)",
        "review_category":      "Performance",
        "specific_focus_area":  "PI.11 target definition — % vs headcount conflict",
        "investigation_notes":  (
            "Reviewed SAWA Proposal (28 Nov 2025), CEL Year 1 Consolidated Workplan "
            "and SMART indicator revision notes (July 2026). The Proposal specifies a "
            "≥60% women participation rate — a percentage target, not a headcount. "
            "The ≥90% figure in the source table does not appear in any authoritative "
            "source document and has no documented origin. The '≥500 members' phrasing "
            "in the indicator statement appears to be a copy-paste error from PI.5 "
            "(enrolment headcount). All three figures are mutually inconsistent; "
            "the Proposal and SMART revision process were used to adjudicate."
        ),
        "key_finding": (
            "Confirmed: the written indicator statement ('% of programme participants "
            "who are women') and the Proposal target (≥60%) are authoritative, "
            "following SMART revision sign-off by Programme Manager on 25 July 2026. "
            "The ≥90% figure in the source table was a transcription error from a "
            "superseded draft logframe. The '≥500 members' phrasing was also erroneous "
            "— it belongs to PI.5, not PI.11. Correct target for all monitoring "
            "periods is ≥60%."
        ),
        "status": "Closed",
        "actions": [
            {
                "decision_maker":  "MEAL Officer",
                "action": (
                    "Correct PI.11 target in Logframe (Module B) to ≥60% and "
                    "remove the '≥500 members' headcount reference from the "
                    "indicator statement field"
                ),
                "action_due_date": "2026-08-15",
                "action_status":   "Resolved",
            }
        ],
    }
]

DATA_COLLECTION_PLAN: list[dict] = [
    {
        "stakeholder": "PWD participants",
        "indicator_statement": (
            "Number and % of enrolled participants who self-identify as PWD; "
            "disability type and functional limitation at enrolment"
        ),
        "data_points": "Disability status; disability type; sex; region; enrolment date",
        "rationale": (
            "Establishes the disability-disaggregated baseline for all subsequent data; "
            "confirms programme meets its PWD inclusion commitment (PII.R5 — 8 jobs Y1)"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "Enrolment",
        "integration_mechanism": "Enrolment screening form administered by mobilisation agent",
        "frequency": "Once",
        "collection_month": 2,
        "collection_year": 2026,
        "responsible_party": "Programme Team",
    },
    {
        "stakeholder": "All programme participants",
        "indicator_statement": (
            "Number attending training and BDS sessions per quarter, "
            "disaggregated by sex and disability status (PI.5, PI.6)"
        ),
        "data_points": "Name; sex; PWD status; session type; date; anchor partner",
        "rationale": (
            "Core output tracker for PI.5 (enrolment) and PI.6 (BDS completion); "
            "quarterly rhythm aligns with CEL Consolidated Workplan milestones"
        ),
        "instrument_status": "Existing",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "Training",
        "integration_mechanism": "Paper register scanned and uploaded to KoboToolbox",
        "frequency": "Quarterly",
        "collection_month": 2,
        "collection_year": 2026,
        "responsible_party": "Programme Team",
    },
    {
        "stakeholder": "Supported enterprises",
        "indicator_statement": (
            "Output volume per worker and revenue per worker at supported D&F enterprises "
            "compared to previous year (Outcome 2: PII.R6 / PIII.R2 — production volume LoP)"
        ),
        "data_points": "Enterprise ID; production volume; revenue; headcount; year",
        "rationale": (
            "Tracks Outcome 2 (Enterprise Growth) via PII.R6/PIII.R2 production volume; "
            "annual timing captures the full production cycle and avoids seasonal distortion"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "Annual review",
        "integration_mechanism": "Field verification visit and partner financial record review",
        "frequency": "Annual",
        "collection_month": 11,
        "collection_year": 2026,
        "responsible_party": "Partner MEAL",
    },
    {
        "stakeholder": "Young women participants",
        "indicator_statement": (
            "Self-efficacy score; agency over livelihood decisions; "
            "aspirations index — measured at baseline and 6-month follow-up"
        ),
        "data_points": "Agency score; aspiration scale; decision-making domain; sex; cohort",
        "rationale": (
            "Captures transformative gender outcomes invisible to economic metrics alone; "
            "bi-annual timing allows before/after comparison across one programme cycle"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "Enrolment",
        "integration_mechanism": "Face-to-face structured interview by trained CEL enumerator",
        "frequency": "Bi-annual",
        "collection_month": 5,
        "collection_year": 2026,
        "responsible_party": "CEL MEAL",
    },
    {
        "stakeholder": "Enterprises and value chain actors",
        "indicator_statement": (
            "Number of formalised market linkages; input access rates; "
            "active supplier relationships per enterprise (PIII.6)"
        ),
        "data_points": "Linkage type; buyer name; contract status; input source; enterprise ID",
        "rationale": (
            "Tracks PIII.6 and OP3 outputs; bi-annual cadence captures the mid-year "
            "market window and year-end stabilisation"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "6-month follow-up",
        "integration_mechanism": "Partner report verified by CEL field officer",
        "frequency": "Bi-annual",
        "collection_month": 5,
        "collection_year": 2026,
        "responsible_party": "Programme Team",
    },
    {
        "stakeholder": "Non-continuers and dropouts",
        "indicator_statement": (
            "Primary reason for dropout or non-participation; "
            "barrier category (financial / mobility / social norm / programme design)"
        ),
        "data_points": "Reason code; barrier category; sex; PWD status; dropout stage; region",
        "rationale": (
            "Essential for adaptive management; identifies where programme design needs "
            "adjustment before the next cohort; cannot be collected retrospectively"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "3-month check-in",
        "integration_mechanism": "Phone follow-up interview by Programme Team",
        "frequency": "Quarterly",
        "collection_month": 2,
        "collection_year": 2026,
        "responsible_party": "Programme Team",
    },
    {
        "stakeholder": "Programme participants (all)",
        "indicator_statement": (
            "DFW composite score: % reporting dignified conditions, "
            "fair pay, safety, and meaningful work (Impact statement metric)"
        ),
        "data_points": "DFW domain scores; safety rating; fair-pay perception; sex; cohort",
        "rationale": (
            "Directly measures the programme Impact statement — 'dignified and fulfilling work' "
            "— which cannot be inferred from production or revenue data alone"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "6-month follow-up",
        "integration_mechanism": "Structured interview at 6-month follow-up field visit",
        "frequency": "Annual",
        "collection_month": 5,
        "collection_year": 2026,
        "responsible_party": "CEL MEAL",
    },
    {
        "stakeholder": "Individual participants",
        "indicator_statement": (
            "Individual income from D&F activities per month; "
            "income change vs baseline (Outcome 1: PII.R5 / PIII.R1 — employment into D&F)"
        ),
        "data_points": "Monthly income (GHS); income source; weeks worked; sex; PWD status",
        "rationale": (
            "Tracks Outcome 1 (Employment) via PII.R5/PIII.R1; disaggregation by sex and PWD "
            "status enables equity analysis; bi-annual timing captures seasonal variation"
        ),
        "instrument_status": "Existing",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "6-month follow-up",
        "integration_mechanism": "Phone follow-up or field visit by CEL enumerator",
        "frequency": "Bi-annual",
        "collection_month": 5,
        "collection_year": 2026,
        "responsible_party": "CEL MEAL",
    },
    {
        "stakeholder": "SAWA-supported enterprises",
        "indicator_statement": (
            "Enterprise operational status 12 months after programme support ends; "
            "revenue sustainability vs programme-exit baseline (Outcome 2: PIII.R3)"
        ),
        "data_points": "Operational status; revenue vs exit-baseline; employment headcount; sex of owner",
        "rationale": (
            "Tests PIII.R3 enterprise growth persistence post-programme exit; "
            "NOT collectible at baseline — enterprises do not yet exist at enrolment stage"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "Annual review",
        "integration_mechanism": "Field verification visit and financial record review",
        "frequency": "Annual",
        "collection_month": 5,
        "collection_year": 2027,
        "responsible_party": "Partner MEAL",
    },
    {
        "stakeholder": "Production enterprises (fishpond operators)",
        "indicator_statement": (
            "Fish production volume (MT) per pond/site; yield per unit area; "
            "seasonal variation (Outcome 2: PIII.R2 — 50,000 MT additional/year LoP)"
        ),
        "data_points": "Site ID; volume (MT); area (ha); harvest cycle; fish species; anchor partner",
        "rationale": (
            "Direct measurement of PIII.R2 and long-term impact target; "
            "quarterly frequency captures all four production cycles in Ghana's fisheries calendar"
        ),
        "instrument_status": "Existing",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "3-month check-in",
        "integration_mechanism": "Partner production record review by Partner MEAL officer",
        "frequency": "Quarterly",
        "collection_month": 2,
        "collection_year": 2026,
        "responsible_party": "Partner MEAL",
    },
    {
        "stakeholder": "Programme staff and CEL management",
        "indicator_statement": (
            "% of planned activities completed on schedule; "
            "time from finding to adaptive management response"
        ),
        "data_points": "Activity completion rate; response lag (days); finding category; quarter",
        "rationale": (
            "Internal programme quality tracker; can only be measured once the programme "
            "is underway — NOT applicable at baseline or enrolment stage"
        ),
        "instrument_status": "New",
        "instrument_link": "https://kf.kobotoolbox.org/",
        "journey_step": "Annual review",
        "integration_mechanism": "Internal management review meeting (annual retreat)",
        "frequency": "Annual",
        "collection_month": 12,
        "collection_year": 2026,
        "responsible_party": "CEL MEAL",
    },
]
