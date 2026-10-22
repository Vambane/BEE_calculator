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

G, Q = S.GENERIC, S.QSE
NOT_LOADED = "Sector code not loaded: scored on the generic Amended Codes."
CUTOFF_WARN = "Level cut-offs use the generic table (sector table not extracted; UNVERIFIED)."


def _card(key, name, elements, submins, rule="all", **kw) -> Scorecard:
    return Scorecard(key, name, tuple(elements), tuple(submins), rule, **kw)


# ---------------------------------------------------------------- Construction (N931 2017)
def _con_large(variant: str, skills: float, esd: float, nv: float, nv_min: float,
               pp_min: float, sdp_min: float, sdc_min: float, esd_bonus: float) -> Scorecard:
    return _card(
        f"construction-{variant}",
        f"Construction ({variant}) Large, GG 41287 N931",
        [
            el("ownership", "Ownership", 27, True, {"net_value": nv}, bonus=4),
            el("management", "Management Control", 18, bonus=4),
            el("skills", "Skills Development", skills, True, bonus=5),
            # Sub-element split not extracted: groups are capped at the element weighting.
            el("esd", "Preferential Procurement & Supplier Development", esd, True,
               {"pp": esd, "sd_programmes": esd, "sd_contributions": esd},
               bonus=esd_bonus),
            el("sed", "Socio-Economic Development", 5, bonus=1),
        ],
        [
            sm("ownership", "net_value", nv_min, "Construction cl. 3.6.1"),
            sm("skills", None, round(0.4 * skills, 4), "silent -> D2 (40% of weighting)"),
            sm("esd", "pp", pp_min, "Construction cl. 3.6.1"),
            sm("esd", "sd_programmes", sdp_min, "Construction cl. 3.6.1"),
            sm("esd", "sd_contributions", sdc_min, "Construction cl. 3.6.1"),
        ],
    )


CON_QSE = _card(
    "construction-qse",
    "Construction QSE, GG 41287 N931 cl. 8.2",
    [
        el("ownership", "Ownership", 27, True, bonus=3),
        el("management", "Management Control", 20),
        el("skills", "Skills Development", 24, True, bonus=2),
        el("esd", "Preferential Procurement & Supplier Development", 29, True),
        el("sed", "Socio-Economic Development", 5),
    ],
    [
        sm("ownership", None, 10.8, "silent -> D2 (40% of 27)"),
        sm("skills", None, 9.6, "silent -> D2 (40% of 24)"),
        sm("esd", None, 11.6, "silent -> D2 (40% of 29)"),
    ],
    rule="ownership_plus_one",
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
        (G, "contractor"): _con_large("contractor", 21, 34, 6, 2.4, 7.6, 2, 4, 4),
        (G, "bep"): _con_large("bep", 29, 27, 4, 1.6, 7.2, 1.6, 2, 3),
        (Q, None): CON_QSE,
    },
    construction_eme_rules=True,
    warnings=(
        CUTOFF_WARN,
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


def _fs_large(variant: str, own: float, esd: float, ef: float, afs: float) -> Scorecard:
    elements = [
        el("ownership", "Ownership (FS100)", own, True, {"net_value": 6}),
        el("management", "Management Control (FS200)", 20),
        el("skills", "Skills Development (FS300)", 20, True),
        el("esd", "Procurement & ESD (FS400)", esd, True,
           None if ef else {"pp": esd - 15, "sd": 10, "ed": 5}),
        el("sed", "SED & Consumer Education (FS500)", 5),
    ]
    if ef:
        elements.append(el("ef", "Empowerment Financing & ESD (FS600)", ef, True))
    if afs:
        elements.append(el("afs", "Access to Financial Services (FS700)", afs))
    subs = [
        sm("ownership", "net_value", 2.4, "FSC cl. 3.3.1(a)"),
        sm("skills", None, 8, "FSC cl. 3.3.1(b) per FS-D1", **FS_SKILLS),
    ]
    if ef:
        # cl. 3.3.1: 40% of each of EF, SD, ED. The EF/SD/ED split was not extracted, so
        # the app tests 40% of FS600 and 40% of FS400 (interpretation, UNVERIFIED).
        subs += [
            sm("ef", None, 0.4 * ef, "FSC cl. 3.3.1 (element-level, UNVERIFIED split)"),
            sm("esd", None, 0.4 * esd, "FSC cl. 3.3.1 (element-level, UNVERIFIED split)"),
        ]
    else:
        subs += [
            sm("esd", "pp", 8, "FSC cl. 3.3.1(c)"),
            sm("esd", "sd", 4, "FSC cl. 3.3.1(c)"),
            sm("esd", "ed", 2, "FSC cl. 3.3.1(c)"),
        ]
    return _card(f"fs-{variant}", f"Financial Services {variant}, GG 41287 N1325",
                 elements, subs, level_base=109, level_base_option="fs_rescale_109")


FS_QSFI = _card(
    "fs-qsfi",
    "Financial Services QSFI (FS800), GG 41287 N1325",
    [
        el("ownership", "Ownership", 25, True, {"net_value": 6}),
        el("management", "Management Control", 15),
        el("skills", "Skills Development", 25, True),
        el("esd", "ESD", 30, True, {"pp": 20, "sd": 5, "ed": 5}),
        el("sed", "SED", 5),
    ],
    [
        sm("ownership", "net_value", 2.4, "FSC cl. 3.3.1(a)"),
        sm("skills", None, 10, "silent -> D2 (40% of 25)"),
        sm("esd", "pp", 8, "silent -> D2 (40% of 20)"),
        sm("esd", "sd", 2, "silent -> D2"),
        sm("esd", "ed", 2, "silent -> D2"),
    ],
    rule="ownership_plus_one",  # cl. 3.3.2(b)
    level_base=109,
    level_base_option="fs_rescale_109",
)

FINANCIAL = SectorConfig(
    key="financial",
    name="Financial Services (Amended FSC 2017)",
    gazette="GG 41287, Notice 1325, 1 Dec 2017",
    status="verified",
    variants=("bank", "short_term_insurer", "exchange", "other"),
    default_variant="other",
    cards={
        (G, "bank"): _fs_large("bank", 23, 15, 25, 12),
        (G, "short_term_insurer"): _fs_large("short_term_insurer", 23, 35, 0, 12),
        (G, "exchange"): _fs_large("exchange", 23, 35, 0, 0),
        (G, "other"): _fs_large("other", 25, 35, 0, 0),
        (Q, None): FS_QSFI,
    },
    size_labels={Q: "QSFI"},
    warnings=(
        FS_NOTE,
        "FSC levels: score normalised to 109 (score x 109 / scorecard total) before the "
        "cl. 8.2.1 table (interpretation; switch off with options['fs_rescale_109']=False).",
    ),
)


# -------------------------------------------------------------- AgriBEE (N1354 2017)
def _agri(key, name, own, mc, sd, esd, sed, rule="all"):
    elements, subs = [], []
    if own:
        elements.append(el("ownership", "Ownership", own, True, {"net_value": 8}))
        subs.append(sm("ownership", "net_value", 3.2, "generic via AgriBEE cl. 1.3"))
    elements += [
        el("management", "Management Control", mc),
        el("skills", "Skills Development", sd, True),
        el("esd", "ESD", esd, True),
        el("sed", "SED", sed),
    ]
    subs += [
        sm("skills", None, 0.4 * sd, "AgriBEE cl. 5.1; silent figure -> D2"),
        sm("esd", None, 0.4 * esd, "AgriBEE cl. 5.1; silent figure -> D2"),
    ]
    return _card(key, name, elements, subs, rule)


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
        (G, "standard"): _agri("agri-large", "AgriBEE Large", 25, 19, 20, 40, 15),
        (Q, "standard"): _agri("agri-qse", "AgriBEE QSE", 25, 15, 30, 25, 15),
        (G, "specialised"): _agri("agri-spec-large", "AgriBEE Specialised Large",
                                  0, 20, 25, 50, 5),
        (Q, "specialised"): _agri("agri-spec-qse", "AgriBEE Specialised QSE",
                                  0, 25, 30, 30, 15),
    },
    warnings=(
        "AgriBEE R10m boundary: cl. 2.7 'less than' vs cl. 6.10.1 'or less'; app treats "
        "R10m as EME (cl. 6.10.1).",
        "AgriBEE indicator targets not extracted; ESD/Skills sub-minimums use 40% of the "
        "AgriBEE weighting (silent -> D2).",
        CUTOFF_WARN,
    ),
)


# --------------------------------------------------------------- Tourism (GG 39430 2015)
def _tourism(key, name, own, mc, sd, esd_groups, rule, nv_min, sd_min, pp, sdv, ed):
    return _card(
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


TOURISM = SectorConfig(
    key="tourism",
    name="Tourism",
    gazette="GG 39430, 20 Nov 2015",
    status="verified",
    thresholds={None: Thresholds(5_000_000, 45_000_000)},  # cl. 13.1, 14.1, 15.4
    cards={
        (G, None): _tourism("tourism-large", "Tourism Large (cl. 17.1)", 27, 19, 20,
                            {"pp": 25, "sd": 10, "ed": 5}, "all", 3.2, 8, 10, 4, 2),
        (Q, None): _tourism("tourism-qse", "Tourism QSE (cl. 17.2)", 26, 15, 25,
                            {"pp": 20, "sd": 5, "ed": 5}, "ownership_plus_one",
                            3.2, 10, 8, 2, 2),
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

ICT = SectorConfig(
    key="ict",
    name="ICT",
    gazette="GG 40407, 7 Nov 2016",
    status="unverified",
    # cl. 2.14.1 "QSE <= R50m": exactly R50m is a QSE under ICT.
    thresholds={None: Thresholds(10_000_000, 50_000_000, large_inclusive=False)},
    cards={(G, None): ICT_LARGE, (Q, None): qse.SCORECARD},
    warnings=(
        "UNVERIFIED: ICT sector code figures were decoded from a garbled PDF and need "
        "human verification before use.",
        "ICT QSE table not decoded: QSEs use the generic QSE scorecard.",
        "ICT automatic-recognition ownership % garbled; generic 51%/100% used.",
        CUTOFF_WARN,
    ),
)


# --------------------------------------------------------------- excluded / not loaded
MAC = SectorConfig(
    key="mac",
    name="Marketing, Advertising & Communication",
    gazette="GG 39887, Apr 2016",
    status="excluded",
    cards={},
    warnings=(
        "MAC sector code is excluded from this version (internal total inconsistency "
        "124 vs 134; sub-minimums not extracted). Use a verification agency.",
    ),
)

_GENERIC_CARDS = {(G, None): generic.SCORECARD, (Q, None): qse.SCORECARD}


def _fallback(key, name, gazette, status="not_loaded", extra=()):
    return SectorConfig(key, name, gazette, status, dict(_GENERIC_CARDS),
                        warnings=(NOT_LOADED, *extra))


GENERIC = SectorConfig("generic", "Generic (Amended Codes)", "GG 36928 / GG 42496",
                       "verified", dict(_GENERIC_CARDS))

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
            ("Legacy 2007-Codes sector code; confirm with the dtic. Not mixed with "
             "Amended weightings.",),
        ),
    )
}
