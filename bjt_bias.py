def validate_inputs(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> None:
    """ตรวจสอบความถูกต้องของค่าอินพุตวงจร BJT Common-Emitter"""
    if vcc <= 0:
        raise ValueError("แรงดัน V_CC ต้องมากกว่า 0")
    if r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0:
        raise ValueError("ค่าความต้านทานต้องมากกว่า 0 โอห์ม")
    if beta <= 0:
        raise ValueError("ค่า β ต้องมากกว่า 0")
    if vbe < 0 or vbe >= vcc:
        raise ValueError("ค่า V_BE ต้องอยู่ระหว่าง 0 ถึง V_CC")


def calculate_dc_bias(
    vcc: float,
    r1: float,
    r2: float,
    rc: float,
    re: float,
    beta: float,
    vbe: float,
) -> dict:
    """คำนวณจุดทำงาน Q-point ของวงจร BJT Common-Emitter แบบ voltage divider bias"""
    validate_inputs(vcc, r1, r2, rc, re, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)
    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    warnings: list[str] = []
    ic_sat = None

    if vth < vbe or ib <= 0:
        region = "cutoff"
        ib = ic = ie = 0.0
        ve = 0.0
        vb = vth
        vc = vcc
        vce = vcc
        warnings.append("ทรานซิสเตอร์อยู่ในย่าน cutoff (V_TH < V_BE หรือ I_B ≤ 0)")
    elif vce <= 0.2:
        region = "saturation"
        ic_sat = (vcc - 0.2) / (rc + re)
        warnings.append(
            "ทรานซิสเตอร์อยู่ในย่าน saturation (V_CE ≤ 0.2 V) "
            "— ค่า I_C จากแบบจำลองเชิงเส้นใช้ไม่ได้"
        )
    else:
        region = "active"

    ratio = beta * re / (10 * r2)
    approx_vb = vcc * r2 / (r1 + r2)
    approx_ve = approx_vb - vbe
    approx_ie = approx_ve / re
    approx_ic = approx_ie
    approx_vc = vcc - approx_ic * rc
    approx_vce = approx_vc - approx_ve

    if ratio < 1:
        applicable = False
        reason = "ไม่เข้าเงื่อนไข βR_E ≥ 10R2"
    elif approx_ve <= 0:
        applicable = False
        reason = "V_E ≤ 0 (วงจรอยู่ใน cutoff) ใช้วิธี approximate ไม่ได้"
        approx_vb = approx_ve = approx_ie = None
        approx_ic = approx_vc = approx_vce = None
    else:
        applicable = True
        reason = ""

    if applicable and ic > 0:
        ic_diff_pct = abs(approx_ic - ic) / ic * 100
        vce_diff_pct = abs(approx_vce - vce) / abs(vce) * 100
    else:
        ic_diff_pct = None
        vce_diff_pct = None

    return {
        "exact": {
            "vth": vth,
            "rth": rth,
            "ib": ib,
            "ic": ic,
            "ie": ie,
            "vb": vb,
            "ve": ve,
            "vc": vc,
            "vce": vce,
        },
        "region": region,
        "warnings": warnings,
        "ic_sat": ic_sat,
        "vce_sat": 0.2,
        "approximate": {
            "applicable": applicable,
            "reason": reason,
            "ratio": ratio,
            "vb": approx_vb,
            "ve": approx_ve,
            "ie": approx_ie,
            "ic": approx_ic,
            "vc": approx_vc,
            "vce": approx_vce,
        },
        "comparison": {
            "ic_diff_pct": ic_diff_pct,
            "vce_diff_pct": vce_diff_pct,
        },
    }
