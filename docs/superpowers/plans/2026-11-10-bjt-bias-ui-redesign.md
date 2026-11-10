# BJT Bias Dashboard UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the BJT bias calculator page as a polished 3-column English dashboard matching the approved reference, with unit-aware inputs, live circuit values, and a clear region status.

**Architecture:** Keep `bjt_bias.py` as the pure calculation module and `app.py` as the Flask adapter. Add unit conversion at the adapter boundary so the engineering layer continues to receive volts and ohms. Replace the single-column template and CSS with a dashboard grid while preserving the inline SVG circuit and the required exact-vs-approximate comparison.

**Tech Stack:** Python 3.12, Flask 3.1, Jinja2, plain CSS, inline SVG, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-bias-ui-redesign.md`

## Global Constraints

- UI copy, validation errors, warnings, and approximate-method reasons are English.
- No JavaScript, no new dependencies, no database, no authentication.
- Do not change DC-bias formulas or numerical results in `calculate_dc_bias`.
- Do not modify `electrical.py` or `test_electrical.py`.
- Keep the required exact vs approximate comparison and `%` difference.
- Inputs reach `calculate_dc_bias` in base units: volts and ohms.
- Run tests with `.venv\Scripts\python -m unittest -v`.
- Work on `main`; push to `origin/main` at the end.

## Review Focus

1. **kΩ unit conversion** — `100` kΩ must reach the calculator as `100000` Ω, not `100`. Test: `TestParseForm.test_kilo_ohm_unit_multiplies_by_1000` in Task 2.
2. **Missing unit fallback** — a POST without `*_unit` must still use the base unit (Ω/V), so existing programmatic callers do not silently change scale. Test: `TestParseForm.test_missing_unit_defaults_to_base_unit` in Task 2.
3. **Unknown unit** — `r1_unit=MΩ` must produce a readable English error and HTTP 200, never a traceback. Tests: `TestParseForm.test_invalid_unit_raises` in Task 2 and `test_invalid_unit_shows_error` in Task 3.
4. **First-load dashboard** — `GET /` must render all three cards populated from the defaults, not an empty results card. Test: `test_get_index_shows_default_results` in Task 3.
5. **Invalid input layout** — a validation error must keep the dashboard and input card visible, show the English error, and omit the results status. Test: `test_zero_resistance_shows_validation_error` in Task 3.

---

### Task 1: English User-Facing Messages

**Files:**
- Modify: `bjt_bias.py:1-120`
- Test: `test_bjt_bias.py`, `test_app.py`

**Interfaces:**
- Consumes: existing `validate_inputs(...)` and `calculate_dc_bias(...)` signatures; no signature changes.
- Produces: the same functions with English `ValueError` messages, English cutoff/saturation warnings, and English approximate-method reasons.

- [ ] **Step 1: Write the failing message tests**

Add to `test_bjt_bias.py`:

```python
class TestEnglishMessages(unittest.TestCase):
    def test_validation_message_is_english(self):
        with self.assertRaises(ValueError) as context:
            validate_inputs(0, 47000, 10000, 2200, 1000, 150, 0.7)
        self.assertIn("greater than 0", str(context.exception))

    def test_cutoff_warning_is_english(self):
        result = calculate_dc_bias(**dict(DEFAULT, r2=1000))
        self.assertIn("cutoff region", result["warnings"][0])

    def test_approximation_reason_is_english(self):
        result = calculate_dc_bias(**dict(DEFAULT, re=100))
        self.assertIn("is not met", result["approximate"]["reason"])
```

Update the existing assertion in `test_app.py`:

```python
    def test_zero_resistance_shows_validation_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("greater than 0".encode(), response.data)
        self.assertNotIn(b"region-active", response.data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m unittest -v test_bjt_bias test_app`

Expected: FAIL — messages are still Thai.

- [ ] **Step 3: Translate the messages in `bjt_bias.py`**

Use these exact strings:

```python
if vcc <= 0:
    raise ValueError("V_CC must be greater than 0")
if r1 <= 0 or r2 <= 0 or rc <= 0 or re <= 0:
    raise ValueError("All resistance values must be greater than 0 Ω")
if beta <= 0:
    raise ValueError("β must be greater than 0")
if vbe < 0 or vbe >= vcc:
    raise ValueError("V_BE must be between 0 and V_CC")
```

```python
warnings.append("Transistor is in the cutoff region (V_TH < V_BE or I_B ≤ 0)")
```

```python
warnings.append(
    "Transistor is in the saturation region (V_CE ≤ 0.2 V) "
    "— the linear I_C model no longer applies"
)
```

```python
reason = "Condition βR_E ≥ 10R2 is not met"
```

```python
reason = "V_E ≤ 0 (circuit is in cutoff); the approximate method does not apply"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python -m unittest -v test_bjt_bias test_app`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add bjt_bias.py test_bjt_bias.py test_app.py
git commit -m "feat: translate user-facing bias messages to English"
```

---

### Task 2: Unit-Aware Parsing and Resistance Formatting

**Files:**
- Modify: `app.py:1-60`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `FIELDS`, `DEFAULTS` from the existing app.
- Produces:
  - `RESISTANCE_FIELDS: tuple[str, ...] = ("r1", "r2", "rc", "re")`
  - `BASE_UNITS: dict[str, str]` mapping each field to `"Ω"` or `"V"` (`"–"` for beta)
  - `DEFAULT_UNITS: dict[str, str]` with base units for now
  - `DEFAULT_FORM: dict[str, str]` = amounts plus `<field>_unit` keys
  - `form_units(form: Mapping[str, str]) -> dict[str, str]`
  - `parse_form(form: Mapping[str, str]) -> dict[str, float]` now multiplies resistance amounts by 1000 when the field's unit is `kΩ`
  - `format_resistance(value: str, unit: str = "Ω") -> str` converting to ohms first, then formatting

- [ ] **Step 1: Write the failing parser and formatter tests**

Replace `TestFormatResistance` in `test_app.py` and add `TestParseForm`:

```python
from app import create_app, format_resistance, parse_form


class TestFormatResistance(unittest.TestCase):
    def test_kilo_ohm_amount_formats_without_conversion(self):
        self.assertEqual(format_resistance("100", "kΩ"), "100 kΩ")
        self.assertEqual(format_resistance("2.2", "kΩ"), "2.2 kΩ")
        self.assertEqual(format_resistance("1.0", "kΩ"), "1.0 kΩ")

    def test_ohm_amount_converts_to_kilo_ohms(self):
        self.assertEqual(format_resistance("47000", "Ω"), "47 kΩ")
        self.assertEqual(format_resistance("2200", "Ω"), "2.2 kΩ")
        self.assertEqual(format_resistance("1000", "Ω"), "1.0 kΩ")

    def test_small_values_stay_in_ohms(self):
        self.assertEqual(format_resistance("470", "Ω"), "470 Ω")

    def test_invalid_value_passes_through(self):
        self.assertEqual(format_resistance("abc"), "abc")


class TestParseForm(unittest.TestCase):
    def setUp(self):
        self.base = {
            "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
            "re": "1", "beta": "100", "vbe": "0.7",
        }

    def test_kilo_ohm_unit_multiplies_by_1000(self):
        form = dict(
            self.base,
            r1="100", r1_unit="kΩ",
            r2="22", r2_unit="kΩ",
            rc="2.2", rc_unit="kΩ",
            re="1", re_unit="kΩ",
        )
        values = parse_form(form)
        self.assertAlmostEqual(values["r1"], 100000.0)
        self.assertAlmostEqual(values["r2"], 22000.0)
        self.assertAlmostEqual(values["rc"], 2200.0)
        self.assertAlmostEqual(values["re"], 1000.0)

    def test_ohm_unit_keeps_value(self):
        form = dict(self.base, r1="470", r1_unit="Ω")
        self.assertAlmostEqual(parse_form(form)["r1"], 470.0)

    def test_missing_unit_defaults_to_base_unit(self):
        values = parse_form(dict(self.base, r1="47000"))
        self.assertAlmostEqual(values["r1"], 47000.0)

    def test_invalid_unit_raises(self):
        with self.assertRaises(ValueError) as context:
            parse_form(dict(self.base, r1_unit="MΩ"))
        self.assertIn("valid unit", str(context.exception))
```

Update the parse-error test to English:

```python
    def test_non_numeric_input_shows_parse_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, vcc="abc"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("numbers".encode(), response.data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m unittest -v test_app`

Expected: FAIL — `parse_form` ignores units and `format_resistance` does not accept a unit.

- [ ] **Step 3: Implement unit handling in `app.py`**

Keep the existing `DEFAULTS` values unchanged in this task. Add:

```python
RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")

BASE_UNITS = {
    "vcc": "V", "r1": "Ω", "r2": "Ω", "rc": "Ω", "re": "Ω",
    "beta": "–", "vbe": "V",
}

DEFAULT_UNITS = dict(BASE_UNITS)
DEFAULT_FORM = {
    **DEFAULTS,
    **{f"{field}_unit": unit for field, unit in DEFAULT_UNITS.items()},
}
```

`parse_form` becomes:

```python
def parse_form(form: Mapping[str, str]) -> dict[str, float]:
    """Convert the HTML form amounts to base units for calculation."""
    values: dict[str, float] = {}
    for field in FIELDS:
        try:
            amount = float(form[field])
        except (KeyError, ValueError):
            raise ValueError("Please enter numbers in all fields.") from None
        unit = form.get(f"{field}_unit", BASE_UNITS[field])
        allowed_units = ("kΩ", "Ω") if field in RESISTANCE_FIELDS else (BASE_UNITS[field],)
        if unit not in allowed_units:
            raise ValueError("Please choose a valid unit.")
        values[field] = amount * 1000 if unit == "kΩ" else amount
    return values
```

`format_resistance` becomes:

```python
def format_resistance(value: str, unit: str = "Ω") -> str:
    """Format a resistance amount, converting kΩ input to ohms first."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    ohms = amount * 1000 if unit == "kΩ" else amount
    if ohms >= 1000:
        kilo = ohms / 1000
        if kilo < 10:
            return f"{kilo:.1f} kΩ"
        return f"{kilo:g} kΩ"
    return f"{ohms:g} Ω"
```

Add `form_units`:

```python
def form_units(form: Mapping[str, str]) -> dict[str, str]:
    return {
        field: form.get(f"{field}_unit", BASE_UNITS[field])
        for field in FIELDS
    }
```

In the routes, pass units to the template (the old template ignores the extra key until Task 3):

```python
return render_template(
    "index.html", form=DEFAULTS, units=DEFAULT_UNITS, result=None, error=None
)
```

For POST:

```python
units = form_units(request.form)
try:
    values = parse_form(request.form)
    result = calculate_dc_bias(**values)
except ValueError as error:
    return render_template(
        "index.html", form=request.form, units=units, result=None, error=str(error)
    )
return render_template(
    "index.html", form=request.form, units=units, result=result, error=None
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python -m unittest -v`

Expected: PASS. The old template still renders the diagram because `format_resistance` defaults to `Ω` and the default amounts remain in ohms.

- [ ] **Step 5: Commit**

```bash
git add app.py test_app.py
git commit -m "feat: add unit-aware input parsing and resistance formatting"
```

---

### Task 3: Dashboard Template and Styles

**Files:**
- Modify: `app.py` (`DEFAULTS`, `DEFAULT_UNITS`, `index` route)
- Modify: `templates/index.html` (full replacement)
- Modify: `static/style.css` (full replacement)
- Test: `test_app.py`

**Interfaces:**
- Consumes: `parse_form`, `form_units`, `format_resistance`, `calculate_dc_bias`, and the context keys `form`, `units`, `result`, `error`.
- Produces: a `GET /` and `POST /` that render the dashboard with three cards, a populated default result, and a status box using classes `status--active`, `status--cutoff`, `status--saturation`.

- [ ] **Step 1: Write the failing dashboard tests**

Replace the UI-facing tests in `test_app.py` with:

```python
class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_index_shows_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        for text in (
            "Input Parameters",
            "Circuit: Common-Emitter Amplifier",
            "DC Bias Results",
            "Calculate DC Bias",
        ):
            self.assertIn(text.encode(), response.data)

    def test_get_index_shows_default_results(self):
        response = self.client.get("/")
        self.assertIn(b"Active region", response.data)
        self.assertIn(b"8.05", response.data)
        self.assertIn(b"12.30", response.data)

    def test_diagram_shows_parameter_values(self):
        response = self.client.get("/")
        for text in ("100 kΩ", "22 kΩ", "2.2 kΩ", "1.0 kΩ"):
            self.assertIn(text.encode(), response.data)

    def test_diagram_updates_with_submitted_values(self):
        form = dict(
            VALID_FORM,
            r1="47", r1_unit="kΩ",
            r2="10", r2_unit="kΩ",
        )
        response = self.client.post("/", data=form)
        self.assertIn("47 kΩ".encode(), response.data)
        self.assertIn("10 kΩ".encode(), response.data)

    def test_post_valid_input_shows_active_q_point(self):
        response = self.client.post("/", data=VALID_FORM)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Active region", response.data)
        self.assertIn(b"1.23", response.data)

    def test_zero_resistance_shows_validation_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("greater than 0".encode(), response.data)
        self.assertNotIn(b"Active region", response.data)
        self.assertIn(b"Input Parameters", response.data)

    def test_non_numeric_input_shows_parse_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, vcc="abc"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("numbers".encode(), response.data)

    def test_invalid_unit_shows_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1_unit="MΩ"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("valid unit".encode(), response.data)

    def test_zero_vce_saturation_returns_page(self):
        form = dict(
            VALID_FORM, vcc="5", r1="1000", r1_unit="Ω",
            r2="100", r2_unit="Ω", rc="105.5", rc_unit="Ω",
            re="10", re_unit="Ω", beta="200", vbe="0",
        )
        response = self.client.post("/", data=form)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Saturation region", response.data)
```

Update `VALID_FORM` to the new display units:

```python
VALID_FORM = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1.0", "beta": "100", "vbe": "0.7",
    "vcc_unit": "V", "r1_unit": "kΩ", "r2_unit": "kΩ",
    "rc_unit": "kΩ", "re_unit": "kΩ", "vbe_unit": "V",
}
```

The saturation test above intentionally omits units; it must still work through the base-unit fallback.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m unittest -v test_app`

Expected: FAIL — the old Thai single-column template has none of the new headings, cards, or status text.

- [ ] **Step 3: Update defaults and the GET route in `app.py`**

```python
DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

DEFAULT_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "beta": "–",
    "vbe": "V",
}
```

`DEFAULT_FORM` already composes these two maps, so it updates automatically.

The GET route calculates the default result:

```python
@app.get("/")
def index():
    result = calculate_dc_bias(**parse_form(DEFAULT_FORM))
    return render_template(
        "index.html", form=DEFAULTS, units=DEFAULT_UNITS, result=result, error=None
    )
```

- [ ] **Step 4: Replace `templates/index.html` with the dashboard**

Structure the file with these sections. Use the existing SVG geometry and update labels to `{{ form.rX|resistance(units.rX) }}`. Set `<html lang="en">` and the title to `Lab 02: BJT DC Bias Web App`.

Header:

```html
<header class="page-header">
  <div class="brand">
    <svg class="chip-icon" viewBox="0 0 48 48" aria-hidden="true">
      <rect x="12" y="12" width="24" height="24" rx="4" fill="none" stroke="currentColor" stroke-width="2"/>
      <path d="M18 12V6M24 12V6M30 12V6M18 36v6M24 36v6M30 36v6M12 18H6M12 24H6M12 30H6M36 18h6M36 24h6M36 30h6" stroke="currentColor" stroke-width="2"/>
    </svg>
    <div>
      <h1>Lab 02: BJT DC Bias Web App</h1>
      <p class="subtitle">ENG29 2121 – Common Emitter (Voltage Divider Bias)</p>
    </div>
  </div>
  <div class="course-badge">
    <svg class="code-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 6 3 12l5 6M16 6l5 6-5 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span>Computer Programming for<br>Electrical Engineers</span>
  </div>
</header>
```

Card icons: use simple 24×24 inline SVGs with `fill="none" stroke="currentColor" stroke-width="2"`:
- input gear: `<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/>`
- circuit node: `<circle cx="6" cy="12" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="18" cy="18" r="2"/><path d="M8 12h4l4-6M12 12l4 6"/>`
- bar chart: `<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>`
- calculator button: `<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M8 6h8M8 11h2M12 11h2M16 11h2M8 15h2M12 15h2M16 15h2M8 19h6"/>`

Dashboard grid:

```html
<div class="dashboard">
  <section class="card input-card">...</section>
  <section class="card circuit-card">...</section>
  <section class="card results-card">...</section>
</div>
<section class="card comparison-card">...</section>
```

Input rows use this shape for each resistance field:

```html
<div class="field-row">
  <label for="r1">R<sub>1</sub> <span>(Upper Divider)</span></label>
  <input id="r1" name="r1" type="number" step="any" value="{{ form.r1 }}" required>
  <select name="r1_unit" aria-label="R1 unit">
    <option value="kΩ" {% if units.r1 == "kΩ" %}selected{% endif %}>kΩ</option>
    <option value="Ω" {% if units.r1 == "Ω" %}selected{% endif %}>Ω</option>
  </select>
</div>
```

For `vcc` and `vbe`, render a one-option select with `V`. For `beta`, render `<span class="unit-static">–</span>`.

The submit button must contain a calculator icon and the exact text `Calculate DC Bias`. Put the error block above the fields inside the input card:

```html
{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
```

Results table order and formatting:

```html
<table class="results-table">
  <tbody>
    <tr><th>V<sub>B</sub></th><td>{{ "%.2f"|format(result.exact.vb) }}</td><td>V</td></tr>
    <tr><th>V<sub>E</sub></th><td>{{ "%.2f"|format(result.exact.ve) }}</td><td>V</td></tr>
    <tr><th>V<sub>C</sub></th><td>{{ "%.2f"|format(result.exact.vc) }}</td><td>V</td></tr>
    <tr><th>V<sub>CE</sub></th><td>{{ "%.2f"|format(result.exact.vce) }}</td><td>V</td></tr>
    <tr><th>I<sub>B</sub></th><td>{{ "%.2f"|format(result.exact.ib * 1e6) }}</td><td>µA</td></tr>
    <tr><th>I<sub>C</sub></th><td>{{ "%.2f"|format(result.exact.ic * 1e3) }}</td><td>mA</td></tr>
    <tr><th>I<sub>E</sub></th><td>{{ "%.2f"|format(result.exact.ie * 1e3) }}</td><td>mA</td></tr>
  </tbody>
</table>
```

Status box:

```html
<div class="status status--{{ result.region }}">
  <svg class="status-icon" viewBox="0 0 24 24" aria-hidden="true">
    <path d="M20 6 9 17l-5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <div>
    <strong>{{ result.region|capitalize }} region</strong>
    {% if result.region == "active" %}
    <p>V<sub>CE</sub> = {{ "%.2f"|format(result.exact.vce) }} V &gt; 0.2 V (transistor in active region)</p>
    {% elif result.region == "cutoff" %}
    <p>I<sub>C</sub> = 0 A (transistor is off)</p>
    {% else %}
    <p>V<sub>CE</sub> ≤ 0.2 V — I<sub>C,sat</sub> = {{ "%.2f"|format(result.ic_sat * 1e3) }} mA</p>
    {% endif %}
  </div>
</div>
```

When `result` is missing (invalid POST), show `<p class="empty">Enter values and press Calculate.</p>` inside the results card, and do not render the comparison card.

Comparison card keeps 3-decimal values and shows a PASS/FAIL pill:

```html
<p class="condition">
  <strong>βR<sub>E</sub> ≥ 10R<sub>2</sub>:</strong>
  {% if result.approximate.ratio >= 1 %}
  <span class="pill pill--pass">PASS</span>
  {% else %}
  <span class="pill pill--fail">FAIL</span>
  {% endif %}
  (ratio {{ "%.2f"|format(result.approximate.ratio) }})
  {% if not result.approximate.applicable %}<span class="reason">— {{ result.approximate.reason }}</span>{% endif %}
</p>
```

Comparison table columns: `Quantity`, `Exact`, `Approximate`, `Diff (%)`; rows `I_C (mA)` and `V_CE (V)` using `%.3f` and `N/A` when `None`.

- [ ] **Step 5: Replace `static/style.css` with the dashboard styles**

Implement the visual system from the spec:

```css
:root {
  --bg: #eef3f7;
  --card: #ffffff;
  --text: #1b2a3a;
  --muted: #6b7a8c;
  --border: #d9e4ec;
  --primary: #0f6674;
  --primary-dark: #0d5c6b;
  --badge-bg: #dbeafe;
  --badge-text: #1e4f9c;
  --active-bg: #e8f7ec;
  --active-text: #1a7f37;
  --cutoff-bg: #fff6e0;
  --cutoff-text: #9a6700;
  --saturation-bg: #fdecea;
  --saturation-text: #b42318;
}
```

Required layout rules:

- `* { box-sizing: border-box; }`
- `body { margin: 0; background: var(--bg); color: var(--text); font-family: "Segoe UI", "Noto Sans Thai", Tahoma, sans-serif; line-height: 1.5; }`
- `main { max-width: 1200px; margin: 0 auto; padding: 1.5rem 1.25rem 3rem; }`
- `.page-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1.25rem; }`
- `.page-header h1 { margin: 0; font-size: 1.9rem; line-height: 1.2; color: #102a43; }`
- `.subtitle { margin: 0.15rem 0 0; color: var(--muted); }`
- `.brand { display: flex; align-items: center; gap: 1rem; }`
- `.chip-icon { width: 52px; height: 52px; color: var(--primary); }`
- `.course-badge { display: flex; align-items: center; gap: 0.6rem; background: var(--badge-bg); color: var(--badge-text); border-radius: 10px; padding: 0.7rem 1rem; font-weight: 600; line-height: 1.25; }`
- `.dashboard { display: grid; grid-template-columns: 1fr 1.35fr 1.1fr; gap: 1rem; align-items: start; }`
- `.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.1rem 1.15rem; box-shadow: 0 2px 6px rgba(21, 45, 70, 0.05); }`
- `.card-title { display: flex; align-items: center; gap: 0.5rem; color: var(--primary); font-size: 1.1rem; margin: 0 0 0.9rem; }`
- `.card-title svg { width: 20px; height: 20px; }`
- `.field-row { display: grid; grid-template-columns: minmax(0, 1fr) 5.6rem 4.2rem; gap: 0.45rem; align-items: center; margin-bottom: 0.7rem; }`
- `.field-row label { font-size: 0.86rem; color: var(--text); line-height: 1.25; }`
- `.field-row label span { color: var(--muted); font-size: 0.78rem; display: block; }`
- `.field-row input, .field-row select { width: 100%; padding: 0.45rem 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.9rem; }`
- `.field-row input:focus, .field-row select:focus { outline: 2px solid var(--primary); outline-offset: 1px; }`
- `.calculate-button { width: 100%; margin-top: 0.4rem; padding: 0.65rem 1rem; border: 0; border-radius: 7px; background: var(--primary-dark); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }`
- `.results-table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }`
- `.results-table th { text-align: left; font-weight: 500; color: var(--text); background: #eef6fb; padding: 0.45rem 0.6rem; }`
- `.results-table td { padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--border); }`
- `.results-table td:nth-child(2) { text-align: right; font-weight: 700; }`
- `.results-table td:last-child { text-align: right; color: var(--muted); width: 3rem; }`
- `.status { display: flex; gap: 0.6rem; align-items: flex-start; margin-top: 0.9rem; padding: 0.75rem 0.85rem; border-radius: 8px; border: 1px solid transparent; }`
- `.status strong { display: block; font-size: 0.95rem; }`
- `.status p { margin: 0.15rem 0 0; font-size: 0.82rem; }`
- `.status--active { background: var(--active-bg); color: var(--active-text); border-color: #b7e3c3; }`
- `.status--cutoff { background: var(--cutoff-bg); color: var(--cutoff-text); border-color: #f0d58a; }`
- `.status--saturation { background: var(--saturation-bg); color: var(--saturation-text); border-color: #f3b6b0; }`
- `.status-icon { width: 22px; height: 22px; flex: 0 0 22px; }`
- `.comparison-card { margin-top: 1rem; }`
- `.comparison-table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }`
- `.comparison-table th, .comparison-table td { padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--border); }`
- `.comparison-table th { text-align: left; color: var(--muted); font-weight: 600; }`
- `.comparison-table td:not(:first-child) { text-align: right; }`
- `.pill { display: inline-block; border-radius: 999px; padding: 0.05rem 0.55rem; font-size: 0.75rem; font-weight: 700; }`
- `.pill--pass { background: var(--active-bg); color: var(--active-text); }`
- `.pill--fail { background: var(--saturation-bg); color: var(--saturation-text); }`
- `.condition { margin: 0 0 0.8rem; color: var(--muted); }`
- `.reason { font-size: 0.85rem; }`
- `.empty { margin: 0.5rem 0; color: var(--muted); }`
- `.error { margin: 0 0 0.8rem; padding: 0.6rem 0.75rem; border-left: 4px solid var(--saturation-text); background: var(--saturation-bg); border-radius: 4px; color: var(--saturation-text); font-size: 0.88rem; }`
- `.circuit-card svg { display: block; width: 100%; max-width: 380px; height: auto; margin: 0 auto; }`
- `.circuit-card svg text { font-family: inherit; }`
- `.circuit-card svg .value { fill: var(--muted); font-size: 12px; }`
- Responsive: `@media (max-width: 980px) { .dashboard { grid-template-columns: 1fr; } }`
- Header responsiveness: `@media (max-width: 700px) { .page-header { flex-direction: column; align-items: flex-start; } }`

Keep the existing SVG `viewBox="0 0 360 400"` and geometry. Give the transistor circle `fill="#dbeafe"` and keep its stroke. Keep `V_CC = {{ form.vcc }} V`, `β = {{ form.beta }}` and the four `|resistance(units.rX)` labels.

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python -m unittest -v`

Expected: PASS. If `test_get_index_shows_default_results` fails on `8.05` or `12.30`, verify the defaults and the two-decimal filters against the computed values from Task 3 Step 3.

- [ ] **Step 7: Commit**

```bash
git add app.py templates/index.html static/style.css test_app.py
git commit -m "feat: redesign bias calculator dashboard"
```

---

### Task 4: Documentation, Visual Verification, and Push

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the README demo section**

Replace the old demo defaults with:

| Parameter | Value |
|---|---|
| V_CC | 12.0 V |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| R_C | 2.2 kΩ |
| R_E | 1.0 kΩ |
| β | 100 |
| V_BE | 0.70 V |

State that the page shows exact values: V_CE ≈ 8.05 V, I_C ≈ 1.23 mA, I_B ≈ 12.30 µA, and that the approximate condition is **not met** for these values (ratio 0.45).

Add one line that inputs accept kΩ or Ω and are converted to ohms before calculation.

- [ ] **Step 2: Run the full suite**

Run: `.venv\Scripts\python -m unittest -v`

Expected: all tests PASS.

- [ ] **Step 3: Verify visually in the in-app browser**

Open `http://127.0.0.1:5000`, confirm:
- three cards side by side at desktop width
- header with chip icon and course badge
- diagram labels `100 kΩ`, `22 kΩ`, `2.2 kΩ`, `1.0 kΩ`
- results show `V_CE 8.05 V`, `I_B 12.30 µA`, `I_C 1.23 mA`
- green **Active region** status
- comparison card shows **FAIL** with ratio 0.45
- browser width below 980px stacks the cards

Capture a screenshot for the report.

- [ ] **Step 4: Commit and push**

```bash
git add README.md
git commit -m "docs: update dashboard defaults and demo results"
git push origin main
```

Expected: push succeeds and `origin/main` matches local `HEAD`.

---

## Self-Review

- **Spec coverage:** layout, English copy, unit selects, defaults, circuit values, results formatting, status, comparison, responsive CSS, error state, tests, docs, and push all have tasks.
- **Type consistency:** `parse_form` still returns `dict[str, float]`; `format_resistance(value, unit="Ω")` is used by the template with the matching `units` context; `form_units` returns `dict[str, str]`; status classes match the template and CSS.
- **Review Focus:** each of the five risky inputs has a named test in the owning task.
- **Proportion:** tasks are four; the template/CSS task is larger because the whole page is one visual deliverable, but its steps split tests, template, and styles.
