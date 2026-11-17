# Lab 03 — BJT DC Bias Web App

A small Flask web application for calculating the DC operating point (Q-point) of a
BJT Common-Emitter circuit. Lab 03 extends the original Lab 02 voltage-divider
calculator with two additional bias methods and a mode-aware interface.

**Course:** ENG29 2121 — Computer Programming for Electrical Engineers

---

## 1. Project Overview

The app runs three Common-Emitter DC bias methods behind a single form. Selecting a
bias mode shows only that mode's required inputs, its own circuit diagram, and
mode-labelled results.

| Bias mode | Form value | Required inputs |
|---|---|---|
| Voltage Divider Bias | `voltage_divider` | `V_CC`, `R1`, `R2`, `R_C`, `R_E`, `β`, `V_BE` |
| Fixed Bias | `fixed` | `V_CC`, `R_B`, `R_C`, `β`, `V_BE` |
| Emitter Bias (single supply) | `emitter` | `V_CC`, `R_B`, `R_C`, `R_E`, `β`, `V_BE` |

Features:

- Unit-aware resistance inputs (`kΩ` or `Ω`), converted to ohms before calculation.
- Computes `I_B`, `I_C`, `I_E`, `V_B`, `V_C`, `V_E`, and `V_CE`, with display units.
- Operating-region detection: **active**, **cutoff**, or **saturation**, with warnings.
- Exact vs. approximate comparison for Voltage Divider Bias (`βR_E ≥ 10R2` condition).
- Parameter values rendered into a mode-specific SVG circuit diagram.
- Input validation that reports a clear, mode-prefixed error instead of crashing.
- A failed calculation clears earlier results — stale numbers are never left on screen.
- Switching modes marks existing results as stale until **Calculate DC Bias** is pressed.

**Stack:** Python 3.10+, Flask 3, Jinja2, vanilla JavaScript, CSS (no build step).

---

## 2. Setup & How to Run

### Prerequisites

- Python 3.10 or newer
- `pip`

### Install and start

```powershell
# 1. (Optional but recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install the only runtime dependency
pip install flask

# 3. Start the development server
python -m flask --app app run
```

Then open **<http://127.0.0.1:5000/>** in a browser.

`pip install -r requirements.txt` is equivalent to `pip install flask`
(the file pins `Flask>=3.0,<4`). `python app.py` also works and starts Flask in
debug mode.

### Run the unit tests

```powershell
python -m unittest -v
```

Expected: **39 tests, all passing** (`OK`).

---

## 3. Engineering Equations & Units

All internal calculations use **volts (V)**, **amps (A)**, and **ohms (Ω)**.
Conversion to display units happens only when building the result dictionary.

### 3.1 Notation

| Symbol | Meaning |
|---|---|
| `V_CC` | Collector supply voltage |
| `V_BE` | Base-emitter forward drop (default `0.70 V`) |
| `β` | Forward current gain `h_FE` |
| `R1`, `R2` | Voltage-divider resistors (upper / lower) |
| `R_B` | Base bias resistor (fixed and emitter bias) |
| `R_C` | Collector resistor |
| `R_E` | Emitter resistor |
| `V_TH`, `R_TH` | Thevenin equivalent of the divider |
| `V_CE(sat)` | Saturation threshold, fixed at `0.2 V` |

### 3.2 Voltage Divider Bias — exact method

Implemented in `bjt_bias.calculate_dc_bias()` and delegated to by
`dc_bias.calculate_voltage_divider_bias()` (Lab 2 code, unchanged).

```text
V_TH = V_CC · R2 / (R1 + R2)
R_TH = R1 · R2 / (R1 + R2)
I_B  = (V_TH − V_BE) / (R_TH + (β + 1)·R_E)
I_C  = β · I_B
I_E  = (β + 1)·I_B
V_E  = I_E · R_E
V_B  = V_E + V_BE
V_C  = V_CC − I_C · R_C
V_CE = V_C − V_E
```

### 3.3 Fixed Bias

Implemented in `dc_bias.calculate_fixed_bias()`. The emitter is tied directly to
ground, so `V_E = 0 V` exactly.

```text
I_B  = (V_CC − V_BE) / R_B
I_C  = β · I_B
I_E  = (β + 1)·I_B
V_E  = 0
V_B  = V_BE
V_C  = V_CC − I_C · R_C
V_CE = V_C
```

### 3.4 Emitter Bias (single supply)

Implemented in `dc_bias.calculate_emitter_bias()`. Note that `V_E` uses `I_E`,
not `I_C`.

```text
I_B  = (V_CC − V_BE) / (R_B + (β + 1)·R_E)
I_C  = β · I_B
I_E  = (β + 1)·I_B
V_E  = I_E · R_E
V_B  = V_E + V_BE
V_C  = V_CC − I_C · R_C
V_CE = V_C − V_E
```

### 3.5 Approximate method (Voltage Divider Bias only)

Shown as a comparison card when the divider mode is selected.

```text
ratio      = β · R_E / (10 · R2)        # method applies when ratio ≥ 1
V_B(approx) ≈ V_CC · R2 / (R1 + R2)
V_E(approx) = V_B(approx) − V_BE
I_E(approx) = V_E(approx) / R_E
I_C(approx) ≈ I_E(approx)
V_C(approx) = V_CC − I_C(approx) · R_C
V_CE(approx) = V_C(approx) − V_E(approx)
```

The card reports PASS/FAIL for `βR_E ≥ 10R2`, the ratio, and the percentage
difference in `I_C` and `V_CE` against the exact solution. Comparison values are
suppressed when the condition fails or the circuit is cut off.

### 3.6 Units and conversions

| Quantity | Form input | Internal unit | Display unit | Conversion |
|---|---|---|---|---|
| Resistance | `kΩ` or `Ω` | Ω | `kΩ` / `Ω` | `Ω = kΩ × 1000` |
| `V_CC`, `V_BE`, voltages | V | V | V | — |
| `I_B` | — | A | µA | `µA = A × 1 000 000` |
| `I_C`, `I_E` | — | A | mA | `mA = A × 1000` |

The resistance dropdowns offer **kΩ** and **Ω** only. A megohm resistor is entered
as its kΩ equivalent — for example, `1 MΩ` is entered as `1000 kΩ`, which converts
to `1 000 000 Ω` internally. Unit selection is validated server-side; an unexpected
unit string is rejected with `Please choose a valid unit.`

### 3.7 Input validation

Validation runs only on the fields required by the selected mode.

| Rule | Error message |
|---|---|
| `V_CC > 0` | `V_CC must be greater than 0` |
| `β > 0` | `β must be greater than 0` |
| `0 ≤ V_BE < V_CC` | `V_BE must be between 0 and V_CC` |
| Active-mode resistances `> 0` | `R_B must be greater than 0 Ω` (etc.) |
| All active fields numeric | `Please enter numbers in all fields.` |
| Known mode value | `Unknown bias mode '…'.` |

Errors are prefixed with the mode label, for example
`Fixed Bias: R_B must be greater than 0 Ω`, and are rendered with `role="alert"`.
On error, `result` is `None`, so **no previous result table is rendered**.

### 3.8 Operating-region checks

| Region | Condition | Behaviour |
|---|---|---|
| **Cutoff** | `I_B ≤ 0` (voltage divider also checks `V_TH < V_BE`) | Forces `I_C = I_E = 0`, `V_CE = V_CC`, adds a cutoff warning |
| **Saturation** | `V_CE ≤ 0.2 V` | Keeps the linear model, adds a saturation warning and reports `I_C(sat)` |
| **Active** | `V_CE > 0.2 V` | Normal forward-active operation |

Saturation current uses

```text
I_C(sat) = (V_CC − 0.2) / (R_C + R_E)
```

For Fixed Bias, `R_E` is passed as `0`, so the same expression reduces to
`(V_CC − 0.2) / R_C`.

---

## 4. Browser Acceptance Testing (A1–A5)

### 4.1 How the browser tooling connects

`opencode.json` declares a local Playwright MCP server:

```json
{
  "mcp": {
    "servers": {
      "playwright": {
        "type": "local",
        "command": ["npx", "-y", "@playwright/mcp@latest", "--browser", "chrome", "--isolated"]
      }
    }
  }
}
```

When connected, OpenCode starts that server, discovers its tools, and uses them to
open tabs, read accessibility snapshots, fill fields, submit forms, and capture
screenshots against the running Flask app.

> **Verification note:** in the environment used for these Lab 03 runs, the
> Playwright MCP server could not start because `npx` was not on the process PATH
> (`mcp connect failed … 'npx' is not recognized`). The acceptance cases below were
> therefore executed in OpenCode's built-in Chromium browser tool against the same
> URL. Installing Node.js/npm (or pointing `command` at an absolute `npx.cmd` path)
> restores Playwright MCP without any application change.

### 4.2 Test conditions

All cases use `V_CC = 12 V`, `R_C = 2.2 kΩ`, `β = 100`, `V_BE = 0.70 V`.
Each case was run by selecting the mode, taking a snapshot, submitting the form,
and taking a second snapshot plus a full-page screenshot.

| ID | Method | Inputs | Expected | Observed | Status |
|---|---|---|---|---|---|
| A1 | Voltage Divider Bias | `R1 = 100 kΩ`, `R2 = 22 kΩ`, `R_E = 1 kΩ` | `I_C = 1.23 mA`, `V_CE = 8.05 V` | `I_C = 1.23 mA`, `V_CE = 8.05 V` (active) | **PASS** |
| A2 | Fixed Bias | `R_B = 1 MΩ` (entered `1000 kΩ`) | `I_C = 1.13 mA`, `V_CE = 9.51 V` | `I_C = 1.13 mA`, `V_CE = 9.51 V` (active) | **PASS** |
| A3 | Emitter Bias | `R_B = 1 MΩ` (`1000 kΩ`), `R_E = 1 kΩ` | `I_C = 1.03 mA`, `V_CE = 8.71 V` | `I_C = 1.03 mA`, `V_CE = 8.71 V` (active) | **PASS** |
| A4 | Emitter Bias | `R_B = 1 MΩ` (`1000 kΩ`), `R_E = 2 kΩ` | `I_C` decreases (~`0.94 mA`), `V_CE = 8.03 V` | `I_C = 0.94 mA` (down from `1.03 mA`), `V_CE = 8.03 V` | **PASS** |
| A5 | Fixed Bias (invalid) | `R_B = 0` | Error `Fixed Bias: R_B must be greater than 0 Ω`, no old results | Exact error shown as an `alert`; results card replaced by “Enter values and press Calculate.” — 0 result tables | **PASS** |

A5 was deliberately run while A4's results were still displayed; after submitting,
the previous `I_C = 0.94 mA` / `V_CE = 8.03 V` table was gone, confirming the
error path does not leak stale output.

### 4.3 Reproducing the checks manually

1. Start the server (section 2) and open <http://127.0.0.1:5000/>.
2. Select a bias mode; confirm the input rows and circuit diagram switch.
3. Enter the inputs for A1–A4 and press **Calculate DC Bias**; compare `I_C` and
   `V_CE` with the table above.
4. Select **Fixed Bias**, enter `R_B = 0`, submit, and confirm the error message and
   that no results table remains.

---

## 5. AI Assistance & Human Verification Disclosure

This lab was built with AI assistance, then reviewed and verified by the student.

| Component | Origin |
|---|---|
| `dc_bias.py` — `calculate_fixed_bias()` and `calculate_emitter_bias()` | Generated with OpenCode AI |
| Unified result schema, region/warning handling, `I_C(sat)` helper | Generated with OpenCode AI |
| `app.py` mode metadata, per-mode field sets, dispatch, validation wiring | Generated with OpenCode AI |
| Mode selector UI, `data-modes` input rows, stale-result notice (`static/app.js`) | Generated with OpenCode AI |
| Mode-specific SVG circuit diagrams (Fixed and Emitter) and styling | Generated with OpenCode AI |
| This README draft | Generated with OpenCode AI |
| Lab 2 voltage-divider math (`bjt_bias.py`) | Pre-existing code, left unchanged |

| Verification performed by the student | Detail |
|---|---|
| DC equations | Reviewed every equation against course notes for all three modes |
| Unit conversions | Confirmed kΩ → Ω and A → mA / µA scaling |
| Independent hand calculations | Recomputed Q-points by hand and checked them against app output |
| Browser verification (A1–A5) | Confirmed each acceptance case in the browser and reviewed the observed values |

All AI-generated code is covered by the existing unittest suite
(`python -m unittest -v`, 39 tests passing). Browser runs for the acceptance table
were driven with OpenCode browser automation, and the observed values were checked
by the student against independent hand calculations. No application behaviour was
accepted without that review.

---

## 6. Project Structure

```text
.
├── app.py                  # Flask app, form parsing, validation, mode dispatch
├── dc_bias.py              # Fixed / Emitter / Voltage-divider DC calculations
├── bjt_bias.py             # Lab 2 voltage-divider math (unchanged)
├── electrical.py           # Ohm's-law DC analyzer (not used by the web app)
├── templates/
│   └── index.html          # Dashboard, mode selector, SVG circuit diagrams
├── static/
│   ├── app.js              # Mode switching, field hiding, stale-result notice
│   └── style.css           # Dashboard styling
├── test_app.py             # Flask route and validation tests
├── test_bjt_bias.py        # Lab 2 calculation tests
├── test_electrical.py      # Legacy analyzer tests
├── requirements.txt        # Flask>=3.0,<4
├── opencode.json           # Playwright MCP server configuration
└── docs/superpowers/       # Design specs and implementation plans
```

---

## 7. Lab 2 Notes (retained)

The original Lab 2 voltage-divider calculator remains fully functional and is the
default mode. Its documented demo values:

| Parameter | Value |
|---|---|
| `V_CC` | 12.0 V |
| `R1` | 100 kΩ |
| `R2` | 22 kΩ |
| `R_C` | 2.2 kΩ |
| `R_E` | 1.0 kΩ |
| `β` | 100 |
| `V_BE` | 0.70 V |

Expected result: **active** region, exact `V_CE ≈ 8.05 V`, `I_C ≈ 1.23 mA`,
`I_B ≈ 12.30 µA`. The approximate-method condition **fails** for this set
(ratio `0.45`).

<details>
<summary>Original Lab 2 wording (Thai)</summary>

เว็บแอป Flask ขนาดเล็กสำหรับคำนวณจุดทำงานกระแสตรง (Q-point) ของวงจร BJT
Common-Emitter แบบ voltage-divider bias

- รับค่า V_CC, R1, R2, R_C, R_E, β และ V_BE
- แสดง I_B, I_C, I_E, V_B, V_C, V_E, V_CE พร้อมหน่วย
- ตรวจสอบและเตือนเมื่อวงจรอยู่ในย่าน cutoff หรือ saturation
- เปรียบเทียบผลกับวิธี approximate (เงื่อนไข βR_E ≥ 10R2)
- ตรวจสอบอินพุตและแสดงข้อความผิดพลาดโดยหน้าเว็บไม่ crash

ช่องความต้านทานรับค่าได้ทั้ง kΩ และ Ω โดยระบบแปลงเป็นโอห์มก่อนคำนวณ

</details>

---

<details>
<summary>Appendix: unrelated legacy note retained from the original README</summary>

Smart Plant Watering System (ระบบรดน้ำต้นไม้อัตโนมัติ) — ใช้เซนเซอร์วัดความชื้นในดินเพื่อสั่งการปั๊มน้ำให้ทำงานเมื่อดินแห้งตามค่าที่กำหนด วัตถุประสงค์คือช่วยดูแลต้นไม้แทนผู้ปลูกและประหยัดทรัพยากรน้ำ

This text is not related to the Lab 03 BJT bias application; it is preserved here
so no previous content is lost.

</details>
