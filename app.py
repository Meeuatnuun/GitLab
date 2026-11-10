from collections.abc import Mapping

from flask import Flask, render_template, request

from bjt_bias import calculate_dc_bias

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

RESISTANCE_FIELDS = ("r1", "r2", "rc", "re")

DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

BASE_UNITS = {
    "vcc": "V",
    "r1": "Ω",
    "r2": "Ω",
    "rc": "Ω",
    "re": "Ω",
    "beta": "–",
    "vbe": "V",
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

DEFAULT_FORM = {
    **DEFAULTS,
    **{f"{field}_unit": unit for field, unit in DEFAULT_UNITS.items()},
}


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


def form_units(form: Mapping[str, str]) -> dict[str, str]:
    return {
        field: form.get(f"{field}_unit", BASE_UNITS[field])
        for field in FIELDS
    }


def create_app() -> Flask:
    app = Flask(__name__)
    app.add_template_filter(format_resistance, "resistance")

    @app.get("/")
    def index():
        result = calculate_dc_bias(**parse_form(DEFAULT_FORM))
        return render_template(
            "index.html", form=DEFAULTS, units=DEFAULT_UNITS, result=result, error=None
        )

    @app.post("/")
    def calculate():
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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
