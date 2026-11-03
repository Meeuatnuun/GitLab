def analyze_dc(voltage_v: float, resistance_ohm: float) -> dict[str, float]:
    """คำนวณกระแสและกำลังไฟฟ้าของวงจร DC ตามกฎของโอห์ม"""
    if resistance_ohm <= 0:
        raise ValueError("ค่าความต้านทานต้องมากกว่า 0 โอห์ม")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


if __name__ == "__main__":
    try:
        voltage_v = float(input("ป้อนแรงดันไฟฟ้า (V): "))
        resistance_ohm = float(input("ป้อนค่าความต้านทาน (Ohm): "))
        result = analyze_dc(voltage_v, resistance_ohm)

        print(f"กระแสไฟฟ้า: {result['current_a']:.2f} A")
        print(f"กำลังไฟฟ้า: {result['power_w']:.2f} W")
    except ValueError as error:
        print(f"ข้อมูลไม่ถูกต้อง: {error}")
