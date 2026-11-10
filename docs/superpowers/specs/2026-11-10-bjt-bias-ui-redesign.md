# BJT Bias Web App — Dashboard UI Redesign (Approach A)

**Date:** 2026-11-10
**Status:** Awaiting approval
**Scope:** Presentation + input units. No change to the DC-bias formulas.

## Intent

ทำให้หน้าจอของเว็บแอปดูเป็น dashboard ระดับ lab report ตามภาพอ้างอิง:
header มี identity ของ Lab, เนื้อหาแบ่ง 3 การ์ด (Input / Circuit / Results),
ตัวเลขอ่านง่าย และสถานะการทำงานเด่นชัด โดยยังคงผลคำนวณ exact เป็นแหล่งความจริง

## Goals

- หน้าตา 3 คอลัมน์ตามภาพ reference: Input Parameters | Circuit | DC Bias Results
- UI ภาษาอังกฤษทั้งหมด รวมข้อความ error และ warning
- ช่องกรอกมี dropdown หน่วย (V, kΩ/Ω, –) และแปลงเป็นหน่วยฐานก่อนคำนวณ
- ค่าเริ่มต้นตรงภาพ: V_CC 12.0 V, R1 100 kΩ, R2 22 kΩ, R_C 2.2 kΩ, R_E 1.0 kΩ, β 100, V_BE 0.70 V
- ผลลัพธ์ 2 ตำแหน่ง: V_B, V_E, V_C, V_CE (V), I_B (µA), I_C/I_E (mA)
- กล่องสถานะสีเขียว/เหลือง/แดง พร้อมเหตุผล เช่น `V_CE = 7.76 V > 0.2 V`
- ตาราง exact vs approximate + % ต่าง ยังอยู่ครบ (ข้อกำหนด lab) วางใต้การ์ดทั้ง 3 ใบเต็มความกว้าง
- Responsive: จอแคบเรียงเป็นการ์ดเดี่ยว

## Non-goals

- ไม่แก้สูตรหรือโครงสร้างผลลัพธ์ใน `calculate_dc_bias`
- ไม่เพิ่ม JavaScript, framework, ฐานข้อมูล หรือ authentication
- ไม่แตะ `electrical.py` / `test_electrical.py`
- ไม่ทำ AC/transient analysis หรือ schematic editor

## Approaches Considered

| Approach | Trade-off | Decision |
|---|---|---|
| A. Full dashboard redesign + English + unit selects | ตรงภาพที่สุด แต่ต้องแก้ template/CSS/parse/tests | **เลือก** |
| B. Layout ตามภาพ แต่คงภาษาไทยและกรอก Ω | ใกล้ภาพแต่ไม่ตรงรายละเอียด | ไม่เลือก |
| C. ปรับสี/ระยะห่างเท่านั้น | เสี่ยงน้อย แต่ไม่ได้บรรยากาศ dashboard | ไม่เลือก |

## Design

### 1. Page structure

```
<header>
  chip icon | Lab 02: BJT DC Bias Web App
             ENG29 2121 – Common Emitter (Voltage Divider Bias)
             [code icon] Computer Programming for Electrical Engineers
</header>

<div class="dashboard">
  <section class="card input-card">     Input Parameters
  <section class="card circuit-card">   Circuit: Common-Emitter Amplifier
  <section class="card results-card">   DC Bias Results
</div>

<section class="card comparison-card"> Exact vs Approximate
```

- CSS grid: `grid-template-columns: 1fr 1.35fr 1.1fr` on wide screens.
- `max-width: 1200px`; below ~980px the grid becomes one column.
- Card headers use inline SVG icons (gear, circuit node, bar chart) — no icon library.

### 2. Inputs and units

Each input is a row: label, numeric input, unit select.

| Field | Label | Default | Units |
|---|---|---|---|
| vcc | V_CC (Supply Voltage) | 12.0 | V |
| r1 | R1 (Upper Divider) | 100 | kΩ, Ω |
| r2 | R2 (Lower Divider) | 22 | kΩ, Ω |
| rc | R_C (Collector Resistor) | 2.2 | kΩ, Ω |
| re | R_E (Emitter Resistor) | 1.0 | kΩ, Ω |
| beta | β (Current Gain) | 100 | – (fixed) |
| vbe | V_BE (Base-Emitter Voltage) | 0.70 | V |

- `parse_form` reads `<field>` and optional `<field>_unit`.
- Resistance: `kΩ` multiplies by 1000; `Ω` uses the number as-is.
- Missing unit defaults to the base unit (`Ω` / `V`) so existing programmatic posts stay valid.
- Unit values are validated; an unknown unit raises the same user-facing parse error.
- `BJT` calculations still receive base units (V, Ω).

### 3. Circuit card

- Keep the existing inline SVG geometry.
- Restyle to match the reference: light-blue transistor fill, clean black strokes.
- Labels under each resistor show the live formatted value: R1 100 kΩ, R2 22 kΩ, R_C 2.2 kΩ, R_E 1.0 kΩ.
- `V_CC` and `β` remain bound to the submitted values.
- Formatting rule: `>= 1000 Ω` shows as kΩ; values below 10 kΩ keep one decimal (`2.2 kΩ`, `1.0 kΩ`), values `>= 10 kΩ` use no unnecessary decimal (`22 kΩ`, `100 kΩ`).

### 4. Results card

Rows in this order: V_B, V_E, V_C, V_CE, I_B, I_C, I_E.
- Voltages: 2 decimals + `V`
- I_B: 2 decimals + `µA` (`ib * 1e6`)
- I_C / I_E: 2 decimals + `mA` (`* 1e3`)
- Status box:
  - active: green, check icon, `Active region — V_CE = … V > 0.2 V`
  - cutoff: amber, `Cutoff region — I_C = 0 A`
  - saturation: red, `Saturation region — V_CE ≤ 0.2 V`, plus `I_C,sat`
- `I_C,sat` and warnings appear inside the status box, not as loose text.

### 5. Comparison card

- Full-width card below the dashboard.
- Condition line: `βR_E ≥ 10R2: PASS/FAIL (ratio 1.00)` + reason when inapplicable.
- Table columns: Quantity | Exact | Approximate | Diff (%).
- Values formatted to 3 decimals to keep engineering precision.

### 6. English copy

- All template text becomes English.
- Translate user-facing messages in `bjt_bias.py`:
  - validation errors
  - cutoff/saturation warnings
  - approximate-method reason strings
- No numerical or control-flow behavior changes.

### 7. Visual system

- Background `#eef3f7`; cards white, radius 12px, 1px border `#d9e4ec`, soft shadow.
- Primary teal `#0f6674`; button dark teal `#0d5c6b` with white text.
- Header badge light blue `#dbeafe` with dark blue text `#1e4f9c`.
- Result table label column tinted `#eef6fb`; values bold, right-aligned.
- Status colors: green `#e8f7ec / #1a7f37`, amber `#fff6e0 / #9a6700`, red `#fdecea / #b42318`.
- Font stack: `"Segoe UI", "Noto Sans Thai", Tahoma, sans-serif`; tabular numerals for tables.

## Files to Change

- `templates/index.html` — full restructure, English copy, icons, unit selects
- `static/style.css` — dashboard layout and visual system
- `app.py` — `DEFAULTS` with units, `parse_form` unit conversion, `format_resistance` rule
- `bjt_bias.py` — English user-facing strings only
- `test_app.py` — updated English/default expectations, unit-conversion tests
- `README.md` — update demo defaults and screenshot description

## Testing

- Existing engineering tests in `test_bjt_bias.py` stay green (no numeric changes).
- App tests updated for:
  - GET `/` shows the three cards and English headings
  - default diagram shows 100 kΩ / 22 kΩ / 2.2 kΩ / 1.0 kΩ
  - POST with `kΩ` converts correctly (e.g. `r1=100, r1_unit=kΩ` equals `100000 Ω`)
  - POST with no unit still works in base units
  - invalid input shows English error, HTTP 200
  - active / saturation / zero-V_CE paths still render
- `format_resistance`: 100000→`100 kΩ`, 2200→`2.2 kΩ`, 1000→`1.0 kΩ`, 470→`470 Ω`, invalid passthrough.
- Run full suite: `.venv\Scripts\python -m unittest -v`
- Visual check in the in-app browser at 1280px and narrow width.

## Rollout

Single commit after green suite, pushed to `origin/main`.
