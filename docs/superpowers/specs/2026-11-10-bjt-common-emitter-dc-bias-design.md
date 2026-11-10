# BJT Common-Emitter DC Bias Web App — Design (ENG29 2121)

## 1. เป้าหมายและเหตุผล

แอป Flask ขนาดเล็กที่ทำงานได้จริง สำหรับรายวิชา ENG29 2121 ใช้คำนวณ ตรวจสอบ
และเปรียบเทียบจุดทำงานกระแสตรง (Q-point) ของวงจร BJT Common-Emitter
แบบ voltage-divider bias

เหตุผล: เป็น deliverable ของ lab สั้น ต้องมี demo บน localhost และ commit ขึ้น
GitHub ภายในวันนี้ จึงเน้น "เล็กที่สุดที่ทำงานครบ" ไม่ใช่แอปวิศวกรรมเต็มรูปแบบ

## 2. ขอบเขต

**ทำ:**
- รับค่า V_CC (V), R1 (Ω), R2 (Ω), R_C (Ω), R_E (Ω), β, V_BE (V)
- คำนวณ Q-point ด้วยวิธี exact (Thevenin) พร้อมหน่วย
- คำนวณด้วยวิธี approximate (independent calculation) แล้วเปรียบเทียบ
- ตรวจสอบขอบเขตการทำงาน: cutoff / saturation / active พร้อมคำเตือน
- validate อินพุตและแสดงข้อผิดพลาดบนหน้าเดิมโดยไม่ crash
- เทสต์อัตโนมัติและรันบน localhost

**ไม่ทำ (non-goals):**
- AC analysis, transient analysis
- schematic editor / แก้วงจรบนหน้าเว็บ
- FET หรืออุปกรณ์อื่น
- ฐานข้อมูล, login, deploy ขึ้น cloud

**anti-goals** (แม้จะทำงานได้แต่ถือว่าล้มเหลว):
- ต้องแก้โค้ดหรือเดาค่าเพื่อให้ demo ผ่าน
- หน้าเว็บพังเมื่อผู้ใช้กรอกค่าผิด
- ผล approximate ถูกใช้ตัดสิน region แทนวิธี exact

## 3. แนวทางที่พิจารณา

| ทาง | ลักษณะ | ผล |
|---|---|---|
| **A. Server-rendered Flask (เลือก)** | หน้าเดียว, `POST` แล้วเรนเดอร์ HTML กลับมา, ตรรกะ pure module | ไม่มี JS, เทสต์ง่าย, demo เสถียร, ตรงกับ spec เดิม |
| B. Flask JSON API + fetch | แยก `/api/calculate` กับหน้าเว็บ | เพิ่ม JS และจัดการ error สองที่ เสี่ยงต่อ demo โดยไม่จำเป็น |
| C. Multi-page / schematic editor | ให้ผู้ใช้แก้วงจร | ขัด non-goals และเกินเวลา |

เลือก **A** เพราะเป็นวิธีมาตรฐานที่นิยมที่สุดสำหรับ lab และมีชิ้นส่วนน้อยที่สุด

## 4. การตัดสินใจที่ตกลงกัน

- UI ภาษาไทย + สัญลักษณ์วิศวกรรมอังกฤษ (เช่น "แรงดัน V_CC (V)", "Q-point")
- หน้าเดียว: `GET /` แสดงฟอร์ม, `POST /` คำนวณแล้วเรนเดอร์ผลในหน้าเดิม
- ค่าเริ่มต้นในฟอร์มเพื่อให้ demo ได้ทันที: V_CC=12, R1=47000, R2=10000,
  R_C=2200, R_E=1000, β=150, V_BE=0.7 (ผลคือ active)
- region ตัดสินจากวิธี exact เท่านั้น; approximate ใช้เปรียบเทียบเท่านั้น
- ใช้ `unittest` ตามสไตล์เดิมของ repo (`test_electrical.py`)
- ไม่แตะ `electrical.py` / `test_electrical.py` เดิม

## 5. สถาปัตยกรรมและไฟล์

```
bjt_bias.py           # pure engineering logic (ไม่มี Flask)
app.py                # Flask app factory + routes
templates/index.html  # ฟอร์ม + ผลลัพธ์ + ตารางเปรียบเทียบ
static/style.css      # จัดหน้าให้อ่านง่าย
test_bjt_bias.py      # เทสต์ตรรกะวิศวกรรม
test_app.py           # เทสต์ route (Flask test client)
requirements.txt      # Flask
README.md             # เพิ่มหัวข้อวิธีรัน/ทดสอบของ lab นี้
```

`app.py` ใช้ `create_app()` เพื่อให้เทสต์สร้าง app แยกได้ และมี
`app = create_app()` ท้ายไฟล์สำหรับ `python app.py`

## 6. สูตรและตรรกะ

### 6.1 วิธี Exact (Thevenin equivalent)

```
V_TH = V_CC * R2 / (R1 + R2)
R_TH = R1 * R2 / (R1 + R2)
I_B  = (V_TH - V_BE) / (R_TH + (β + 1) * R_E)
I_C  = β * I_B
I_E  = (β + 1) * I_B
V_E  = I_E * R_E
V_B  = V_E + V_BE
V_C  = V_CC - I_C * R_C
V_CE = V_C - V_E
```

### 6.2 วิธี Approximate (independent comparison)

เงื่อนไขใช้งาน: `β * R_E >= 10 * R2`

```
V_B  ≈ V_CC * R2 / (R1 + R2)
V_E  ≈ V_B - V_BE
I_E  ≈ V_E / R_E
I_C  ≈ I_E
V_C  ≈ V_CC - I_C * R_C
V_CE ≈ V_C - V_E
```

ถ้าเงื่อนไขไม่ผ่าน → แสดงผล approximate พร้อมป้าย "ไม่เข้าเงื่อนไข (ใช้เป็น
ตัวเปรียบเทียบไม่ได้)" และไม่คำนวณส่วนต่าง procent
ถ้า `V_E <= 0` → approximate ใช้ไม่ได้ (วงจรอยู่ใน cutoff) แสดง N/A

### 6.3 การตัดสิน region (จากวิธี exact)

- **Cutoff**: `V_TH < V_BE` หรือ `I_B <= 0`
  → clamp `I_B = I_C = I_E = 0`, `V_E = 0`, `V_C = V_CC`, `V_CE = V_CC`
  → เตือน "ทรานซิสเตอร์อยู่ในย่าน cutoff"
- **Saturation**: `V_CE <= V_CE,sat` (ใช้ 0.2 V)
  → เตือน "อยู่ในย่าน saturation" และแสดง
    `I_C,sat = (V_CC - 0.2) / (R_C + R_E)`
  → ค่าจากแบบจำลอง exact ยังแสดง แต่กำกับว่า "แบบจำลองเชิงเส้นใช้ไม่ได้ในช่วงนี้"
- **Active**: `I_B > 0` และ `V_CE > 0.2`

### 6.4 การเปรียบเทียบ

เมื่อทั้งสองวิธีใช้ได้และ `I_C(exact) > 0`:

```
diff_IC_%  = |I_C(approx) - I_C(exact)| / I_C(exact) * 100
diff_VCE_% = |V_CE(approx) - V_CE(exact)| / |V_CE(exact)| * 100
```

แสดงตาราง side-by-side: ค่า, exact, approximate, ต่างกัน (%)
พร้อมป้ายว่าเงื่อนไข `β R_E >= 10 R2` ผ่านหรือไม่ และค่า `β R_E / (10 R2)`

## 7. Validation

ตรวจก่อนคำนวณทั้งหมด; ผิดข้อใดข้อหนึ่ง → แสดงข้อความภาษาไทยบนหน้าเดิม
และคงค่าที่ผู้ใช้กรอกไว้

- `V_CC > 0`
- `R1, R2, R_C, R_E > 0`
- `β > 0` (แนะนำ >= 1 ในข้อความเตือน แต่ไม่บังคับ)
- `0 <= V_BE < V_CC`
- ค่าที่กรอกต้องเป็นตัวเลข; ถ้าแปลงไม่ได้ให้ข้อความ "กรุณากรอกเป็นตัวเลข"

`bjt_bias.py` โยน `ValueError` พร้อมข้อความภาษาไทย; `app.py` จับแล้วส่งต่อ
ให้ template (สไตล์เดียวกับ `electrical.py`)

## 8. หน้าเว็บ (หน้าเดียว)

```
┌──────────────────────────────────────────────┐
│  วงจร BJT Common-Emitter DC Bias (ENG29 2121)│
│  [ ฟอร์ม 7 ช่อง + ปุ่ม "คำนวณ" ]              │
├──────────────────────────────────────────────┤
│  สถานะ: [ Active ]  (เขียว/เหลือง/แดง)        │
│  Q-point: I_B, I_C, I_E (mA), V_BE, V_B,      │
│           V_C, V_E, V_CE (V)                  │
├──────────────────────────────────────────────┤
│  เปรียบเทียบ exact vs approximate             │
│  เงื่อนไข β R_E >= 10 R2: ผ่าน (อัตราส่วน x)  │
│  ตาราง: ปริมาณ | exact | approx | ต่าง (%)    │
├──────────────────────────────────────────────┤
│  คำเตือน / หมายเหตุ (ถ้ามี)                    │
└──────────────────────────────────────────────┘
```

- ไม่มี JavaScript; ใช้ HTML form + CSS ล้วน
- ค่าที่แสดง: กระแสเป็น mA (ทศนิยม 3 ตำแหน่ง), แรงดันเป็น V (ทศนิยม 3 ตำแหน่ง),
  ความต้านทานเป็น Ω
- ผลลัพธ์มีหน่วยกำกับทุกค่า

## 9. เทสต์

`test_bjt_bias.py` (ไม่ต้องใช้ Flask):
- ค่าที่รู้คำตอบ (เคส default: V_CC=12, R1=47k, R2=10k, R_C=2.2k, R_E=1k, β=150)
  → ตรวจ I_C, V_CE อยู่ในย่าน active และค่าตรงกับที่คำนวณมือ
- cutoff (เช่น R2 เล็กมากจน V_TH < V_BE) → region cutoff, I_C = 0
- saturation (เช่น R_C ใหญ่/β สูง) → region saturation, มี I_C,sat
- validation: V_CC <= 0, R ใด ๆ <= 0, β <= 0, V_BE >= V_CC → ValueError
- approximate: เงื่อนไขผ่าน → มี diff %, เงื่อนไขไม่ผ่าน → applicable = False

`test_app.py` (Flask test client):
- `GET /` → 200 และมีฟอร์ม
- `POST /` ค่าถูกต้อง → 200 และมีค่า Q-point/สถานะ
- `POST /` ค่าผิด (R1 = 0) → 200, แสดงข้อความ error, ไม่ crash
- `POST /` ค่าไม่ใช่ตัวเลข → 200, แสดงข้อความ error

## 10. Dependencies และคำสั่ง

- Python 3.12 (มีอยู่แล้ว)
- Flask (ติดตั้งใน `.venv` ซึ่ง gitignore ไว้แล้ว) + `requirements.txt`
- รันแอป: `python app.py` → http://127.0.0.1:5000
- รันเทสต์: `python -m unittest -v`

## 11. Demo และ commit

- demo: เปิด localhost, แสดงเคส default (active), เปลี่ยนค่าให้เป็น saturation
  และ cutoff อย่างละครั้ง, แสดงเคสอินพุตผิด
- commit ตาม TDD เป็นชุด (test → feat) แล้วปิดท้ายด้วย docs; อย่างน้อยหนึ่ง
  commit ขึ้น `origin/main` ภายในวันนี้

## 12. สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- ข้อความไทย/อังกฤษของ label และ warning (ให้สอดคล้องกันทั้งไฟล์)
- รูปแบบ CSS (ไม่ต้องมี library ภายนอก)
- จะแสดงค่ากระแสเป็น mA อย่างเดียว หรือมี A กำกับด้วย
- รายละเอียดเล็ก ๆ ของ layout ที่ไม่กระทบสูตรหรือขอบเขต

## 13. เกณฑ์ว่าเสร็จ

- `python -m unittest -v` ผ่านทั้งหมด
- `python app.py` เปิดได้ และเคส default แสดงผล active ถูกต้อง
- กรอกค่าผิดแล้วหน้าเว็บไม่ crash
- มีตารางเปรียบเทียบ exact vs approximate พร้อมเงื่อนไข
- commit ขึ้น GitHub แล้ว
