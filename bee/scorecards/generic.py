"""Generic (large enterprise) scorecard: 111 points before bonuses.

Sources: S1 GG 36928 (Statements 100, 200, 500); S3/S4/S5 GG 42496 (2019).
Decisions D1 (MC = 19) and D2 (PP sub-minimum = 10.8) per rules-baseline.md.
"""

from bee.rules import Element, Indicator, Scorecard, SubMinimum

I = Indicator  # noqa: E741

OWNERSHIP = Element(
    "ownership",
    "Ownership",
    (
        I("100 2.1.1", "Voting rights: black people", 4, 25.0001),
        I("100 2.1.2", "Voting rights: black women", 2, 10),
        I("100 2.2.1", "Economic interest: black people", 4, 25),
        I("100 2.2.2", "Economic interest: black women", 2, 10),
        I("100 2.2.3", "Economic interest: designated groups/ESOP/co-ops", 3, 3),
        I("100 2.2.4", "New entrants", 2, 2),
        # Net Value graduation (Annexe 100(C)/(E)) is computed outside the engine; input is
        # the % of the Net Value target achieved.
        I("100 2.3.1", "Net Value", 8, 100, group="net_value"),
    ),
    priority=True,
)

MANAGEMENT = Element(
    "management",
    "Management Control",
    (
        I("200 2.1.1", "Black board members", 2, 50),
        I("200 2.1.2", "Black female board members", 1, 25),
        I("200 2.1.3", "Black executive directors", 2, 50),
        I("200 2.1.4", "Black female executive directors", 1, 25),
        I("200 2.2.1", "Black other executive management", 2, 60),
        I("200 2.2.2", "Black female other executive management", 1, 30),
        I("200 2.3.1", "Black senior management", 2, 60),
        I("200 2.3.2", "Black female senior management", 1, 30),
        I("200 2.4.1", "Black middle management", 2, 75),
        I("200 2.4.2", "Black female middle management", 1, 38),
        I("200 2.5.1", "Black junior management", 1, 88),
        I("200 2.5.2", "Black female junior management", 1, 44),
        I("200 2.6.1", "Black employees with disabilities", 2, 2),
    ),
)

SKILLS = Element(
    "skills",
    "Skills Development",
    (
        I("300 2.1.1.1", "Learning programmes: black people", 6, 3.5, "leviable"),
        I("300 2.1.1.2", "Bursaries: black students", 4, 2.5, "leviable"),
        I("300 2.1.1.3", "Learning programmes: black employees with disabilities", 4, 0.3,
          "leviable"),
        I("300 2.1.2.1", "Black learnerships/apprenticeships/internships", 6, 5, "employees"),
        I("300 2.1.3", "Bonus: black learners absorbed", 5, 100, bonus=True),
    ),
    priority=True,
)

ESD = Element(
    "esd",
    "Enterprise & Supplier Development",
    (
        I("400 2.1.1", "B-BBEE spend: all Empowering Suppliers", 5, 80, "tmps", "pp"),
        I("400 2.1.2", "B-BBEE spend: QSE Empowering Suppliers", 3, 15, "tmps", "pp"),
        I("400 2.1.3", "B-BBEE spend: EME Empowering Suppliers", 4, 15, "tmps", "pp"),
        I("400 2.1.4", "B-BBEE spend: >=51% black-owned", 11, 50, "tmps", "pp"),
        I("400 2.1.5", "B-BBEE spend: >=30% black-women-owned", 4, 12, "tmps", "pp"),
        I("400 2.1.6", "Bonus: designated-group suppliers >=51% black-owned", 2, 2, "tmps",
          "pp", bonus=True),
        I("400 2.2.1", "Supplier Development", 10, 2, "npat", "sd"),
        I("400 2.3.1", "Enterprise Development", 5, 1, "npat", "ed"),
        I("400 2.4.1", "Bonus: ED beneficiary graduates to SD", 1, 0, "bool", "ed", bonus=True),
        I("400 2.4.2", "Bonus: jobs created through ED/SD", 1, 0, "bool", "ed", bonus=True),
        # Draft Statement 400 of 2026 (GG 54032), NOT LAW. Alternative route to SD + ED.
        I("draft400 2.4.1", "Transformation Fund contribution", 20, 3, "npat", "tf",
          draft_only=True),
    ),
    priority=True,
)

SED = Element(
    "sed",
    "Socio-Economic Development",
    (I("500 2.1", "SED contributions", 5, 1, "npat"),),
)

SCORECARD = Scorecard(
    key="generic",
    name="Generic (Amended Codes 2019)",
    elements=(OWNERSHIP, MANAGEMENT, SKILLS, ESD, SED),
    submins=(
        SubMinimum("ownership", "net_value", 3.2, "S5 cl. 3.3.1.1.1"),
        SubMinimum("skills", None, 8, "S5 cl. 3.3.1.2.1"),
        SubMinimum("esd", "pp", 10.8, "S5 cl. 3.3.1.3.1 per D2 (40% of 27)"),
        SubMinimum("esd", "sd", 4, "S5 cl. 3.3.1.3.1", replaced_by_draft=True),
        SubMinimum("esd", "ed", 2, "S5 cl. 3.3.1.3.1", replaced_by_draft=True),
        SubMinimum("esd", "tf", 8, "Draft S400 2026 cl. 3.3.1", draft_only=True),
    ),
    priority_rule="all",
    sources=("GG 36928", "GG 42496"),
)
