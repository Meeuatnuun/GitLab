"""DC bias calculations for fixed, emitter, and voltage-divider BJT circuits.

Internal calculations use volts, amps, and ohms. Results are converted to
display units: microamps, milliamps, and volts.
"""

from bjt_bias import calculate_dc_bias as _calculate_voltage_divider

VCE_SAT = 0.2


def _require_common(vcc: float, beta: float, vbe: float) -> None:
    if vcc <= 0:
        raise ValueError("V_CC must be greater than 0")
    if beta <= 0:
        raise ValueError("β must be greater than 0")
    if vbe < 0 or vbe >= vcc:
        raise ValueError("V_BE must be between 0 and V_CC")


def _require_positive(**resistances: float) -> None:
    labels = {"rb": "R_B", "rc": "R_C", "re": "R_E"}
    for field, value in resistances.items():
        if value <= 0:
            raise ValueError(f"{labels[field]} must be greater than 0 Ω")


def _scale(value: float | None, factor: float) -> float | None:
    return None if value is None else value * factor


def _build_result(
    mode: str,
    vcc: float,
    rc: float,
    re: float,
    vbe: float,
    ib: float,
    ic: float,
    ie: float,
    vb: float,
    ve: float,
    vc: float,
    vce: float,
) -> dict:
    region = "active"
    warning = None

    if ib <= 0:
        region = "cutoff"
        ib = ic = ie = 0.0
        ve = 0.0
        vb = vbe
        vc = vcc
        vce = vcc
        warning = "Transistor is in the cutoff region (I_B ≤ 0)"
    elif vce <= VCE_SAT:
        region = "saturation"
        warning = (
            "Transistor is in the saturation region (V_CE ≤ 0.2 V) "
            "— the linear I_C model no longer applies"
        )

    ic_sat = (vcc - VCE_SAT) / (rc + re) if (rc + re) > 0 else None

    return {
        "mode": mode,
        "ib_ua": ib * 1e6,
        "ic_ma": ic * 1e3,
        "ie_ma": ie * 1e3,
        "vb_v": vb,
        "ve_v": ve,
        "vc_v": vc,
        "vce_v": vce,
        "region": region,
        "warning": warning,
        "ic_sat_ma": _scale(ic_sat, 1e3),
        "vce_sat_v": VCE_SAT,
        "approximate": None,
        "comparison": None,
    }


def calculate_fixed_bias(
    vcc: float,
    rb: float,
    rc: float,
    beta: float,
    vbe: float,
) -> dict:
    """Fixed bias: base resistor from V_CC to base, emitter at ground."""
    _require_common(vcc, beta, vbe)
    _require_positive(rb=rb, rc=rc)

    ib = (vcc - vbe) / rb
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = 0.0
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    return _build_result("fixed", vcc, rc, 0.0, vbe, ib, ic, ie, vb, ve, vc, vce)


def calculate_emitter_bias(
    vcc: float,
    rb: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> dict:
    """Single-supply emitter bias: R_B from V_CC to base and R_E to ground."""
    _require_common(vcc, beta, vbe)
    _require_positive(rb=rb, rc=rc, re=re)

    ib = (vcc - vbe) / (rb + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    return _build_result("emitter", vcc, rc, re, vbe, ib, ic, ie, vb, ve, vc, vce)


def calculate_voltage_divider_bias(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> dict:
    """Voltage-divider bias, delegated to the unchanged Lab 2 calculation."""
    raw = _calculate_voltage_divider(vcc, r1, r2, rc, re, beta, vbe)
    exact = raw["exact"]
    approximate = raw["approximate"]
    comparison = raw["comparison"]

    return {
        "mode": "voltage_divider",
        "ib_ua": exact["ib"] * 1e6,
        "ic_ma": exact["ic"] * 1e3,
        "ie_ma": exact["ie"] * 1e3,
        "vb_v": exact["vb"],
        "ve_v": exact["ve"],
        "vc_v": exact["vc"],
        "vce_v": exact["vce"],
        "region": raw["region"],
        "warning": " ".join(raw["warnings"]) if raw["warnings"] else None,
        "ic_sat_ma": _scale(raw["ic_sat"], 1e3),
        "vce_sat_v": raw["vce_sat"],
        "approximate": {
            "applicable": approximate["applicable"],
            "reason": approximate["reason"],
            "ratio": approximate["ratio"],
            "vb_v": approximate["vb"],
            "ve_v": approximate["ve"],
            "ie_ma": _scale(approximate["ie"], 1e3),
            "ic_ma": _scale(approximate["ic"], 1e3),
            "vc_v": approximate["vc"],
            "vce_v": approximate["vce"],
        },
        "comparison": comparison,
    }
