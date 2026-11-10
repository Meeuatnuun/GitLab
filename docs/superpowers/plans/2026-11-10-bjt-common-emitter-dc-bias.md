# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal working Flask app that computes the BJT Common-Emitter DC operating point, warns about cutoff/saturation, and compares the exact result with the approximate method.

**Architecture:** A pure engineering module (`bjt_bias.py`) holds validation, the exact Thevenin calculation, the approximate comparison, and region classification. A single server-rendered Flask route (`app.py`) parses form input and renders `templates/index.html`; CSS only, no JavaScript.

**Tech Stack:** Python 3.12, Flask 3.x, Jinja2 templates, plain CSS, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-common-emitter-dc-bias-design.md`

## Global Constraints

- Python 3.12; Flask `>=3.0,<4`; `unittest` only (no pytest).
- UI text is Thai; engineering symbols stay English (`V_CC`, `Q-point`, `saturation`, `cutoff`, `active`).
- Display: currents in mA to 3 decimals, voltages in V to 3 decimals, resistances in Ω.
- `V_CE,sat = 0.2 V` is fixed.
- Region verdict comes from the exact method only. The approximate method never decides the region.
- Approximate method applies only when `β * R_E >= 10 * R2`.
- No JavaScript, no external CSS/JS libraries, no database, no authentication.
- Do not modify `electrical.py` or `test_electrical.py`.
- Demo defaults: `vcc=12, r1=47000, r2=10000, rc=2200, re=1000, beta=150, vbe=0.7`.
- Commit messages use `test:`, `feat:`, or `docs:` prefixes.

## Review Focus

1. **Empty or non-numeric field** — a user clears a box or types `abc`; the page must re-render with a Thai error, HTTP 200, and no traceback. Test added in Task 5.
2. **`V_BE >= V_CC`, `β <= 0`, or any resistance `<= 0`** — must raise a readable validation error, never `ZeroDivisionError`. Tests added in Task 1.
3. **Bias below `V_BE`** (`V_TH < V_BE`) — must report cutoff with `I_C = 0`, `V_CE ≈ V_CC`, not a negative current. Test added in Task 2.
4. **Bias driving `V_CE <= 0.2 V`** — must report saturation and show `I_C,sat`, not silently report "active". Test added in Task 2.
5. **Approximation condition fails (`βR_E < 10R2`) or `V_E <= 0`** — must mark the comparison inapplicable and omit percent differences instead of dividing by zero. Tests added in Task 3.

---

## File Structure

| File | Responsibility |
|---|---|
| `bjt_bias.py` | Validation, exact Q-point, region classification, approximate comparison. No Flask imports. |
| `app.py` | `create_app()`, `GET /`, `POST /`, form parsing, error rendering. |
| `templates/index.html` | Form, Q-point table, region badge, comparison table, warnings. |
| `static/style.css` | Layout and region badge colors. |
| `test_bjt_bias.py` | Unit tests for `bjt_bias.py`. |
| `test_app.py` | Route tests via Flask test client. |
| `requirements.txt` | `Flask>=3.0,<4`. |
| `README.md` | Adds a Thai run/test section for this lab (existing content preserved). |

---

### Task 1: Input Validation

**Files:**
- Create: `bjt_bias.py`
- Test: `test_bjt_bias.py`

**Interfaces:**
- Produces: `validate_inputs(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> None`. Raises `ValueError` with a Thai message on the first invalid value; returns `None` when all values are valid.

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from bjt_bias import validate_inputs


class TestValidation(unittest.TestCase):
    def test_valid_inputs_pass(self):
        validate_inputs(12, 47000, 10000, 2200, 1000, 150, 0.7)

    def test_non_positive_vcc_raises(self):
        with self.assertRaises(ValueError):
            validate_inputs(0, 47000, 10000, 2200, 1000, 150, 0.7)

    def test_non_positive_resistance_raises(self):
        for index in range(1, 5):
            args = [12, 47000, 10000, 2200, 1000, 150, 0.7]
            args[index] = 0
            with self.assertRaises(ValueError):
                validate_inputs(*args)

    def test_non_positive_beta_raises(self):
        with self.assertRaises(ValueError):
            validate_inputs(12, 47000, 10000, 2200, 1000, 0, 0.7)

    def test_vbe_must_be_below_vcc(self):
        with self.assertRaises(ValueError):
            validate_inputs(12, 47000, 10000, 2200, 1000, 150, 12)

    def test_negative_vbe_raises(self):
        with self.assertRaises(ValueError):
            validate_inputs(12, 47000, 10000, 2200, 1000, 150, -0.1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest -v test_bjt_bias`
Expected: FAIL with `ModuleNotFoundError: No module named 'bjt_bias'`.

- [ ] **Step 3: Implement `validate_inputs` in `bjt_bias.py`**

Use Thai `ValueError` messages in the same style as `electrical.py`, for example:
`"แรงดัน V_CC ต้องมากกว่า 0"`, `"ค่าความต้านทานต้องมากกว่า 0 โอห์ม"`,
`"ค่า β ต้องมากกว่า 0"`, `"ค่า V_BE ต้องอยู่ระหว่าง 0 ถึง V_CC"`.
`V_BE` is valid when `0 <= vbe < vcc`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest -v test_bjt_bias`
Expected: 6 tests, all PASS.

- [ ] **Step 5: Commit**

```bash
git add bjt_bias.py test_bjt_bias.py
git commit -m "feat: add BJT bias input validation"
```

---

### Task 2: Exact Q-Point and Region Classification

**Files:**
- Modify: `bjt_bias.py`
- Test: `test_bjt_bias.py`

**Interfaces:**
- Consumes: `validate_inputs(...)` from Task 1.
- Produces: `calculate_dc_bias(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict` returning

```python
{
    "exact": {"vth": float, "rth": float, "ib": float, "ic": float, "ie": float,
              "vb": float, "ve": float, "vc": float, "vce": float},
    "region": "active" | "cutoff" | "saturation",
    "warnings": [str],      # empty when active
    "ic_sat": float | None, # set only for saturation
    "vce_sat": 0.2,
}
```

Task 3 adds `"approximate"` and `"comparison"` keys to this same dict.

- [ ] **Step 1: Write the failing tests**

Append to `test_bjt_bias.py`:

```python
from bjt_bias import calculate_dc_bias

DEFAULT = dict(vcc=12, r1=47000, r2=10000, rc=2200, re=1000, beta=150, vbe=0.7)


class TestExactOperatingPoint(unittest.TestCase):
    def test_default_case_is_active(self):
        result = calculate_dc_bias(**DEFAULT)
        exact = result["exact"]
        self.assertEqual(result["region"], "active")
        self.assertEqual(result["warnings"], [])
        self.assertAlmostEqual(exact["vth"], 2.1052631579, places=6)
        self.assertAlmostEqual(exact["rth"], 8245.614035, places=3)
        self.assertAlmostEqual(exact["ib"], 8.824501487e-06, delta=1e-9)
        self.assertAlmostEqual(exact["ic"], 0.001323675223, delta=1e-9)
        self.assertAlmostEqual(exact["ie"], 0.001332499725, delta=1e-9)
        self.assertAlmostEqual(exact["ve"], 1.332499725, delta=1e-6)
        self.assertAlmostEqual(exact["vb"], 2.032499725, delta=1e-6)
        self.assertAlmostEqual(exact["vc"], 9.087914509, delta=1e-6)
        self.assertAlmostEqual(exact["vce"], 7.755414785, delta=1e-6)

    def test_cutoff_when_vth_below_vbe(self):
        args = dict(DEFAULT, r2=1000)
        result = calculate_dc_bias(**args)
        exact = result["exact"]
        self.assertEqual(result["region"], "cutoff")
        self.assertAlmostEqual(exact["ib"], 0.0)
        self.assertAlmostEqual(exact["ic"], 0.0)
        self.assertAlmostEqual(exact["ie"], 0.0)
        self.assertAlmostEqual(exact["ve"], 0.0)
        self.assertAlmostEqual(exact["vc"], 12.0)
        self.assertAlmostEqual(exact["vce"], 12.0)
        self.assertAlmostEqual(exact["vb"], 0.25)
        self.assertTrue(any("cutoff" in warning for warning in result["warnings"]))

    def test_saturation_when_vce_at_or_below_limit(self):
        args = dict(DEFAULT, rc=10000)
        result = calculate_dc_bias(**args)
        self.assertEqual(result["region"], "saturation")
        self.assertAlmostEqual(result["exact"]["vce"], -2.569251955, delta=1e-6)
        self.assertAlmostEqual(result["ic_sat"], 0.001072727273, delta=1e-9)
        self.assertTrue(any("saturation" in warning for warning in result["warnings"]))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest -v test_bjt_bias`
Expected: FAIL with `ImportError`/`AttributeError` for `calculate_dc_bias`.

- [ ] **Step 3: Implement `calculate_dc_bias`**

Call `validate_inputs` first. Compute `vth`, `rth`, `ib`, `ic`, `ie`, `ve`, `vb`, `vc`, `vce` with the exact formulas from the spec. Then classify:

- cutoff when `vth < vbe` or `ib <= 0`: set `ib = ic = ie = 0`, `ve = 0`, `vb = vth`, `vc = vcc`, `vce = vcc`; append the warning `"ทรานซิสเตอร์อยู่ในย่าน cutoff (V_TH < V_BE หรือ I_B ≤ 0)"`.
- saturation when `vce <= 0.2`: compute `ic_sat = (vcc - 0.2) / (rc + re)`; append `"ทรานซิสเตอร์อยู่ในย่าน saturation (V_CE ≤ 0.2 V) — ค่า I_C จากแบบจำลองเชิงเส้นใช้ไม่ได้"`; keep the computed exact values in `"exact"` and put `ic_sat` in the result.
- otherwise `"active"` with `ic_sat = None`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest -v test_bjt_bias`
Expected: 9 tests, all PASS.

- [ ] **Step 5: Commit**

```bash
git add bjt_bias.py test_bjt_bias.py
git commit -m "feat: calculate exact Q-point and classify region"
```

---

### Task 3: Approximate Method and Comparison

**Files:**
- Modify: `bjt_bias.py`
- Test: `test_bjt_bias.py`

**Interfaces:**
- Produces: two extra keys on the `calculate_dc_bias` result:

```python
"approximate": {
    "applicable": bool,
    "reason": str,          # "" when applicable
    "ratio": float,         # beta * re / (10 * r2)
    "vb": float | None, "ve": float | None, "ie": float | None,
    "ic": float | None, "vc": float | None, "vce": float | None,
},
"comparison": {"ic_diff_pct": float | None, "vce_diff_pct": float | None},
```

- [ ] **Step 1: Write the failing tests**

Append to `test_bjt_bias.py`:

```python
class TestApproximateComparison(unittest.TestCase):
    def test_default_case_matches_approximation_closely(self):
        result = calculate_dc_bias(**DEFAULT)
        approx = result["approximate"]
        self.assertTrue(approx["applicable"])
        self.assertEqual(approx["reason"], "")
        self.assertAlmostEqual(approx["ratio"], 1.5, places=9)
        self.assertAlmostEqual(approx["vb"], 2.1052631579, places=6)
        self.assertAlmostEqual(approx["ve"], 1.4052631579, places=6)
        self.assertAlmostEqual(approx["ic"], 0.001405263158, delta=1e-9)
        self.assertAlmostEqual(approx["vce"], 7.503157895, places=6)
        comparison = result["comparison"]
        self.assertAlmostEqual(comparison["ic_diff_pct"], 6.16374269, delta=0.01)
        self.assertAlmostEqual(comparison["vce_diff_pct"], 3.25265504, delta=0.01)

    def test_condition_failure_marks_inapplicable(self):
        args = dict(DEFAULT, re=100)
        result = calculate_dc_bias(**args)
        approx = result["approximate"]
        self.assertFalse(approx["applicable"])
        self.assertIn("10R2", approx["reason"])
        self.assertIsNotNone(approx["ic"])
        self.assertIsNone(result["comparison"]["ic_diff_pct"])
        self.assertIsNone(result["comparison"]["vce_diff_pct"])

    def test_cutoff_case_approximation_is_unavailable(self):
        result = calculate_dc_bias(**dict(DEFAULT, r2=1000))
        approx = result["approximate"]
        self.assertFalse(approx["applicable"])
        self.assertIn("cutoff", approx["reason"])
        self.assertIsNone(approx["ve"])
        self.assertIsNone(result["comparison"]["ic_diff_pct"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest -v test_bjt_bias`
Expected: FAIL with `KeyError: 'approximate'`.

- [ ] **Step 3: Implement the approximate block**

Compute `ratio = beta * re / (10 * r2)`. Compute `vb`, `ve`, `ie`, `ic`, `vc`, `vce` with the approximate formulas. Set `applicable = ratio >= 1 and ve > 0`.

- If `ratio < 1`: `reason = "ไม่เข้าเงื่อนไข βR_E ≥ 10R2"`.
- If `ratio >= 1` but `ve <= 0`: `reason = "V_E ≤ 0 (วงจรอยู่ใน cutoff) ใช้วิธี approximate ไม่ได้"`, and set the approximate value fields to `None`.
- Otherwise `reason = ""`.

Set `comparison["ic_diff_pct"]` and `["vce_diff_pct"]` only when `applicable` is true and `exact["ic"] > 0`; otherwise both are `None`. Use the percent-difference formulas from the spec.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest -v test_bjt_bias`
Expected: 12 tests, all PASS.

- [ ] **Step 5: Commit**

```bash
git add bjt_bias.py test_bjt_bias.py
git commit -m "feat: add approximate bias comparison"
```

---

### Task 4: Flask App, Template, and CSS (Happy Path)

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`, `requirements.txt`, `test_app.py`

**Interfaces:**
- Consumes: `calculate_dc_bias(**values)` and its full result dict from Tasks 2–3.
- Produces: `create_app() -> Flask`; module-level `app = create_app()`; `parse_form(form: Mapping[str, str]) -> dict[str, float]`; `FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`; `DEFAULTS` mapping those keys to the demo defaults as strings.

- [ ] **Step 1: Create `requirements.txt` and the virtual environment**

`requirements.txt`:

```
Flask>=3.0,<4
```

Run: `python -m venv .venv`
Run: `.venv\Scripts\python -m pip install -r requirements.txt`

- [ ] **Step 2: Write the failing route tests**

Create `test_app.py`:

```python
import unittest

from app import create_app

VALID_FORM = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_index_shows_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Q-point".encode(), response.data)

    def test_post_valid_input_shows_active_q_point(self):
        response = self.client.post("/", data=VALID_FORM)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Active", response.data)
        self.assertIn(b"7.755", response.data)
        self.assertIn(b"1.324", response.data)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv\Scripts\python -m unittest -v test_app`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 4: Implement `app.py`**

`create_app()` builds `Flask(__name__)`, registers `GET /` (renders the form with `DEFAULTS`, `result=None`, `error=None`) and `POST /` (parses with `parse_form`, calls `calculate_dc_bias`, renders with `result`), and returns the app. `parse_form` converts each `FIELDS` entry with `float()` and raises `ValueError("กรุณากรอกเป็นตัวเลขทั้งหมด")` on the first failure. Keep `app = create_app()` and `if __name__ == "__main__": app.run(debug=True)` at module level.

- [ ] **Step 5: Implement `templates/index.html` and `static/style.css`**

The page must contain, in this order: title with `ENG29 2121`, a form posting to `/` with one labelled input per `FIELDS` entry (labels in Thai with the English symbol, e.g. `แรงดัน V_CC (V)`), a submit button `คำนวณ`, the region badge, a Q-point table, the comparison table, and warnings.

- Badge text is `{{ result.region|capitalize }}` with class `region-{{ result.region }}`; include the literal text `Q-point` in a heading.
- Q-point table rows: `I_B`, `I_C`, `I_E` in mA (3 decimals), `V_BE` (= `vbe`), `V_B`, `V_C`, `V_E`, `V_CE` in V (3 decimals). Format with `{{ "%.3f"|format(value) }}`.
- Comparison table columns: `ปริมาณ`, `Exact`, `Approximate`, `ต่าง (%)`. Show `I_C` and `V_CE` rows. Show `N/A` when a value or diff is `None`. Show the condition line `βR_E ≥ 10R2: ผ่าน/ไม่ผ่าน (อัตราส่วน {{ "%.2f"|format(approx.ratio) }})`, where the pass/fail word follows `approx.ratio >= 1`; when `approx.applicable` is false, also render `approx.reason` next to it.
- When `region == "saturation"`, show `I_C,sat` in mA; when `warnings` is non-empty, list each warning as a `<li>`.
- Render result/table/warning blocks only when `result` is defined.

CSS: plain stylesheet, readable max-width layout, and three badge colors (`.region-active`, `.region-cutoff`, `.region-saturation`).

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python -m unittest -v`
Expected: 14 tests, all PASS.

- [ ] **Step 7: Commit**

```bash
git add app.py templates/index.html static/style.css requirements.txt test_app.py
git commit -m "feat: add Flask UI for BJT bias calculator"
```

---

### Task 5: Form Error Handling

**Files:**
- Modify: `app.py`
- Test: `test_app.py`

**Interfaces:**
- Consumes: `parse_form`, `create_app`, and the `index.html` render context keys `form`, `result`, `error`.
- Produces: `POST /` always returns HTTP 200 with `error` set and `result=None` when input is invalid.

- [ ] **Step 1: Write the failing tests**

Append inside `TestApp`:

```python
    def test_zero_resistance_shows_validation_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, r1="0"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("มากกว่า 0".encode(), response.data)
        self.assertNotIn(b"region-active", response.data)

    def test_non_numeric_input_shows_parse_error(self):
        response = self.client.post("/", data=dict(VALID_FORM, vcc="abc"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode(), response.data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m unittest -v test_app`
Expected: FAIL — the route raises `ValueError` (test client propagates it).

- [ ] **Step 3: Handle errors in `POST /`**

Wrap parsing and calculation in `try/except ValueError as error`. On failure render `index.html` with `form=request.form`, `result=None`, `error=str(error)`. On success render with `form=request.form`, `result=result`, `error=None`. In the template, render `{{ error }}` in a visible error block above the form when `error` is set.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python -m unittest -v`
Expected: 16 tests, all PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py templates/index.html test_app.py
git commit -m "feat: show form errors without crashing"
```

---

### Task 6: README, Localhost Demo, and GitHub Commit

**Files:**
- Modify: `README.md`
- Add (untracked until now): `docs/`

- [ ] **Step 1: Add the lab section to `README.md`**

Append a Thai section `## BJT Common-Emitter DC Bias (ENG29 2121)` covering: what the app does, `python -m venv .venv`, `.venv\Scripts\python -m pip install -r requirements.txt`, `.venv\Scripts\python app.py`, open `http://127.0.0.1:5000`, `.venv\Scripts\python -m unittest -v`, and the demo default values.

- [ ] **Step 2: Run the full test suite**

Run: `.venv\Scripts\python -m unittest -v`
Expected: 16 tests, all PASS.

- [ ] **Step 3: Verify the app serves on localhost**

Run: `.venv\Scripts\python app.py` in the background.
Run: `(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000).StatusCode`
Expected: `200`. Stop the server afterwards.

- [ ] **Step 4: Commit docs and plan**

```bash
git add README.md docs/
git commit -m "docs: document BJT bias lab and implementation plan"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```

Expected: push succeeds and `origin/main` contains the commits. If authentication fails, stop and report the exact error; do not force-push.

---

## Self-Review

- Spec coverage: inputs, exact formulas, approximate formulas and condition, region rules, validation, UI, tests, demo defaults, README, and commit/push all map to Tasks 1–6.
- Step scan: every step names a file, a command, or exact expected output.
- Type consistency: `calculate_dc_bias` returns the same key names used by the template and tests (`exact`, `region`, `warnings`, `ic_sat`, `approximate`, `comparison`).
- Review Focus: all five lines have a named test in Tasks 1, 2, 3, or 5.
