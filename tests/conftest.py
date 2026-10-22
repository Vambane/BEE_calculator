from bee import CompanyProfile, ScoreInput, YesInput, YesTier


def generic_points(own, nv, mc, sd, pp, sdv, ed, sed, esd_bonus=0.0):
    return {
        "ownership": {"total": own, "net_value": nv},
        "management": {"main": mc},
        "skills": {"main": sd},
        "esd": {"pp": pp, "sd": sdv, "ed": ed, "bonus": esd_bonus},
        "sed": {"main": sed},
    }


def make(revenue, bo=30.0, points=None, tier=YesTier.NONE, **kw):
    return ScoreInput(
        profile=CompanyProfile(total_revenue=revenue, black_ownership_pct=bo),
        points=points or {},
        yes=YesInput(tier=tier),
        **kw,
    )
