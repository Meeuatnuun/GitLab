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
