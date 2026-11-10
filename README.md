Smart Plant Watering System (ระบบรดน้ำต้นไม้อัตโนมัติ)
ใช้เซนเซอร์วัดความชื้นในดินเพื่อสั่งการปั๊มน้ำให้ทำงานเมื่อดินแห้งตามค่าที่กำหนด วัตถุประสงค์คือช่วยดูแลต้นไม้แทนผู้ปลูกและประหยัดทรัพยากรน้ำ

## BJT Common-Emitter DC Bias (ENG29 2121)

เว็บแอป Flask ขนาดเล็กสำหรับคำนวณจุดทำงานกระแสตรง (Q-point) ของวงจร BJT
Common-Emitter แบบ voltage-divider bias

- รับค่า V_CC, R1, R2, R_C, R_E, β และ V_BE
- แสดง I_B, I_C, I_E, V_B, V_C, V_E, V_CE พร้อมหน่วย
- ตรวจสอบและเตือนเมื่อวงจรอยู่ในย่าน cutoff หรือ saturation
- เปรียบเทียบผลกับวิธี approximate (เงื่อนไข βR_E ≥ 10R2)
- ตรวจสอบอินพุตและแสดงข้อความผิดพลาดโดยหน้าเว็บไม่ crash

### การติดตั้งและรัน

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

เปิดเบราว์เซอร์ที่ http://127.0.0.1:5000

### การทดสอบ

```powershell
.venv\Scripts\python -m unittest -v
```

### ค่าเริ่มต้นสำหรับ demo

| พารามิเตอร์ | ค่า |
|---|---|
| V_CC | 12 V |
| R1 | 47000 Ω |
| R2 | 10000 Ω |
| R_C | 2200 Ω |
| R_E | 1000 Ω |
| β | 150 |
| V_BE | 0.7 V |

ผลที่ควรได้: ย่าน **Active**, I_C ≈ 1.324 mA, V_CE ≈ 7.755 V และวิธี
approximate ต่างจาก exact ประมาณ 6.16% ในค่า I_C
