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
| V_CC | 12.0 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| R_C | 2.2 kΩ |
| R_E | 1.0 kΩ |
| β | 100 |
| V_BE | 0.70 V |

ผลที่ควรได้: ย่าน **Active** โดยหน้าเว็บแสดงค่า exact V_CE ≈ 8.05 V,
I_C ≈ 1.23 mA และ I_B ≈ 12.30 µA ส่วนเงื่อนไข approximate **ไม่ผ่าน**
สำหรับค่าชุดนี้ (ratio 0.45)

ช่องความต้านทานรับค่าได้ทั้ง kΩ และ Ω โดยระบบแปลงเป็นโอห์มก่อนคำนวณ
