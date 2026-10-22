"""Sector configs as data. Source: bee-team/compliance/sector-codes.md (23 Oct 2026).

All sector codes are aligned to the 2013 Amended Codes; the 2019 generic amendments
(GG 42496) are not cascaded. Where a sector code is silent on a sub-minimum, the app uses
40% of the element's own weighting in the sector scorecard (D2-style default), marked
"silent -> D2".
"""

from __future__ import annotations

from bee.models import EnterpriseSize as S
from bee.rules import Scorecard
from bee.scorecards import generic, qse
from bee.sectors.base import GENERIC_THRESHOLDS, SectorConfig, Thresholds, el, sm
from bee.sectors.tables import attach

G, Q = S.GENERIC, S.QSE
NOT_LOADED = "Sector code not loaded: scored on the generic Amended Codes."
CUTOFF_WARN = "Level cut-offs use the generic table (sector table not extracted; UNVERIFIED)."


def _card(key, name, elements, submins, rule="all", **kw) -> Scorecard:
    return Scorecard(key, name, tuple(elements), tuple(submins), rule, **kw)


# ---------------------------------------------------------------- Construction (N931 2017)
CON_LEVELS = (
    "Construction levels: CSC000 cl. 8.3 absolute points (>=100 L1 ... <40 non-compliant), "
    "no rescaling of the 123-point Large or the QSE scorecard."
)


def _con_large(
    variant: str,
    skills: float,
    esd: dict,
    esd_bonus: float,
    nv: float,
    nv_min: float,
    pp_min: float,
    sdp_min: float,
    sdc_min: float,
    skills_min: float,
    label: str,
) -> Scorecard:
    card = _card(
        f"construction-{variant}",
        f"Construction ({variant}) Large, GG 41287 N931",
        [
            el("ownership", "Ownership", 27, True, {"net_value": nv}, bonus=4),
            el("management", "Management Control", 18, bonus=4),
            el("skills", "Skills Development", skills, True, bonus=5),
            # CSC400 cl. 2 split (VERIFIED): PP / SD programmes / SD contributions. No ED.
            el(
                "esd",
                "Preferential Procurement & Supplier Development",
                sum(esd.values()),
                True,
                esd,
                bonus=esd_bonus,
            ),
            el("sed", "Socio-Economic Development", 5, bonus=1),
        ],
        [
            sm("ownership", "net_value", nv_min, "CSC000 cl. 3.6.1.1.1"),
            sm("skills", None, skills_min, "CSC000 cl. 3.6.1.2.1 (40% of weighting)"),
            sm("esd", "pp", pp_min, "CSC000 cl. 3.6.1.3.1(i)"),
            sm("esd", "sd_programmes", sdp_min, "CSC000 cl. 3.6.1.3.1(ii)"),
            sm("esd", "sd_contributions", sdc_min, "CSC000 cl. 3.6.1.3.1(iii)"),
        ],
        notes=(CON_LEVELS,),
    )
    return attach(card, "Construction", {"*": (label,)})


def _con_qse(variant: str, new_entrant_target: float) -> Scorecard:
    card = _card(
        f"construction-qse-{variant}",
        f"Construction QSE ({variant}), GG 41287 N931 cl. 8.2",
        [
            el("ownership", "Ownership", 27, True, {"net_value": 5}, bonus=3),
            el("management", "Management Control", 20),
            el("skills", "Skills Development", 24, True, bonus=2),
            el(
                "esd",
                "Preferential Procurement & Supplier Development",
                29,
                True,
                {"pp": 22, "sd_contributions": 7},
            ),
            # CSC605 table: 3 core + 2 bonus (the cl. 8.2 scorecard prints 5).
            el("sed", "Socio-Economic Development", 3, bonus=2),
        ],
        [
            sm("ownership", "net_value", 2, "CSC601 2.1 -> CSC100 (40% of 5, INTERPRETATION)"),
            sm("skills", None, 9.6, "CSC603 2.1 -> CSC300 (40% of 24, INTERPRETATION)"),
            sm("esd", "pp", 8.8, "CSC604 2.1 -> CSC400 (40% of 22, INTERPRETATION)"),
            sm("esd", "sd_contributions", 2.8, "CSC604 2.1 -> CSC400 (40% of 7, INTERPRETATION)"),
        ],
        rule="ownership_plus_one",
        notes=(
            CON_LEVELS,
            "Gazette inconsistency (Construction QSE SED): cl. 8.2 scorecard prints 5 but the "
            "CSC605 table prints 3 + 2 bonus; the app uses 3 core + 2 bonus (max 5). "
            "INTERPRETATION.",
            "Gazette inconsistency (Construction QSE MC 2.1/2.2): senior+middle management "
            "targets print as 20% / 10%, below junior management's 40%; reproduced as "
            "printed (likely typo, UNVERIFIED intent).",
            "Construction QSE SD 1.3 target printed '3%' with a struck-through figure; "
            "the app uses 3%.",
        ),
    )
    return attach(
        card,
        "Construction",
        {"*": ("QSE (Contractor & BEP)",)},
        {"CSC601 1.2.3": new_entrant_target},
    )


CONSTRUCTION = SectorConfig(
    key="construction",
    name="Construction",
    gazette="GG 41287, Notice 931, 1 Dec 2017",
    status="verified",
    variants=("contractor", "bep"),
    default_variant="contractor",
    thresholds={
        "contractor": Thresholds(10_000_000, 50_000_000),  # cl. 4.1, 5.1
        "bep": Thresholds(6_000_000, 25_000_000),
    },
    eme_deemed=((100, 1), (51, 2), (30, 4), (0, 5)),  # cl. 4.2
    cards={
        (G, "contractor"): _con_large(
            "contractor",
            21,
            {"pp": 19, "sd_programmes": 5, "sd_contributions": 10},
            4,
            6,
            2.4,
            7.6,
            2,
            4,
            8.4,
            "Large-Contractor",
        ),
        (G, "bep"): _con_large(
            "bep",
            29,
            {"pp": 18, "sd_programmes": 4, "sd_contributions": 5},
            3,
            4,
            1.6,
            7.2,
            1.6,
            2,
            11.6,
            "Large-BEP",
        ),
        (Q, "contractor"): _con_qse("contractor", 10),
        (Q, "bep"): _con_qse("bep", 5),
    },
    construction_eme_rules=True,
    warnings=(
        "QSEs on automatic levels must still comply with QSE Skills Development "
        "(cl. 3.6.2.3); not assessed by the calculator.",
    ),
)


# ------------------------------------------------------- Financial Services (N1325 2017)
FS_SKILLS = dict(option_key="fs_skills_submin")
FS_NOTE = (
    "FSC Skills sub-minimum: cl. 3.3.1(b) reads '40% of 15' but the weighting is 20; the "
    "app uses 8 (40% of 20) per owner decision FS-D1 (interpretation)."
)
FS2A = "Large (Table 2a: banks, insurers, exchanges)"
FS_ALL = "Large (all)"
FS_OTHER = "Large-Other (STI, exchanges, others)"
FS_BANK = "Large-Banks&Life"
FS_AFS = "Large-Banks&Life + STI"


def _fs_large(variant: str, own: float, afs: float, labels: dict) -> Scorecard:
    bank = variant == "bank"
    elements = [
        el("ownership", "Ownership (FS100)", own, True, {"net_value": 6}, bonus=5),
        el("management", "Management Control (FS200)", 20),
        el("skills", "Skills Development (FS300)", 20, True, bonus=3),
        el(
            "esd",
            "Procurement & ESD (FS400)",
            15 if bank else 35,
            True,
            {"pp": 15} if bank else {"pp": 20, "sd": 10, "ed": 5},
            bonus=4 if bank else 8,
        ),
        el("sed", "SED & Consumer Education (FS500)", 5, bonus=1),
    ]
    if bank:
        # FS600 (VERIFIED): EF 15 (12 + 3), SD 7 (1.8% NPAT), ED 3 (0.2% NPAT), bonus 4.
        elements.append(
            el(
                "ef",
                "Empowerment Financing & ESD (FS600)",
                25,
                True,
                {"ef": 15, "sd": 7, "ed": 3},
                bonus=4,
            )
        )
    if afs:
        elements.append(el("afs", "Access to Financial Services (FS700)", afs))
    subs = [
        sm("ownership", "net_value", 2.4, "FSC cl. 3.3.1(a)"),
        sm("skills", None, 8, "FSC cl. 3.3.1(b) per FS-D1", **FS_SKILLS),
    ]
    if bank:
        subs += [
            sm("ef", "ef", 6, "FSC cl. 3.3.1(d) (40% of 15)"),
            sm("ef", "sd", 2.8, "FSC cl. 3.3.1(d) (40% of 7)"),
            sm("ef", "ed", 1.2, "FSC cl. 3.3.1(d) (40% of 3)"),
        ]
    else:
        subs += [
            sm("esd", "pp", 8, "FSC cl. 3.3.1(c)"),
            sm("esd", "sd", 4, "FSC cl. 3.3.1(c)"),
            sm("esd", "ed", 2, "FSC cl. 3.3.1(c)"),
        ]
    notes = ("FS indicator targets with a year-3+ step use the year 1-3 figure.",)
    if variant == "other":
        notes += (
            "FS 'Other' Ownership: the 25-point indicator split is not extracted "
            "(UNVERIFIED); enter Ownership as points.",
        )
    card = _card(
        f"fs-{variant}",
        f"Financial Services {variant}, GG 41287 N1325",
        elements,
        subs,
        level_base=109,
        level_base_option="fs_rescale_109",
        notes=notes,
    )
    return attach(card, "FS 2017", labels)


FS_QSFI = attach(
    _card(
        "fs-qsfi",
        "Financial Services QSFI (FS800), GG 41287 N1325",
        [
            # Net Value 8 = 25 - 17 listed indicators (DERIVED, Compliance table).
            el("ownership", "Ownership", 25, True, {"net_value": 8}, bonus=4),
            el("management", "Management Control", 15),
            el("skills", "Skills Development", 25, True),
            el("esd", "ESD", 30, True, {"pp": 20, "sd": 5, "ed": 5}),
            el("sed", "SED & Consumer Education", 5, bonus=1),
        ],
        [
            sm("ownership", "net_value", 3.2, "FSC cl. 3.3.2 -> FS100 (40% of 8, derived)"),
            sm("skills", None, 10, "silent -> D2 (40% of 25)"),
            sm("esd", "pp", 8, "silent -> D2 (40% of 20)"),
            sm("esd", "sd", 2, "silent -> D2"),
            sm("esd", "ed", 2, "silent -> D2"),
        ],
        rule="ownership_plus_one",  # cl. 3.3.2(b)
        level_base=109,
        level_base_option="fs_rescale_109",
    ),
    "FS 2017",
    {"*": ("QSFI",)},
)

_FS_COMMON = {"management": (FS_ALL,), "skills": (FS_ALL,)}
FINANCIAL = SectorConfig(
    key="financial",
    name="Financial Services (Amended FSC 2017)",
    gazette="GG 41287, Notice 1325, 1 Dec 2017",
    status="verified",
    variants=("bank", "short_term_insurer", "exchange", "other"),
    default_variant="other",
    cards={
        (G, "bank"): _fs_large(
            "bank",
            23,
            12,
            {
                **_FS_COMMON,
                "ownership": (FS2A,),
                "esd": (FS_BANK,),
                "ef": (FS_BANK,),
                "sed": (FS_BANK,),
                "afs": (FS_AFS,),
            },
        ),
        (G, "short_term_insurer"): _fs_large(
            "short_term_insurer",
            23,
            12,
            {
                **_FS_COMMON,
                "ownership": (FS2A,),
                "esd": (FS_OTHER,),
                "sed": (FS_OTHER,),
                "afs": (FS_AFS,),
            },
        ),
        (G, "exchange"): _fs_large(
            "exchange",
            23,
            0,
            {**_FS_COMMON, "ownership": (FS2A,), "esd": (FS_OTHER,), "sed": (FS_OTHER,)},
        ),
        (G, "other"): _fs_large(
            "other", 25, 0, {**_FS_COMMON, "esd": (FS_OTHER,), "sed": (FS_OTHER,)}
        ),
        (Q, None): FS_QSFI,
    },
    size_labels={Q: "QSFI"},
    warnings=(
        FS_NOTE,
        "FSC levels: Large scorecards (not 100 points) normalised to 109 (score x 109 / "
        "scorecard total) before the cl. 8.2.1 table (interpretation; switch off with "
        "options['fs_rescale_109']=False). The 100-point QSFI card is scored raw.",
    ),
)


# -------------------------------------------------------------- AgriBEE (N1354 2017)
def _agri(key, name, own, mc, sd, esd, sed, sd_min, esd_mins, rule="all", label=None):
    elements, subs = [], []
    if own:
        elements.append(el("ownership", "Ownership", own, True, {"net_value": 8}))
        subs.append(sm("ownership", "net_value", 3.2, "AgriBEE cl. 5.1.1"))
    elements += [
        el("management", "Management Control", mc),
        el("skills", "Skills Development", sd, True),
        el("esd", "ESD", sum(esd.values()) if esd else 0, True, esd),
        el("sed", "SED", sed),
    ]
    subs.append(sm("skills", None, sd_min, "AgriBEE cl. 5.1.2 (40% of weighting)"))
    for g, v in esd_mins.items():
        subs.append(sm("esd", g, v, "AgriBEE cl. 5.1.3 (40% of category)"))
    card = _card(
        key,
        name,
        elements,
        subs,
        rule,
        notes=("AgriBEE levels: cl. 4.3 absolute points (same table as Generic).",),
    )
    return attach(card, "AgriBEE", {"*": (label,)}) if label else card


AGRI = SectorConfig(
    key="agri",
    name="AgriBEE",
    gazette="GG 41306, Notice 1354, 8 Dec 2017",
    status="verified",
    variants=("standard", "specialised"),
    default_variant="standard",
    # cl. 6.10.1 "R10m or less" (cl. 2.7 says "less than": ambiguity flagged).
    thresholds={None: GENERIC_THRESHOLDS},
    qse_deemed=True,  # black QSEs need not be measured (cl. 2.6)
    cards={
        (G, "standard"): _agri(
            "agri-large",
            "AgriBEE Large",
            25,
            19,
            20,
            {"pp": 25, "sd": 10, "ed": 5},
            15,
            8,
            {"pp": 10, "sd": 4, "ed": 2},
            label="Large",
        ),
        (Q, "standard"): _agri(
            "agri-qse",
            "AgriBEE QSE",
            25,
            15,
            30,
            {"pp": 15, "sd": 5, "ed": 5},
            15,
            12,
            {"pp": 6, "sd": 2, "ed": 2},
            label="QSE",
        ),
        # Specialised scorecards (7.3.4, 7.4.5, 7.5.2, 7.6.2) not tabulated: points only.
        (G, "specialised"): _agri(
            "agri-spec-large",
            "AgriBEE Specialised Large",
            0,
            20,
            25,
            {"main": 50},
            5,
            10,
            {None: 20},
        ),
        (Q, "specialised"): _agri(
            "agri-spec-qse", "AgriBEE Specialised QSE", 0, 25, 30, {"main": 30}, 15, 12, {None: 12}
        ),
    },
    warnings=(
        "AgriBEE R10m boundary: cl. 2.7 'less than' vs cl. 6.10.1 'or less'; app treats "
        "R10m as EME (cl. 6.10.1).",
    ),
)


# --------------------------------------------------------------- Tourism (GG 39430 2015)
def _tourism(key, name, own, mc, sd, esd_groups, rule, nv_min, sd_min, pp, sdv, ed):
    card = _card(
        key,
        name,
        [
            el("ownership", "Ownership", own, True, {"net_value": 8}),
            el("management", "Management Control", mc),
            el("skills", "Skills Development", sd, True),
            el("esd", "ESD", sum(esd_groups.values()), True, esd_groups),
            el("sed", "SED", 5),
        ],
        [
            sm("ownership", "net_value", nv_min, "Tourism cl. 10"),
            sm("skills", None, sd_min, "Tourism cl. 10 (40%)"),
            sm("esd", "pp", pp, "Tourism cl. 10"),
            sm("esd", "sd", sdv, "Tourism cl. 10"),
            sm("esd", "ed", ed, "Tourism cl. 10"),
        ],
        rule,
    )
    return attach(card, "Tourism", {"*": ("Large" if key == "tourism-large" else "QSE",)})


TOURISM = SectorConfig(
    key="tourism",
    name="Tourism",
    gazette="GG 39430, 20 Nov 2015",
    status="verified",
    thresholds={None: Thresholds(5_000_000, 45_000_000)},  # cl. 13.1, 14.1, 15.4
    cards={
        (G, None): _tourism(
            "tourism-large",
            "Tourism Large (cl. 17.1)",
            27,
            19,
            20,
            {"pp": 25, "sd": 10, "ed": 5},
            "all",
            3.2,
            8,
            10,
            4,
            2,
        ),
        (Q, None): _tourism(
            "tourism-qse",
            "Tourism QSE (cl. 17.2)",
            26,
            15,
            25,
            {"pp": 18, "sd": 7, "ed": 5},
            "ownership_plus_one",
            3.2,
            10,
            7.2,
            2.8,
            2,
        ),
    },
    warnings=("Tourism QSE sub-minimums use the 2013 QSE pattern (silent -> D2).",),
)


# ------------------------------------------------------------------ ICT (GG 40407 2016)
ICT_LARGE = _card(
    "ict-large",
    "ICT Large (DECODED, UNVERIFIED)",
    [
        el("ownership", "Ownership", 25, True, {"net_value": 8}),
        el("management", "Management Control", 23),
        el("skills", "Skills Development", 20, True),
        el("esd", "ESD", 50, True, {"pp": 25, "sd": 10, "ed": 15}),
        el("sed", "SED", 12),
    ],
    [
        sm("ownership", "net_value", 3.2, "ICT cl. 3.3 (NV figure garbled; UNVERIFIED)"),
        sm("skills", None, 8, "ICT cl. 3.3.2 (40%)"),
        sm("esd", "pp", 10, "silent -> D2"),
        sm("esd", "sd", 4, "silent -> D2"),
        sm("esd", "ed", 6, "silent -> D2"),
    ],
)

# ICT QSE (AICT600 Statement 600 cl. 3.1): 25+15+25+30+12 = 107 core. Indicators from CSV.
ICT_QSE = attach(
    _card(
        "ict-qse",
        "ICT QSE (AICT600 Statement 600), GG 40407",
        [
            el("ownership", "Ownership", 25, True, {"net_value": 8}),
            el("management", "Management Control", 15),
            el("skills", "Skills Development", 25, True, bonus=5),
            el("esd", "ESD", 30, True, {"pp": 20, "sd": 5, "ed": 5}, bonus=5),
            el("sed", "SED", 12),
        ],
        [
            sm("ownership", "net_value", 3.2, "ICT QSE (40% of 8)"),
            sm("skills", None, 10, "ICT QSE (40% of 25)"),
            sm("esd", "pp", 8, "ICT QSE (40% of 20)"),
            sm("esd", "sd", 2, "ICT QSE (40% of 5)"),
            sm("esd", "ed", 2, "ICT QSE (40% of 5)"),
        ],
        rule="ownership_plus_one",
    ),
    "ICT",
    {"*": ("QSE",)},
)

ICT = SectorConfig(
    key="ict",
    name="ICT",
    gazette="GG 40407, 7 Nov 2016",
    status="unverified",
    # Exactly R50m = Generic (CEO decision 4, Compliance tables; cl. 2.14.1 "<= R50m"
    # reading not applied).
    thresholds={None: GENERIC_THRESHOLDS},
    cards={(G, None): ICT_LARGE, (Q, None): ICT_QSE},
    warnings=(
        "UNVERIFIED: ICT Large figures were decoded from a garbled PDF and need human "
        "verification before use.",
        "ICT QSE indicators transcribed from page images (GG 40407 pp.80-86); still "
        "pending expert verification.",
        "ICT automatic-recognition ownership % garbled; generic 51%/100% used.",
        CUTOFF_WARN,
    ),
)


# --------------------------------------------------------------- excluded / not loaded

_GENERIC_CARDS = {(G, None): generic.SCORECARD, (Q, None): qse.SCORECARD}


def _fallback(key, name, gazette, status="not_loaded", extra=()):
    return SectorConfig(
        key, name, gazette, status, dict(_GENERIC_CARDS), warnings=(NOT_LOADED, *extra)
    )


MAC = _fallback(
    "mac",
    "Marketing, Advertising & Communication",
    "GG 39887, Apr 2016",
    extra=(
        "MAC sector code not loaded (CEO decision): the gazetted card has an internal "
        "total inconsistency (124 vs 134); scored on the generic Amended Codes.",
    ),
)


GENERIC = SectorConfig(
    "generic", "Generic (Amended Codes)", "GG 36928 / GG 42496", "verified", dict(_GENERIC_CARDS)
)

SECTORS: dict[str, SectorConfig] = {
    s.key: s
    for s in (
        GENERIC,
        CONSTRUCTION,
        FINANCIAL,
        AGRI,
        TOURISM,
        ICT,
        MAC,
        _fallback("property", "Property", "GG 40910, Jun 2017"),
        _fallback("defence", "Defence", "GG 42391, 12 Apr 2019"),
        _fallback("forestry", "Forestry", "GG 40803, 21 Apr 2017"),
        _fallback("chartered_accountancy", "Chartered Accountancy", "GG 42417, 26 Apr 2019"),
        _fallback("legal", "Legal", "UNVERIFIED"),
        _fallback(
            "transport",
            "Integrated Transport",
            "GG 32511, 21 Aug 2009",
            "legacy",
            (
                "Legacy 2007-Codes sector code; confirm with the dtic. Not mixed with "
                "Amended weightings.",
            ),
        ),
    )
}
