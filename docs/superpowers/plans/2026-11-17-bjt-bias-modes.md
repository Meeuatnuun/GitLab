# BJT Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Fixed Bias and single-supply Emitter Bias modes alongside the existing Voltage Divider Bias without changing Lab 2 calculations.

**Architecture:** A new `dc_bias.py` exposes three mode functions with one flat, display-unit result schema. It delegates voltage-divider math to the untouched `bjt_bias.calculate_dc_bias`. `app.py` selects the mode, validates only its required fields, converts kΩ to Ω, and dispatches with if/elif. The template renders a mode selector, mode-specific input rows, mode-specific SVG diagrams, and mode-labeled results/errors.

**Tech Stack:** Python 3.10, Flask 3, Jinja2, vanilla JS, CSS.

**Spec:** User-approved plan in the 2026-11-17 conversation.

## Global Constraints

- Keep `bjt_bias.calculate_dc_bias` unchanged.
- Keep all existing tests untouched; do not add unittest or Playwright files.
- Fixed Bias: `I_B = (V_CC - V_BE) / R_B`, `V_E = 0 V`.
- Emitter Bias: `I_B = (V_CC - V_BE) / [R_B + (beta + 1) * R_E]`, `V_E = I_E * R_E`.
- Common: `I_C = beta * I_B`, `I_E = (beta + 1) * I_B`, `V_B = V_E + V_BE`, `V_C = V_CC - I_C * R_C`, `V_CE = V_C - V_E`.
- Results use `ib_ua`, `ic_ma`, `ie_ma`, `vb_v`, `ve_v`, `vc_v`, `vce_v`, plus `region` and `warning`.
- Errors must clear old results.
- Unknown modes and non-positive/missing/non-numeric inputs produce clear errors.

## Review Focus

- Voltage-divider regression: default 12 V / 100 kΩ / 22 kΩ / 2.2 kΩ / 1 kΩ / β 100 / V_BE 0.7 must still show V_CE 8.05 V, I_C 1.23 mA, I_B 12.30 µA.
- Fixed-bias emitter: must be drawn directly to ground and `V_E` must be exactly 0 V.
- Emitter-bias `V_E`: must use `I_E * R_E`, not `I_C * R_E`.
- Mode switching: hidden fields must not be required or submitted, and the diagram must match the selected mode.
- Error path: a failed calculation must not leave an earlier result visible.

### Task 1: Unified calculation module

**Files:** Create `dc_bias.py`.

- [ ] Add `calculate_fixed_bias(vcc, rb, rc, beta, vbe)`.
- [ ] Add `calculate_emitter_bias(vcc, rb, rc, re, beta, vbe)`.
- [ ] Add `calculate_voltage_divider_bias(vcc, r1, r2, rc, re, beta, vbe)` delegating to `bjt_bias.calculate_dc_bias`.
- [ ] Normalize all three to the shared flat schema and warnings.

### Task 2: Flask dispatch and validation

**Files:** Modify `app.py`.

- [ ] Add mode metadata, mode field sets, `rb` defaults/units.
- [ ] Keep `parse_form(form, mode="voltage_divider")` backward compatible.
- [ ] Validate only active-mode fields; convert kΩ to Ω; reject unknown modes.
- [ ] Dispatch with if/elif; render mode label; clear results on error.

### Task 3: Template, diagrams, JS, CSS

**Files:** Modify `templates/index.html`, `static/style.css`; create `static/app.js`.

- [ ] Add three-way mode selector.
- [ ] Tag input rows with `data-modes`; hide/disable irrelevant rows.
- [ ] Add Fixed Bias and Emitter Bias SVGs; keep Voltage Divider SVG.
- [ ] Show mode in results and errors; show comparison only for voltage divider.
- [ ] Toggle fields/diagrams and stale-result notice in JS.

### Task 4: Verify

- [ ] `python -m unittest -v` → all existing tests pass.
- [ ] Browser check: each mode, values, warnings, errors, diagrams, divider regression.
