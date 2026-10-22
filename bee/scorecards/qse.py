"""QSE scorecard (Code Series 600, GG 38766, 2015): 100 points before bonuses.

ESD bonuses (604 cl. 5.1.1.2, 5.1.1.5.1-2) and SED (605 cl. 6.2: 5 points, 1% of NPAT)
verified from the GG 38766 page images (cto-interpretations.md §4).
"""

from bee.rules import Element, Indicator, Scorecard, SubMinimum

I = Indicator  # noqa: E741

OWNERSHIP = Element(
    "ownership",
    "Ownership",
    (
        I("601 2.1.1.1", "Voting rights: black people", 5, 25.0001),
        I("601 2.1.1.2", "Voting rights: black women", 2, 10),
        I("601 2.1.2.1", "Economic interest: black people", 5, 25),
        I("601 2.1.2.2", "Economic interest: black women", 2, 10),
        I("601 2.1.2.3", "New entrants or black designated groups", 3, 2),
        I("601 2.1.3.1", "Net Value", 8, 100, group="net_value"),
    ),
    priority=True,
)

MANAGEMENT = Element(
    "management",
    "Management Control",
    (
        I("602 3.1.1.1.1", "Black executive management", 5, 50),
        I("602 3.1.1.1.2", "Black female executive management", 2, 25),
        I("602 3.1.1.2.1", "Black senior, middle and junior management", 6, 60),
        I("602 3.1.1.2.2", "Black female senior, middle and junior management", 2, 30),
    ),
)

SKILLS = Element(
    "skills",
    "Skills Development",
    (
        I("603 4.1.1.1.1", "Learning programmes: black people", 15, 3, "leviable"),
        I("603 4.1.1.1.2", "Learning programmes: black females", 7, 1, "leviable"),
        I(
            "603 4.1.1.1.3",
            "Learning programmes: black people with disabilities",
            3,
            0.15,
            "leviable",
        ),
        I("603 4.1.1.2", "Bonus: black people absorbed", 5, 100, bonus=True),
    ),
    priority=True,
)

ESD = Element(
    "esd",
    "Enterprise & Supplier Development",
    (
        I("604 5.1.1.1.1", "B-BBEE spend: all Empowering Suppliers", 15, 60, "tmps", "pp"),
        I("604 5.1.1.1.2", "B-BBEE spend: >=51% black-owned", 5, 15, "tmps", "pp"),
        I(
            "604 5.1.1.2",
            "Bonus: designated-group suppliers >=51% black-owned",
            1,
            1,
            "tmps",
            "pp",
            bonus=True,
        ),
        I("604 5.1.1.3.1", "Supplier Development", 5, 1, "npat", "sd"),
        I("604 5.1.1.4.1", "Enterprise Development", 5, 1, "npat", "ed"),
        I(
            "604 5.1.1.5.1",
            "Bonus: ED beneficiary graduates to SD",
            1,
            0,
            "bool",
            "ed",
            bonus=True,
            draft_points=2,
        ),
        I(
            "604 5.1.1.5.2",
            "Bonus: jobs created through ED/SD",
            1,
            0,
            "bool",
            "ed",
            bonus=True,
            draft_points=2,
        ),
        # Draft QSE Transformation Fund (2026 draft, NOT LAW): alternative to SD + ED.
        I(
            "draft604 7.1.1.5.1",
            "Transformation Fund contribution",
            15,
            2,
            "npat",
            "tf",
            draft_only=True,
        ),
    ),
    priority=True,
)

SED = Element(
    "sed",
    "Socio-Economic Development",
    (I("605 6.2", "SED contributions", 5, 1, "npat"),),
)

SCORECARD = Scorecard(
    key="qse",
    name="QSE (Code Series 600, 2015)",
    elements=(OWNERSHIP, MANAGEMENT, SKILLS, ESD, SED),
    submins=(
        SubMinimum("ownership", "net_value", 3.2, "S5 cl. 3.3.1.1.1 via 601 cl. 2.2.2"),
        SubMinimum("skills", None, 10, "603 cl. 4.2.1 (40% of 25, interpretation)"),
        SubMinimum("esd", "pp", 8, "604 cl. 5.2.1 (40% of 20, interpretation)"),
        SubMinimum("esd", "sd", 2, "604 cl. 5.2.1", replaced_by_draft=True),
        SubMinimum("esd", "ed", 2, "604 cl. 5.2.1", replaced_by_draft=True),
        SubMinimum("esd", "tf", 6, "Draft QSE TF (40% of 15, INTERPRETATION)", draft_only=True),
    ),
    priority_rule="ownership_plus_one",
    sources=("GG 38766", "GG 42496"),
)
