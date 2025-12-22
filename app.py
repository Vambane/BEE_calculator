import math
from typing import Dict, Literal

import pandas as pd
import streamlit as st
import altair as alt

EnterpriseSize = Literal["EME", "QSE", "Generic"]


def enterprise_size_from_turnover(turnover: float) -> EnterpriseSize:
    if turnover <= 10_000_000:
        return "EME"
    if turnover <= 50_000_000:
        return "QSE"
    return "Generic"


LEVELS = [
    {"threshold": 100, "label": "Level 1"},
    {"threshold": 95, "label": "Level 2"},
    {"threshold": 90, "label": "Level 3"},
    {"threshold": 80, "label": "Level 4"},
    {"threshold": 75, "label": "Level 5"},
    {"threshold": 70, "label": "Level 6"},
    {"threshold": 55, "label": "Level 7"},
    {"threshold": 40, "label": "Level 8"},
]


def level_from_score(score: float) -> str:
    for level in LEVELS:
        if score >= level["threshold"]:
            return level["label"]
    return "Non-compliant"


def calculate_bee_score(profile: Dict, spend: Dict) -> Dict:
    size = enterprise_size_from_turnover(profile["turnover"])

    if size == "EME":
        level = (
            "Level 1"
            if profile["black_ownership"] >= 100
            else "Level 2"
            if profile["black_ownership"] >= 51
            else "Level 4"
        )
        total = 100 if level == "Level 1" else 95 if level == "Level 2" else 80
        ownership = total * 0.25
        management = total * 0.1
        skills = total * 0.15
        procurement = total * 0.3
        enterprise_dev = total * 0.1
        socio_economic = total * 0.1
        return {
            "ownership": ownership,
            "management": management,
            "skills": skills,
            "procurement": procurement,
            "enterprise_dev": enterprise_dev,
            "socio_economic": socio_economic,
            "total": total,
            "level": level,
            "discount_applied": False,
            "size": size,
        }

    ownership_weight = 25
    management_weight = 15
    skills_weight = 20
    procurement_weight = 20
    enterprise_dev_weight = 10
    socio_economic_weight = 10

    ownership_base = (
        min(profile["black_ownership"], 100) / 100 * ownership_weight
    )
    women_bonus = min(profile["black_women_ownership"], 30) / 30
    ownership = min(
        ownership_weight,
        ownership_base + women_bonus * (ownership_weight * 0.2),
    )

    management = (
        min(profile["black_management"], 100) / 100 * management_weight
    )
    skills = min(1, spend["skills_development_pct"] / 3) * skills_weight

    procurement_bo = min(1, spend["supplier_black_owned_pct"] / 40)
    procurement_eme_qse = min(1, spend["supplier_eme_qse_pct"] / 25)
    procurement = procurement_bo * (procurement_weight * 0.65) + procurement_eme_qse * (
        procurement_weight * 0.35
    )

    enterprise_dev = min(1, spend["enterprise_dev_pct"] / 1) * enterprise_dev_weight
    socio_economic = min(1, spend["socio_economic_pct"] / 1) * socio_economic_weight

    total = ownership + management + skills + procurement + enterprise_dev + socio_economic
    level = level_from_score(total)
    discount_applied = False

    if size == "Generic" and profile["black_ownership"] < 10:
        discount_applied = True
        current_index = next(
            (i for i, lv in enumerate(LEVELS) if lv["label"] == level), None
        )
        if current_index is not None and level != "Non-compliant":
            downgraded = LEVELS[min(current_index + 1, len(LEVELS) - 1)]
            level = downgraded["label"]

    return {
        "ownership": ownership,
        "management": management,
        "skills": skills,
        "procurement": procurement,
        "enterprise_dev": enterprise_dev,
        "socio_economic": socio_economic,
        "total": total,
        "level": level,
        "discount_applied": discount_applied,
        "size": size,
    }


def main():
    st.set_page_config(
        page_title="B-BBEE SME Calculator",
        page_icon="⚖️",
        layout="wide",
    )
    st.title("B-BBEE Calculator for South African SMEs/QSEs")
    st.caption(
        "Plan your scorecard inputs. Simplified model; confirm with your verification agency and sector code."
    )

    default_profile = {
        "company": "Ubuntu Manufacturing (Pty) Ltd",
        "province": "Gauteng",
        "turnover": 24_000_000,
        "payroll": 7_500_000,
        "black_ownership": 35.0,
        "black_women_ownership": 12.0,
        "black_management": 40.0,
    }
    default_spend = {
        "skills_development_pct": 1.8,
        "supplier_black_owned_pct": 28.0,
        "supplier_eme_qse_pct": 18.0,
        "enterprise_dev_pct": 0.6,
        "socio_economic_pct": 0.4,
    }

    with st.form("inputs"):
        cols = st.columns(2)
        with cols[0]:
            st.subheader("Company profile")
            company = st.text_input("Company name", default_profile["company"])
            province = st.selectbox(
                "Province",
                [
                    "Gauteng",
                    "Western Cape",
                    "KwaZulu-Natal",
                    "Eastern Cape",
                    "Free State",
                    "North West",
                    "Mpumalanga",
                    "Northern Cape",
                    "Limpopo",
                ],
                index=0,
            )
            turnover = st.number_input(
                "Annual turnover (ZAR)", min_value=0.0, value=float(default_profile["turnover"]), step=500_000.0
            )
            payroll = st.number_input(
                "Annual payroll (ZAR)", min_value=0.0, value=float(default_profile["payroll"]), step=100_000.0
            )
            black_ownership = st.slider(
                "Black ownership (%)", 0.0, 100.0, float(default_profile["black_ownership"]), 1.0
            )
            black_women_ownership = st.slider(
                "Black women ownership (%)",
                0.0,
                100.0,
                float(default_profile["black_women_ownership"]),
                1.0,
            )
            black_management = st.slider(
                "Black management (%)", 0.0, 100.0, float(default_profile["black_management"]), 1.0
            )
        with cols[1]:
            st.subheader("Contributions")
            skills_development_pct = st.number_input(
                "Skills development (% of payroll)",
                min_value=0.0,
                value=float(default_spend["skills_development_pct"]),
                step=0.1,
            )
            supplier_black_owned_pct = st.number_input(
                "Spend with ≥51% black-owned suppliers (% of total)",
                min_value=0.0,
                max_value=100.0,
                value=float(default_spend["supplier_black_owned_pct"]),
                step=1.0,
            )
            supplier_eme_qse_pct = st.number_input(
                "Spend with EMEs/QSEs (% of total)",
                min_value=0.0,
                max_value=100.0,
                value=float(default_spend["supplier_eme_qse_pct"]),
                step=1.0,
            )
            enterprise_dev_pct = st.number_input(
                "Enterprise & supplier development (% of NPAT)",
                min_value=0.0,
                value=float(default_spend["enterprise_dev_pct"]),
                step=0.1,
            )
            socio_economic_pct = st.number_input(
                "Socio-economic development (% of NPAT)",
                min_value=0.0,
                value=float(default_spend["socio_economic_pct"]),
                step=0.1,
            )
        submitted = st.form_submit_button("Calculate")

    if submitted:
        profile = {
            "company": company,
            "province": province,
            "turnover": turnover,
            "payroll": payroll,
            "black_ownership": black_ownership,
            "black_women_ownership": black_women_ownership,
            "black_management": black_management,
        }
        spend = {
            "skills_development_pct": skills_development_pct,
            "supplier_black_owned_pct": supplier_black_owned_pct,
            "supplier_eme_qse_pct": supplier_eme_qse_pct,
            "enterprise_dev_pct": enterprise_dev_pct,
            "socio_economic_pct": socio_economic_pct,
        }
        breakdown = calculate_bee_score(profile, spend)

        st.markdown("---")
        cols = st.columns([1, 1])
        with cols[0]:
            st.metric("Recognition level", breakdown["level"])
            st.metric(
                "Total points",
                f"{breakdown['total']:.1f}",
                help="Simplified SME/QSE weighting to 100 points",
            )
            st.metric("Enterprise size", breakdown["size"])
            if breakdown["discount_applied"]:
                st.warning("Ownership <10% triggered a one-level discount.")
        with cols[1]:
            st.markdown("**Quick recommendations**")
            st.write(
                "- Raise ownership/management for higher base points (especially QSE/Generic).\n"
                "- Target ~3% of payroll to skills development.\n"
                "- Increase spend with ≥51% black-owned suppliers (~40%) and EMEs/QSEs (~25%).\n"
                "- Allocate ~1% NPAT to enterprise & supplier development and socio-economic development."
            )

        st.markdown("### Score breakdown")
        df = pd.DataFrame(
            {
                "Element": [
                    "Ownership",
                    "Management",
                    "Skills",
                    "Procurement",
                    "Enterprise Dev",
                    "Socio-economic",
                ],
                "Points": [
                    breakdown["ownership"],
                    breakdown["management"],
                    breakdown["skills"],
                    breakdown["procurement"],
                    breakdown["enterprise_dev"],
                    breakdown["socio_economic"],
                ],
                "Max": [25, 15, 20, 20, 10, 10],
            }
        )
        df["% of max"] = (df["Points"] / df["Max"]) * 100
        df["Label"] = df.apply(lambda row: f"{row['Points']:.1f} / {row['Max']}", axis=1)

        max_domain = math.ceil(df["Max"].max() / 5) * 5

        base = (
            alt.Chart(df)
            .mark_bar(size=26, color="#e5e7eb")
            .encode(
                x=alt.X("Max:Q", title="Points", scale=alt.Scale(domain=[0, max_domain])),
                y=alt.Y("Element:N", sort="-x", title=""),
            )
        )

        actual = (
            alt.Chart(df)
            .mark_bar(size=20, color="#22c55e")
            .encode(
                x="Points:Q",
                y=alt.Y("Element:N", sort="-x"),
                tooltip=[
                    alt.Tooltip("Points:Q", format=".1f"),
                    alt.Tooltip("Max:Q", format=".0f"),
                    alt.Tooltip("% of max:Q", format=".0f"),
                ],
            )
        )

        labels = (
            alt.Chart(df)
            .mark_text(align="left", baseline="middle", dx=5, color="#0f172a")
            .encode(x="Points:Q", y=alt.Y("Element:N", sort="-x"), text="Label:N")
        )

        st.altair_chart(base + actual + labels, use_container_width=True)

        st.info(
            "Disclaimer: This is a planning tool. Confirm calculations with your verification agency and apply the correct sector code targets."
        )


if __name__ == "__main__":
    main()
