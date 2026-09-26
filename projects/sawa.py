"""SAWA project constants — partners, indicators, targets, budget."""

PROJECT = {
    "name":         "SAWA",
    "donor":        "Mastercard Foundation",
    "budget_total": 39_810_000,   # USD 39.81M
    "start_date":   "2026-01-01",
    "end_date":     "2030-12-31",
}

# ── Partners ──────────────────────────────────────────────────────────────────
# Source: CEL's contribution to SAWA (Sep 2026) slides 02, 08-10.
PARTNERS = [
    # ── Anchor Partners — production delivery ─────────────────────────────────
    {"name": "AFRIGEM",
     "role": "Anchor Partner — anchors, mentors and peer circles",
     "tier": "Anchor"},
    {"name": "AgroKings",
     "role": "Anchor Partner — AquaRise groups and resident trainers",
     "tier": "Anchor"},
    {"name": "Naple Betta",
     "role": "Anchor Partner — production hubs, processors and women-led grill outlets",
     "tier": "Anchor"},
    {"name": "Aglow Aqua",
     "role": "Anchor Partner — community clusters and cooperatives",
     "tier": "Anchor"},
    {"name": "NewAge Agric",
     "role": "Anchor Partner — Adwenepa hubs, Urban/Rural Blue and Aqua Professionals",
     "tier": "Anchor"},
    # ── Lead Implementing Partner ──────────────────────────────────────────────
    {"name": "Agri-Impact Ltd (AIL)",
     "role": "Lead Implementing Partner — programme management and advocacy coordination",
     "tier": "Implementing"},
    # ── Technical Partners ─────────────────────────────────────────────────────
    {"name": "TechnoServe",
     "role": "Technical Partner — programme finance eligibility assessment",
     "tier": "Technical"},
    {"name": "Fisheries Commission",
     "role": "Technical Partner — regulatory guidance, compliance clinics and referrals",
     "tier": "Technical"},
    {"name": "CSIR",
     "role": "Technical Partner — product development, processing quality and value addition",
     "tier": "Technical"},
    {"name": "e-SAWA/KNUST",
     "role": "Technical Partner — SAWAtech digital tools, SAWA Voices and e-SAWA platform",
     "tier": "Technical"},
]

# ── Module A — Partner Target Funnel ──────────────────────────────────────────
# partner_name=None → Level 2/3/4 (programme-wide, no single partner).
PARTNER_TARGETS = [
    # ── Level 1: Anchor Partner Commitments (source: SAWA Proposal, 28 Nov 2025)
    # ── Life-of-programme targets (source: SAWA Proposal, 28 Nov 2025 + CEL deck Sep 2026)
    {"partner_name": "AFRIGEM",      "level": 1, "metric_label": "Women mentored (peer circles)", "target_value": "TBC", "unit": "participants", "time_basis": "Life of programme", "source_doc": "CEL's contribution to SAWA (Sep 2026)", "source_page": "08"},
    {"partner_name": "AgroKings",    "level": 1, "metric_label": "Young women & PWDs",  "target_value": "14,000", "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025",             "source_page": ""},
    {"partner_name": "Naple Betta",  "level": 1, "metric_label": "Jobs",                "target_value": "6,000",  "unit": "jobs",          "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025",             "source_page": ""},
    {"partner_name": "Naple Betta",  "level": 1, "metric_label": "SME graduates",       "target_value": "800",    "unit": "graduates",     "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025",             "source_page": ""},
    {"partner_name": "Naple Betta",  "level": 1, "metric_label": "Young women empowered", "target_value": "8,000", "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026", "source_page": ""},
    {"partner_name": "Aglow Aqua",   "level": 1, "metric_label": "Young women",         "target_value": "3,000",  "unit": "beneficiaries", "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025",             "source_page": ""},
    {"partner_name": "NewAge Agric", "level": 1, "metric_label": "Production jobs",     "target_value": "5,000",  "unit": "jobs",          "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025",             "source_page": ""},
    {"partner_name": "NewAge Agric", "level": 1, "metric_label": "Processing jobs",     "target_value": "1,000",  "unit": "jobs",          "time_basis": "Life of programme", "source_doc": "SAWA Proposal, 28 Nov 2025",             "source_page": ""},
    {"partner_name": "TechnoServe",  "level": 1, "metric_label": "Finance applications assessed", "target_value": "TBC", "unit": "applications", "time_basis": "Annual",     "source_doc": "CEL's contribution to SAWA (Sep 2026)", "source_page": "06"},

    # ── Level 1, Year 1 basis: confirmed partner Year 1 implementation plans
    # (source: partner Year 1 decks presented to AIL, Sep 2026 — NOT the same
    # time basis as the Life-of-Programme rows above; see the time-basis
    # warning banner and each card's "YR 1" badge before comparing the two.)
    {"partner_name": "AgroKings",   "level": 1, "metric_label": "Young women",           "target_value": "2,650", "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "AgroKings SAWA Year 1 Implementation Plan, Sep 2026",   "source_page": ""},
    {"partner_name": "AgroKings",   "level": 1, "metric_label": "Group enterprises",     "target_value": "800",   "unit": "enterprises",   "time_basis": "Year 1", "source_doc": "AgroKings SAWA Year 1 Implementation Plan, Sep 2026",   "source_page": ""},
    {"partner_name": "AgroKings",   "level": 1, "metric_label": "Operational roles",     "target_value": "400",   "unit": "roles",         "time_basis": "Year 1", "source_doc": "AgroKings SAWA Year 1 Implementation Plan, Sep 2026",   "source_page": ""},
    {"partner_name": "AgroKings",   "level": 1, "metric_label": "PWD reached",           "target_value": "170",   "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "AgroKings SAWA Year 1 Implementation Plan, Sep 2026",   "source_page": ""},
    {"partner_name": "Naple Betta", "level": 1, "metric_label": "Young women mobilised", "target_value": "1,850", "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026", "source_page": ""},
    {"partner_name": "Naple Betta", "level": 1, "metric_label": "Young women in work",   "target_value": "1,712", "unit": "YiW",           "time_basis": "Year 1", "source_doc": "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026", "source_page": ""},
    {"partner_name": "Naple Betta", "level": 1, "metric_label": "PWD in D&F work",       "target_value": "15",    "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "Naple Betta SAWA Year 1 Implementation Plan, Sep 2026", "source_page": ""},
    {"partner_name": "Aglow Aqua",  "level": 1, "metric_label": "Beneficiaries",         "target_value": "1,200", "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "Aglow Aqua SAWA Year 1 Implementation Plan, Sep 2026",  "source_page": ""},
    {"partner_name": "Aglow Aqua",  "level": 1, "metric_label": "PWD reached",           "target_value": "45",    "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "Aglow Aqua SAWA Year 1 Implementation Plan, Sep 2026",  "source_page": ""},
    {"partner_name": "AFRIGEM",     "level": 1, "metric_label": "Young women",           "target_value": "1,000", "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "AFRIGEM SAWA Year 1 Implementation Plan, Sep 2026",      "source_page": ""},
    {"partner_name": "AFRIGEM",     "level": 1, "metric_label": "PWD reached",           "target_value": "50",    "unit": "beneficiaries", "time_basis": "Year 1", "source_doc": "AFRIGEM SAWA Year 1 Implementation Plan, Sep 2026",      "source_page": ""},

    # ── Level 2: CEL Year 1 Delivery — Jul 2026–Jun 2027 ─────────────────────
    # Sources: CEL Year 1 Consolidated Workplan + CEL's contribution to SAWA (Sep 2026) p.16
    {"partner_name": None, "level": 2, "metric_label": "Youth mobilised",                "target_value": "500",   "unit": "youth",        "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "Women receiving BDS",            "target_value": "500",   "unit": "participants", "time_basis": "Year 1", "source_doc": "CEL's contribution to SAWA (Sep 2026)",    "source_page": "16"},
    {"partner_name": None, "level": 2, "metric_label": "Women in coaching & mentorship (gender, financial and digital literacy)",                                       "target_value": "500", "unit": "participants",                                "time_basis": "Year 1", "source_doc": "CEL's contribution to SAWA (Sep 2026)", "source_page": "05"},
    {"partner_name": None, "level": 2, "metric_label": "WAN forum engagements (awareness campaigns/road shows, institutionalize occupational health standards)", "target_value": "500", "unit": "engagements, campaigns/roadshows, sites/partners covered", "time_basis": "Year 1", "source_doc": "CEL's contribution to SAWA (Sep 2026)", "source_page": "16"},
    {"partner_name": None, "level": 2, "metric_label": "Women-led cooperatives/clusters strengthened (focal persons on GALS & EMAP)",                           "target_value": "25",  "unit": "cooperatives, focal persons",                             "time_basis": "Year 1", "source_doc": "CEL's contribution to SAWA (Sep 2026)", "source_page": "16"},
    {"partner_name": None, "level": 2, "metric_label": "Gender-transformative trained",  "target_value": "500",   "unit": "participants", "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "Safeguarding trained",           "target_value": "500",   "unit": "participants", "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 2, "metric_label": "PWD mentors identified",         "target_value": "8",     "unit": "mentors",      "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},

    # ── Level 3: Year 1 Results
    {"partner_name": None, "level": 3, "metric_label": "PIII.R1  D&F jobs (value addition)",       "target_value": "100",     "unit": "jobs",    "time_basis": "Year 1", "source_doc": "CEL's contribution to SAWA (Sep 2026)",    "source_page": "16"},
    {"partner_name": None, "level": 3, "metric_label": "PII.R5   D&F jobs (PWD, programme-wide)",  "target_value": "8",       "unit": "jobs",    "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "PII.R6   Fish produced by PWDs in D&F",    "target_value": "9 MT",    "unit": "MT",      "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "PII.R7   Revenue, PWDs in D&F",            "target_value": "16,667",  "unit": "USD",     "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "PIII.R2  Fish produced/traded",            "target_value": "115.74",  "unit": "MT",      "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},
    {"partner_name": None, "level": 3, "metric_label": "PIII.R3  Revenue, value-added trading",    "target_value": "208,333", "unit": "USD",     "time_basis": "Year 1", "source_doc": "CEL Year 1 Consolidated Workplan",         "source_page": ""},

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
# ── Module B: Theory of Change nodes — SAWA Proposal (28 Nov 2025) faithful ──
# source_verified=True  → content sourced verbatim or paraphrased from proposal
# source_verified=False → CEL operational addition absent from the proposal
TOC_NODES = [
    # ── Impact ────────────────────────────────────────────────────────────────
    {
        "key": "impact", "parent_key": None, "level": "Impact",
        "source_verified": True,
        "source_note": (
            "Impact statement verbatim from SAWA Proposal ToC s3.2. The four "
            "measurement commitments are sourced with explicit targets but "
            "carry no formal Pl.x-style indicator ID."
        ),
        "statement": (
            "Over 60,000 financially disadvantaged young women and persons with "
            "disabilities are engaged in dignified and fulfilling work across "
            "the aquaculture value chain, resulting in economic empowerment, "
            "resilience and poverty reduction at both individual and community "
            "levels.\n\n"
            "D&F WORK ≥ 86% · PRODUCTION 50,000 MT/yr · "
            "INCOME increase vs baseline · PWD INCLUSION staged ramp "
            "1%→3%→5%"
        ),
    },
    # ── Outcomes ──────────────────────────────────────────────────────────────
    {
        "key": "outcome1", "parent_key": "impact", "level": "Outcome",
        "source_verified": True,
        "source_note": "Proposal heading, s3.9 Outcome 1.",
        "statement": (
            "Transition into self and wage employment.\n\n"
            "Plll.R1 (≥100 D&F jobs, value addition) · "
            "Pll.R5 (8 D&F jobs, PWDs)"
        ),
    },
    {
        "key": "outcome2", "parent_key": "impact", "level": "Outcome",
        "source_verified": True,
        "source_note": "Proposal heading, s3.9 Outcome 2.",
        "statement": (
            "Improved practices drive sustainable enterprise growth.\n\n"
            "Pll.R6/Pll.R7 · Plll.R2/Plll.R3 · PRODUCTIVITY "
            "(≥30% yield improvement) · ENTERPRISE CREATION "
            "(≥70% survival at 12mo) · INCOME"
        ),
    },
    {
        "key": "outcome3", "parent_key": "impact", "level": "Outcome",
        "source_verified": True,
        "source_note": (
            "CORRECTED from a previous 'climate-resilient' version that does "
            "not appear in the source proposal and is not tested by either "
            "indicator below it. This is the proposal's actual Outcome 3 "
            "heading, s3.9."
        ),
        "statement": (
            "Resilience, agency and market position.\n\n"
            "MINDSET & AGENCY (validated self-efficacy scale) · "
            "INPUT & MARKET LINKAGE (≥60% of cohort within 6 months)"
        ),
    },
    # ── Intermediate Outcomes ─────────────────────────────────────────────────
    # NOT in the source proposal — absent from SAWA Proposal (28 Nov 2025).
    # Kept as CEL operational additions to give IO1.1/IO2.1/IO3.1 a tree home.
    {
        "key": "io1", "parent_key": "outcome1", "level": "Intermediate Outcome",
        "source_verified": False,
        "source_note": (
            "This entire tier is absent from the SAWA Proposal (28 Nov 2025), "
            "which runs Impact → Outcome → Output directly. Included "
            "here as a CEL operational addition. IO1.1 is proposed, not approved."
        ),
        "statement": (
            "Young women and PWDs have the skills, confidence, networks and "
            "initial resources to enter and succeed in D&F work.\n\n"
            "IO1.1 (proposed) · MINDSET_AND_AGENCY · Pl.11 · Pl.12a · Pl.12b"
        ),
    },
    {
        "key": "io2", "parent_key": "outcome2", "level": "Intermediate Outcome",
        "source_verified": False,
        "source_note": (
            "Not in the source proposal. IO2.1 is proposed, not approved. "
            "'Inclusive hiring practices' has no indicator anywhere."
        ),
        "statement": (
            "Anchor partner enterprises scale production and value addition "
            "with inclusive hiring practices and strengthened market linkages.\n\n"
            "IO2.1 (proposed)"
        ),
    },
    {
        "key": "io3", "parent_key": "outcome3", "level": "Intermediate Outcome",
        "source_verified": False,
        "source_note": (
            "Not in the source proposal. IO3.1 is proposed, not approved. "
            "'Private investment catalysed' has no indicator anywhere."
        ),
        "statement": (
            "The D&F sector ecosystem — policy, private investment and "
            "coordination — actively enables inclusive and sustainable "
            "enterprise growth.\n\nIO3.1 (proposed)"
        ),
    },
    # ── Outputs — proposal's actual Output 01-04 headings (s3.9) ─────────────
    {
        "key": "op1", "parent_key": "io1", "level": "Output",
        "source_verified": True,
        "source_note": "Proposal's actual Output 01, s3.9.",
        "statement": (
            "OUTPUT 01 · Inclusive, safeguarded participation.\n\n"
            "Pl.9 (25 GYSI focal persons, GALS+EMAP ToT) · "
            "Pl.13 (8 PWD peer mentors) · Pl.19 (≥500 gender-transformative "
            "training) · Pl.20 (≥500 safeguarding-trained) · "
            "Pl.22 (3 campaigns) · Pl.23 (2 sites certified) · SAFEGUARDING"
        ),
    },
    {
        "key": "op2", "parent_key": "io2", "level": "Output",
        "source_verified": True,
        "source_note": (
            "CORRECTED. Previously labelled 'Production: investment in fishpond "
            "and aquaculture facilities' — that investment is anchor-partner "
            "co-investment (see Inputs), not a CEL output. This is the "
            "proposal's actual Output 02, s3.9."
        ),
        "statement": (
            "OUTPUT 02 · Enrolled and skilled cohort.\n\n"
            "Pl.1 (≥500 enrolled, ≥5% PWDs) · Pl.3 (≥500 BDS-trained) · "
            "PlV.5 (≥500 E-SAWA digital literacy) · PARTICIPATION "
            "(100% disaggregated by month 9)"
        ),
    },
    {
        "key": "op3", "parent_key": "io2", "level": "Output",
        "source_verified": True,
        "source_note": (
            "CORRECTED. Previously labelled 'Value Addition: fish processing... "
            "cold-chain and storage established' — no indicator measures "
            "cold-chain/storage. This is the proposal's actual Output 03, s3.9: "
            "cooperative organisation, not physical infrastructure."
        ),
        "statement": (
            "OUTPUT 03 · Organized women-led enterprises.\n\n"
            "Pl.17 (≥500 cooperative development package) · "
            "Pl.18 (25 governance frameworks adopted) · "
            "Plll.6 (25 cooperatives established) — "
            "Pl.18 and Plll.6 track the same 25 entities, report against one register."
        ),
    },
    {
        "key": "op4", "parent_key": "io3", "level": "Output",
        "source_verified": True,
        "source_note": (
            "CORRECTED. Previously labelled 'Policy and regulatory engagement... "
            "private-sector investment catalysed; MoUs' — neither has an "
            "indicator. This is the proposal's actual Output 04, s3.9. "
            "'Investment catalysed' and 'MoUs' remain genuinely unmeasured "
            "claims even in this corrected version."
        ),
        "statement": (
            "OUTPUT 04 · Functional networks and ecosystem.\n\n"
            "Pl.11 (≥500 WAN members, ≥2 forums) · "
            "Pl.12a (1 national bootcamp) · Pl.12b (1 inter-zonal exchange) · "
            "STAKEHOLDER & COORDINATION (zero double-counting registry check)"
        ),
    },
    # ── Activities — by pillar (source: proposal s3.3) ────────────────────────
    {
        "key": "act1", "parent_key": "op1", "level": "Activity",
        "source_verified": True, "source_note": None,
        "statement": (
            "Pillar 1 — Capacity building and inclusion: community entry and "
            "mobilization; enrolment and needs assessment; GALS/EMAP cycles with "
            "households; safeguarding training, awareness campaigns, site "
            "certification, accessibility audits, PWD mentor recruitment."
        ),
    },
    {
        "key": "act2", "parent_key": "op2", "level": "Activity",
        "source_verified": True, "source_note": None,
        "statement": (
            "Pillar 2 — Production and productivity: starter packs and land "
            "access; community hatcheries and feed depots; hands-on training in "
            "fish handling, water quality, feed formulation, biosecurity."
        ),
    },
    {
        "key": "act3", "parent_key": "op3", "level": "Activity",
        "source_verified": True, "source_note": None,
        "statement": (
            "Pillar 3 — Value addition and markets: processing technology "
            "transfer with CSIR-FRI; two-tier certification with GSA/FDA; "
            "E-SAWA marketplace; micro/catalytic grants; cooperative formation."
        ),
    },
    {
        "key": "act4", "parent_key": "op4", "level": "Activity",
        "source_verified": True, "source_note": None,
        "statement": (
            "Pillar 4 — Ecosystem strengthening: establish WAN nationally and "
            "at community level; leadership bootcamps and exchange visits; "
            "institutional strengthening via the ISP; policy briefs and donor "
            "coordination."
        ),
    },
    # ── Inputs — proposal's fourfold breakdown ────────────────────────────────
    {
        "key": "input_finance", "parent_key": "act2", "level": "Input",
        "source_verified": True, "source_note": None,
        "statement": (
            "Finance: USD 39.81M total (Pillar II 26.78M · III 7.27M · "
            "I 2.41M · IV 0.82M · delivery fee 2.58M). Micro-grants ≤$800, "
            "catalytic ≤$8,000, SME facility ≤$16,000. Starter packs "
            "$1,000–$1,400."
        ),
    },
    {
        "key": "input_partners", "parent_key": "act3", "level": "Input",
        "source_verified": True, "source_note": None,
        "statement": (
            "Partners: Consortium — Agri-Impact (lead), Fisheries Commission, "
            "CEL, TechnoServe, R&B Farms, NewAge Agric, Agro Kings. Anchors — "
            "R&B, AgroKings, Yedent, NewAge, Aglow. Specialists — KNUST, "
            "CSIR/CSIR-FRI, Institutional Strengthening Partner."
        ),
    },
    {
        "key": "input_people", "parent_key": "act1", "level": "Input",
        "source_verified": True, "source_note": None,
        "statement": (
            "People & systems: full-time GYSI officer in every implementing "
            "partner; safeguarding focal persons; zonal coordinators; field "
            "enumerators; MIS/HAMIS registry."
        ),
    },
    {
        "key": "input_instruments", "parent_key": "act4", "level": "Input",
        "source_verified": True, "source_note": None,
        "statement": (
            "Instruments & standards: HAPPY D&F instrument applied verbatim; "
            "validated agency/self-efficacy scales; GALS and EMAP curricula; "
            "PWD toolkit; Good Aquaculture Practices; two-tier certification "
            "pathway."
        ),
    },
]

# ── Module B: Logframe rows ───────────────────────────────────────────────────
# Three stated SAWA ToC assumptions (assigned to relevant rows).
_A1 = "Demand for D&F products is sustained and grows domestically and regionally"
_A2 = "Private sector and anchor partners continue to invest in the D&F value chain without cessation"
_A3 = "Skills, resources and networks acquired through SAWA convert to sustained employment and enterprise operation"

LOGFRAME_ROWS = [
    # ── Impact (Programme-wide LoP target) ────────────────────────────────────
    {
        "indicator_code": "LoP.1",
        "result_level": "Impact",
        "indicator_statement": (
            "Number of financially disadvantaged young women and PWDs engaged in "
            "dignified and fulfilling work across the aquaculture value chain"
        ),
        "disaggregation": "By sex; PWD/non-PWD; D&F sub-sector (production/value-addition)",
        "baseline_value": "0",
        "target_annual": "500 (Y1 pathway target)",
        "target_lop": "60,000",
        "means_of_verification": "Programme monitoring database; Annual outcome surveys; Partner progress reports",
        "frequency": "Annual",
        "responsible": "CEL MEAL",
        "critical_assumption": f"{_A1}; {_A3}",
    },
    # ── Output — Pillar I: Develop Inclusive Young Women-Centred Capacities ──
    {
        "indicator_code": "PI.1",
        "result_level": "Output",
        "indicator_statement": (
            "Number of young women and PWDs mobilised, sensitised and enrolled in "
            "SAWA D&F value-chain activities"
        ),
        "disaggregation": "By sex; PWD status; region; anchor partner; D&F entry point",
        "baseline_value": "0",
        "target_annual": "500 (Q1: 95; Q2: 135; Q3: 135; Q4: 135)",
        "target_lop": "—",
        "means_of_verification": "Enrolment registers; Mobilisation partner reports; KoboToolbox Tool 2",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.3",
        "result_level": "Output",
        "indicator_statement": (
            "Number of young women and PWDs completing Business Development Services (BDS) training "
            "(entrepreneurship, new business support)"
        ),
        "disaggregation": "By sex; PWD status; BDS module; anchor partner",
        "baseline_value": "0",
        "target_annual": "500 (Q1: 95; Q2: 135; Q3: 135; Q4: 135)",
        "target_lop": "—",
        "means_of_verification": "Training attendance registers; BDS completion records; KoboToolbox Tool 2",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.9",
        "result_level": "Output",
        "indicator_statement": (
            "Number of GYSI focal persons trained in GALS and EMAP (Training of Trainers model, "
            "per implementing partner)"
        ),
        "disaggregation": "By partner organisation; region; sex",
        "baseline_value": "0",
        "target_annual": "25 (Q3: 15; Q4: 10)",
        "target_lop": "—",
        "means_of_verification": "Training completion certificates; Focal person registry; Partner reports",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.11",
        "result_level": "Output",
        "indicator_statement": (
            "Number of women engaged in leadership and mentorship forums under the "
            "Women in Aquaculture Network (WAN)"
        ),
        "disaggregation": "By region; forum type; PWD/non-PWD",
        "baseline_value": "0",
        "target_annual": "500 (Q3: 300; Q4: 200)",
        "target_lop": "—",
        "means_of_verification": "WAN attendance registers; Forum reports; CEL field officer notes",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.12",
        "result_level": "Output",
        "indicator_statement": (
            "Number of leadership bootcamps and inter-zonal exchange visits "
            "organised under the Women in Aquaculture Network (WAN)"
        ),
        "disaggregation": "By event type (bootcamp/exchange); region",
        "baseline_value": "0",
        "target_annual": "1 (Q3: 1)",
        "target_lop": "—",
        "means_of_verification": "Event reports; Attendance lists; CEL field officer notes",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.13",
        "result_level": "Output",
        "indicator_statement": (
            "Number of young female PWDs identified as peer mentors and matched "
            "with PWD programme participants"
        ),
        "disaggregation": "By disability type; region; anchor partner",
        "baseline_value": "0",
        "target_annual": "8 (Q1: 1; Q2: 2; Q3: 2; Q4: 3)",
        "target_lop": "—",
        "means_of_verification": "Mentor registry; Match records; Field verification notes",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.17",
        "result_level": "Output",
        "indicator_statement": (
            "Number of women in women-led cooperatives/clusters receiving gender training, "
            "financial literacy and business mentoring"
        ),
        "disaggregation": "By sex; cooperative; region; training module",
        "baseline_value": "0",
        "target_annual": "500 (Q2: 150; Q3: 150; Q4: 200)",
        "target_lop": "—",
        "means_of_verification": "Training registers; Cooperative membership records; Partner reports",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.18",
        "result_level": "Output",
        "indicator_statement": (
            "Number of gender-responsive governance frameworks adopted by "
            "women-led cooperatives/clusters"
        ),
        "disaggregation": "By cooperative/cluster; region; governance framework type",
        "baseline_value": "0",
        "target_annual": "25 (Q3: 15; Q4: 10)",
        "target_lop": "—",
        "means_of_verification": "Signed governance documents; KoboToolbox Tool 3 Governance Checklist; Field verification",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.19",
        "result_level": "Output",
        "indicator_statement": (
            "Number of persons (participants and community champions) receiving "
            "gender-transformative training"
        ),
        "disaggregation": "By sex; role (participant/champion); anchor partner; region",
        "baseline_value": "0",
        "target_annual": "500 (Q2: 150; Q3: 150; Q4: 200)",
        "target_lop": "—",
        "means_of_verification": "Training attendance registers; Post-training knowledge assessment records",
        "frequency": "Quarterly",
        "responsible": "CEL MEAL",
        "critical_assumption": _A3,
    },
    {
        "indicator_code": "PI.20",
        "result_level": "Output",
        "indicator_statement": (
            "Number of young women trained to identify and respond to safeguarding "
            "issues (PSEA awareness)"
        ),
        "disaggregation": "By sex; PWD status; partner organisation; region",
        "baseline_value": "0",
        "target_annual": "500 (Q2: 150; Q3: 150; Q4: 200)",
        "target_lop": "—",
        "means_of_verification": "Training records; Safeguarding incident log; CEL safeguarding officer reports",
        "frequency": "Quarterly",
        "responsible": "CEL MEAL",
        "critical_assumption": "—",
    },
    {
        "indicator_code": "PI.22",
        "result_level": "Output",
        "indicator_statement": (
            "Number of safeguarding awareness campaigns and roadshows undertaken "
            "in SAWA intervention communities"
        ),
        "disaggregation": "By community; region; type (campaign/roadshow)",
        "baseline_value": "0",
        "target_annual": "3 (Q4: 3)",
        "target_lop": "—",
        "means_of_verification": "Campaign reports; Attendance records; Community feedback forms",
        "frequency": "Quarterly",
        "responsible": "CEL MEAL",
        "critical_assumption": "—",
    },
    {
        "indicator_code": "PI.23",
        "result_level": "Output",
        "indicator_statement": (
            "Number of programme sites/partners with institutionalised safeguarding "
            "and occupational health standards"
        ),
        "disaggregation": "By partner organisation; site type (training hub/pond/depot)",
        "baseline_value": "0",
        "target_annual": "2 (Q4: 2)",
        "target_lop": "—",
        "means_of_verification": "Site certification documentation; Safeguarding policy adoption records",
        "frequency": "Annual",
        "responsible": "CEL MEAL",
        "critical_assumption": "—",
    },
    # ── Output — Pillar IV (Ecosystem / Digital Literacy) ────────────────────
    {
        "indicator_code": "PIV.5",
        "result_level": "Output",
        "indicator_statement": (
            "Number of young women receiving E-SAWA digital literacy training, "
            "mentorship and digital entrepreneurship workshops"
        ),
        "disaggregation": "By region; anchor partner; workshop type",
        "baseline_value": "0",
        "target_annual": "500 (Q2: 150; Q3: 150; Q4: 200)",
        "target_lop": "—",
        "means_of_verification": "Training attendance registers; E-SAWA platform enrolment data",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": _A3,
    },
    # ── Outcome 1 (Employment) — Pillars II & III ────────────────────────────
    {
        "indicator_code": "PII.R5",
        "result_level": "Outcome",
        "indicator_statement": (
            "Number of Persons with Disabilities (PWDs) accessing D&F in the Aquaculture "
            "value chain — programme-wide (Young Women in Work, YiW)"
        ),
        "disaggregation": "By disability type; sex; production site; anchor partner",
        "baseline_value": "0",
        "target_annual": "8 (Q1: 1; Q2: 2; Q3: 2; Q4: 3)",
        "target_lop": "—",
        "means_of_verification": "Employment records; Partner payroll verification; Field spot-checks; PWD registry",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A2,
    },
    {
        "indicator_code": "PIII.R1",
        "result_level": "Outcome",
        "indicator_statement": (
            "Number of young women accessing D&F in Aquaculture Value Addition activities (YiW)"
        ),
        "disaggregation": "By sex; value-addition activity type; anchor partner",
        "baseline_value": "0",
        "target_annual": "100 (Q2: 40; Q3: 30; Q4: 30)",
        "target_lop": "—",
        "means_of_verification": "Employment and enterprise records; Field verification",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A2,
    },
    # ── Outcome 2 (Enterprise Growth) — Pillars II & III ────────────────────
    {
        "indicator_code": "PII.R6",
        "result_level": "Outcome",
        "indicator_statement": (
            "Quantity (MT) of fish produced by young women PWDs accessing D&F "
            "in the Aquaculture value chain"
        ),
        "disaggregation": "By PWD type; sex; production site; fish species",
        "baseline_value": "0 MT",
        "target_annual": "9 MT (Q1: 1; Q2: 2; Q3: 2; Q4: 3)",
        "target_lop": "—",
        "means_of_verification": "Production logs; Catch data records; Third-party verification",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": f"{_A1}; {_A2}",
    },
    {
        "indicator_code": "PII.R7",
        "result_level": "Outcome",
        "indicator_statement": (
            "Revenue (USD) generated by young women PWDs accessing D&F "
            "in the Aquaculture value chain"
        ),
        "disaggregation": "By sex; disability type; production site",
        "baseline_value": "USD 0",
        "target_annual": "USD 16,667 (Q1: $2,083; Q2: $4,167; Q3: $4,167; Q4: $6,250)",
        "target_lop": "—",
        "means_of_verification": "Sales receipts; Partner financial records; Income survey",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A1,
    },
    {
        "indicator_code": "PIII.R2",
        "result_level": "Outcome",
        "indicator_statement": (
            "Quantity (MT) of fish produced or fish-related products traded through "
            "SAWA-supported value-addition channels"
        ),
        "disaggregation": "By value-addition type (processed/traded); partner; fish species",
        "baseline_value": "0 MT",
        "target_annual": "115.7 MT (Q2: 46.3; Q3: 34.7; Q4: 34.7)",
        "target_lop": "50,000 MT additional/year",
        "means_of_verification": "Trading and processing records; Market assessment data",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A1,
    },
    {
        "indicator_code": "PIII.R3",
        "result_level": "Outcome",
        "indicator_statement": (
            "Revenue (USD) generated from trading in Value Added Aquaculture products "
            "by SAWA-supported enterprises"
        ),
        "disaggregation": "By enterprise; sex of owner; trading route (domestic/export)",
        "baseline_value": "USD 0",
        "target_annual": "USD 208,333 (Q2: $83,333; Q3: $62,500; Q4: $62,500)",
        "target_lop": "USD 90M additional/year",
        "means_of_verification": "Sales records; Market price monitoring; Financial audits",
        "frequency": "Quarterly",
        "responsible": "Partner MEAL",
        "critical_assumption": _A1,
    },
    # ── Output — Pillar III (Value Addition / Cooperative Organisation) ───────
    {
        "indicator_code": "PIII.6",
        "result_level": "Output",
        "indicator_statement": (
            "Number of women-led cooperatives/clusters strengthened across the "
            "aquaculture value chain (established and registered entities)"
        ),
        "disaggregation": "By cooperative type; region; anchor partner",
        "baseline_value": "0",
        "target_annual": "25 (Q3: 15; Q4: 10)",
        "target_lop": "—",
        "means_of_verification": "Cooperative registration documents; Governance Checklist (Tool 3); Field verification",
        "frequency": "Quarterly",
        "responsible": "Programme Team",
        "critical_assumption": f"{_A1}; {_A2}",
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
# 21 rows — one per logframe indicator.  indicator_code is the link key;
# seed_sawa.py resolves it to logframe_row_id.
# baseline_collected = 'N' for all: SAWA has no baselines collected yet.
# trigger_value = annual Year 1 target (threshold below which not on track).
# Quarterly actuals populated from workplan breakdown.
RAW_DATA_ANALYSIS: list[dict] = [
    # ── Impact ────────────────────────────────────────────────────────────────
    {
        "indicator_code": "LoP.1",
        "data_type": "Performance",
        "target_value": "500 pathway (Y1); 60,000 (LoP)",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 participants on a D&F work pathway by Y1 year-end; "
            "LoP trajectory to 60,000 off track"
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
        "indicator_code": "PI.1",
        "data_type": "Process",
        "target_value": "500 (Y1) — Q1: 95; Q2: 135; Q3: 135; Q4: 135",
        "trigger_value": "500",
        "problem_definition": (
            "Q1 mobilisation below 95; Y1 total of 500 at risk; "
            "community entry and enrolment pipeline insufficient"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.3",
        "data_type": "Process",
        "target_value": "500 (Y1) — Q1: 95; Q2: 135; Q3: 135; Q4: 135",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 young women and PWDs completing BDS training by year-end; "
            "entrepreneurship pipeline below workplan"
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
        "target_value": "25 (Y1) — Q3: 15; Q4: 10",
        "trigger_value": "25",
        "problem_definition": (
            "Fewer than 25 GALS/EMAP focal persons trained; gender-transformative "
            "training cascade at risk across partner organisations"
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
        "data_type": "Process",
        "target_value": "500 (Y1) — Q3: 300; Q4: 200",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 women engaged in WAN leadership/mentorship forums; "
            "women's network not at operating scale"
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
        "target_value": "1 (Y1) — Q3: 1",
        "trigger_value": "1",
        "problem_definition": (
            "No WAN bootcamp or inter-zonal exchange visit organised in Y1; "
            "cross-learning and leadership development not initiated"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.13",
        "data_type": "Process",
        "target_value": "8 (Y1) — Q1: 1; Q2: 2; Q3: 2; Q4: 3",
        "trigger_value": "8",
        "problem_definition": (
            "Fewer than 8 PWD peer mentors identified and matched; "
            "disability inclusion support not in place for Y1 cohort"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.17",
        "data_type": "Process",
        "target_value": "500 (Y1) — Q2: 150; Q3: 150; Q4: 200",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 cooperative women receiving gender, financial literacy "
            "and business mentoring; cooperative development package not delivered at scale"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.18",
        "data_type": "Process",
        "target_value": "25 (Y1) — Q3: 15; Q4: 10",
        "trigger_value": "25",
        "problem_definition": (
            "Fewer than 25 gender-responsive governance frameworks adopted; "
            "cooperatives operating without formal governance structures"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.19",
        "data_type": "Process",
        "target_value": "500 (Y1) — Q2: 150; Q3: 150; Q4: 200",
        "trigger_value": "500",
        "problem_definition": (
            "Gender-transformative training coverage below 500; "
            "gender norm change and GALS household outcomes at risk"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.20",
        "data_type": "Process",
        "target_value": "500 (Y1) — Q2: 150; Q3: 150; Q4: 200",
        "trigger_value": "500",
        "problem_definition": (
            "Safeguarding/PSEA awareness training below 500; "
            "programme duty-of-care obligations not met"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.22",
        "data_type": "Process",
        "target_value": "3 (Y1) — Q4: 3",
        "trigger_value": "3",
        "problem_definition": (
            "Fewer than 3 safeguarding campaigns/roadshows completed; "
            "community awareness of safeguarding norms below target"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    {
        "indicator_code": "PI.23",
        "data_type": "Process",
        "target_value": "2 (Y1) — Q4: 2",
        "trigger_value": "2",
        "problem_definition": (
            "Fewer than 2 sites/partners with institutionalised safeguarding standards; "
            "occupational health compliance not formalised"
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
        "indicator_code": "PIV.5",
        "data_type": "Process",
        "target_value": "500 (Y1) — Q2: 150; Q3: 150; Q4: 200",
        "trigger_value": "500",
        "problem_definition": (
            "Fewer than 500 young women receiving E-SAWA digital literacy and "
            "mentorship workshops; digital entrepreneurship pathway not at scale"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    # ── Outcome 1 — Employment (Pillars II & III) ─────────────────────────────
    {
        "indicator_code": "PII.R5",
        "data_type": "Performance",
        "target_value": "8 (Y1) — Q1: 1; Q2: 2; Q3: 2; Q4: 3",
        "trigger_value": "8",
        "problem_definition": (
            "Fewer than 8 PWDs accessing D&F value chain by year-end; "
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
        "indicator_code": "PIII.R1",
        "data_type": "Performance",
        "target_value": "100 (Y1) — Q2: 40; Q3: 30; Q4: 30",
        "trigger_value": "100",
        "problem_definition": (
            "Fewer than 100 young women in value-addition jobs by year-end; "
            "Pillar III employment target off track"
        ),
        "baseline_collected": "N", "baseline_value": "",
        "actual_q1": "", "actual_q2": "", "actual_q3": "", "actual_q4": "",
        "actual_year": "",
        "indicator_status": "Data not collected yet",
        "action_status":    "No action needed - data reporting only",
        "action_description": "",
    },
    # ── Outcome 2 — Enterprise Growth (Pillars II & III) ─────────────────────
    {
        "indicator_code": "PII.R6",
        "data_type": "Performance",
        "target_value": "9 MT (Y1) — Q1: 1; Q2: 2; Q3: 2; Q4: 3",
        "trigger_value": "9",
        "problem_definition": (
            "Fish production by PWDs below 9 MT; Pillar II production target off track"
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
        "target_value": "USD 16,667 (Y1) — Q1: $2,083; Q2: $4,167; Q3: $4,167; Q4: $6,250",
        "trigger_value": "16667",
        "problem_definition": (
            "PWD revenue below USD 16,667; income impact from disability-inclusive "
            "employment not materialising at workplan rate"
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
        "target_value": "115.7 MT (Y1) — Q2: 46.3; Q3: 34.7; Q4: 34.7 | 50,000 MT/yr (LoP)",
        "trigger_value": "115.7",
        "problem_definition": (
            "Fish volume through value-addition channels below 115.7 MT; "
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
        "target_value": "USD 208,333 (Y1) — Q2: $83,333; Q3: $62,500; Q4: $62,500 | USD 90M/yr (LoP)",
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
    # ── Output — Pillar III (Cooperative Organisation) ────────────────────────
    {
        "indicator_code": "PIII.6",
        "data_type": "Process",
        "target_value": "25 (Y1) — Q3: 15; Q4: 10",
        "trigger_value": "25",
        "problem_definition": (
            "Fewer than 25 women-led cooperatives/clusters strengthened; "
            "cooperative organisation and governance targets behind workplan"
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
# 9 SAWA forms covering all 21 logframe indicators.
# asset_uids prefixed "aSAWA…PLACEHOLDER" — replace with real KoboToolbox
# asset UIDs once forms are created/published in your account.
# Forms 1-5 map to existing/adapted instruments; Forms 6-9 are new.
# indicator_code is resolved to logframe_row_id by seed_sawa.py.
KOBO_FORM_MAPPINGS: list[dict] = [
    # ── Form 1 — Mobilisation & Enrolment Register ────────────────────────────
    # Covers PI.1 (youth enrolled) and PII.R5 (PWD accessing D&F).
    {
        "asset_uid":       "aSAWAEnrolReg2026xxx",
        "kobo_form_name":  "Mobilisation & Enrolment Register",
        "kobo_field_name": "participant_enrolled",
        "indicator_code":  "PI.1",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWAEnrolReg2026xxx",
        "kobo_form_name":  "Mobilisation & Enrolment Register",
        "kobo_field_name": "pwd_enrolled",
        "indicator_code":  "PII.R5",
        "transform":       "count",
    },
    # ── Form 2 — Training Attendance Register ─────────────────────────────────
    # Covers PI.3, PI.9, PI.17, PI.19, PI.20, PIV.5.
    # Each submission = one training session; field values = headcount for that type.
    {
        "asset_uid":       "aSAWATrainAttnd2026x",
        "kobo_form_name":  "Training Attendance Register",
        "kobo_field_name": "bds_session_completed",
        "indicator_code":  "PI.3",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWATrainAttnd2026x",
        "kobo_form_name":  "Training Attendance Register",
        "kobo_field_name": "gals_focal_person_trained",
        "indicator_code":  "PI.9",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWATrainAttnd2026x",
        "kobo_form_name":  "Training Attendance Register",
        "kobo_field_name": "coop_training_attended",
        "indicator_code":  "PI.17",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWATrainAttnd2026x",
        "kobo_form_name":  "Training Attendance Register",
        "kobo_field_name": "gender_transformative_attended",
        "indicator_code":  "PI.19",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWATrainAttnd2026x",
        "kobo_form_name":  "Training Attendance Register",
        "kobo_field_name": "safeguarding_trained",
        "indicator_code":  "PI.20",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWATrainAttnd2026x",
        "kobo_form_name":  "Training Attendance Register",
        "kobo_field_name": "digital_literacy_attended",
        "indicator_code":  "PIV.5",
        "transform":       "sum",
    },
    # ── Form 3 — WAN Leadership Events Log ───────────────────────────────────
    # Covers PI.11 (women at WAN forums) and PI.12 (bootcamps/exchanges held).
    {
        "asset_uid":       "aSAWAWANEvents2026xx",
        "kobo_form_name":  "WAN Leadership Events Log",
        "kobo_field_name": "women_attended_forum",
        "indicator_code":  "PI.11",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWAWANEvents2026xx",
        "kobo_form_name":  "WAN Leadership Events Log",
        "kobo_field_name": "bootcamp_or_exchange_held",
        "indicator_code":  "PI.12",
        "transform":       "count",
    },
    # ── Form 4 — PWD Mentor Registry ─────────────────────────────────────────
    # Covers PI.13 (PWD peer mentors identified and matched).
    {
        "asset_uid":       "aSAWAPWDMentor2026xx",
        "kobo_form_name":  "PWD Mentor Registry",
        "kobo_field_name": "pwd_mentor_identified",
        "indicator_code":  "PI.13",
        "transform":       "count",
    },
    # ── Form 5 — Cooperative & Governance Registry (Tool 3) ──────────────────
    # Covers PIII.6 (cooperatives strengthened) and PI.18 (governance frameworks).
    {
        "asset_uid":       "aSAWATool3GovChk26xx",
        "kobo_form_name":  "Tool 3 Cooperative & Governance Registry",
        "kobo_field_name": "cooperative_registered",
        "indicator_code":  "PIII.6",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWATool3GovChk26xx",
        "kobo_form_name":  "Tool 3 Cooperative & Governance Registry",
        "kobo_field_name": "governance_framework_adopted",
        "indicator_code":  "PI.18",
        "transform":       "count",
    },
    # ── Form 6 — Safeguarding Monitoring Form ────────────────────────────────
    # Covers PI.22 (campaigns held) and PI.23 (sites certified).
    {
        "asset_uid":       "aSAWASafeguard2026xx",
        "kobo_form_name":  "Safeguarding Monitoring Form",
        "kobo_field_name": "campaign_roadshow_held",
        "indicator_code":  "PI.22",
        "transform":       "count",
    },
    {
        "asset_uid":       "aSAWASafeguard2026xx",
        "kobo_form_name":  "Safeguarding Monitoring Form",
        "kobo_field_name": "site_certified",
        "indicator_code":  "PI.23",
        "transform":       "count",
    },
    # ── Form 7 — PWD Production & Revenue Tracker ────────────────────────────
    # Covers PII.R6 (MT fish by PWDs) and PII.R7 (revenue by PWDs).
    {
        "asset_uid":       "aSAWAPWDProdRev2026x",
        "kobo_form_name":  "PWD Production & Revenue Tracker",
        "kobo_field_name": "fish_volume_mt_pwd",
        "indicator_code":  "PII.R6",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWAPWDProdRev2026x",
        "kobo_form_name":  "PWD Production & Revenue Tracker",
        "kobo_field_name": "revenue_usd_pwd",
        "indicator_code":  "PII.R7",
        "transform":       "sum",
    },
    # ── Form 8 — Value-Addition Enterprise Tracker ───────────────────────────
    # Covers PIII.R1 (value-addition jobs), PIII.R2 (MT value-added),
    # PIII.R3 (revenue value-added).
    {
        "asset_uid":       "aSAWAValueAdd2026xxx",
        "kobo_form_name":  "Value-Addition Enterprise Tracker",
        "kobo_field_name": "value_addition_jobs",
        "indicator_code":  "PIII.R1",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWAValueAdd2026xxx",
        "kobo_form_name":  "Value-Addition Enterprise Tracker",
        "kobo_field_name": "fish_volume_mt_va",
        "indicator_code":  "PIII.R2",
        "transform":       "sum",
    },
    {
        "asset_uid":       "aSAWAValueAdd2026xxx",
        "kobo_form_name":  "Value-Addition Enterprise Tracker",
        "kobo_field_name": "revenue_usd_va",
        "indicator_code":  "PIII.R3",
        "transform":       "sum",
    },
    # ── Form 9 — PMU Pre/Post Knowledge Test ─────────────────────────────────
    # Covers PI.19 quality check (mean post-test score for gender training).
    {
        "asset_uid":       "aSAWAPMUPrePost26xxx",
        "kobo_form_name":  "PMU Pre/Post Knowledge Test",
        "kobo_field_name": "post_test_score",
        "indicator_code":  "PI.19",
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
            "LoP.1; PI.1, PI.3, PI.9, PI.11, PI.12, PI.13, PI.17, PI.18, "
            "PI.19, PI.20, PI.22, PI.23; PIV.5; "
            "PII.R5, PII.R6, PII.R7; PIII.R1, PIII.R2, PIII.R3, PIII.6"
        ),
        "existing_info_source":  "raw_data_analysis table, Module D; previous quarterly PIR",
        "actual_info_source":    (
            "Kobo sync (Module E) — Mobilisation & Enrolment Register (PI.1/PII.R5); "
            "Training Attendance Register (PI.3/PI.9/PI.17/PI.19/PI.20/PIV.5); "
            "WAN Events Log (PI.11/PI.12); PWD Mentor Registry (PI.13); "
            "Cooperative & Governance Registry (PIII.6/PI.18); "
            "Safeguarding Monitoring Form (PI.22/PI.23); "
            "PWD Production & Revenue Tracker (PII.R6/PII.R7); "
            "Value-Addition Enterprise Tracker (PIII.R1/PIII.R2/PIII.R3)"
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
            "Year 1 Consolidated Workplan — mobilisation (PI.1), BDS training (PI.3), "
            "GALS focal persons (PI.9), safeguarding training (PI.20), "
            "governance frameworks (PI.18), cooperatives (PIII.6), "
            "PWD mentors (PI.13), WAN forums (PI.11)"
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
            "disaggregated by sex and disability status (PI.1, PI.3)"
        ),
        "data_points": "Name; sex; PWD status; session type; date; anchor partner",
        "rationale": (
            "Core output tracker for PI.1 (mobilisation/enrolment 500 Y1) and "
            "PI.3 (BDS completion 500 Y1); quarterly rhythm aligns with "
            "SAWA Y1 Consolidated Workplan milestones"
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
