from collections.abc import Mapping

from flask import Flask, render_template, request

from dc_bias import (
    calculate_emitter_bias,
    calculate_fixed_bias,
    calculate_voltage_divider_bias,
)

MODE_LABELS = {
    "voltage_divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}

DEFAULT_MODE = "voltage_divider"

MODE_FIELDS = {
    "voltage_divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

ALL_FIELDS = ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe")

FIELDS = MODE_FIELDS[DEFAULT_MODE]

RESISTANCE_FIELDS = ("r1", "r2", "rb", "rc", "re")

FIELD_LABELS = {
    "vcc": "V_CC",
    "r1": "R1",
    "r2": "R2",
    "rb": "R_B",
    "rc": "R_C",
    "re": "R_E",
    "beta": "β",
    "vbe": "V_BE",
}

DEFAULTS = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rb": "430",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

BASE_UNITS = {
    "vcc": "V",
    "r1": "Ω",
    "r2": "Ω",
    "rb": "Ω",
    "rc": "Ω",
    "re": "Ω",
    "beta": "–",
    "vbe": "V",
}

DEFAULT_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rb": "kΩ",
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


def parse_form(
    form: Mapping[str, str], mode: str = DEFAULT_MODE
) -> dict[str, float]:
    """Convert the HTML form amounts to base units for the selected mode."""
    if mode not in MODE_FIELDS:
        raise ValueError(f"Unknown bias mode '{mode}'.")

    values: dict[str, float] = {}
    for field in MODE_FIELDS[mode]:
        try:
            amount = float(form[field])
        except (KeyError, ValueError):
            raise ValueError("Please enter numbers in all fields.") from None
        unit = form.get(f"{field}_unit", BASE_UNITS[field])
        allowed_units = (
            ("kΩ", "Ω") if field in RESISTANCE_FIELDS else (BASE_UNITS[field],)
        )
        if unit not in allowed_units:
            raise ValueError("Please choose a valid unit.")
        values[field] = amount * 1000 if unit == "kΩ" else amount
    return values


def validate_values(values: Mapping[str, float], mode: str) -> None:
    """Validate only the positive inputs required by the active mode."""
    if mode not in MODE_FIELDS:
        raise ValueError(f"Unknown bias mode '{mode}'.")
    if values["vcc"] <= 0:
        raise ValueError("V_CC must be greater than 0")
    if values["beta"] <= 0:
        raise ValueError("β must be greater than 0")
    if values["vbe"] < 0 or values["vbe"] >= values["vcc"]:
        raise ValueError("V_BE must be between 0 and V_CC")
    for field in MODE_FIELDS[mode]:
        if field in RESISTANCE_FIELDS and values[field] <= 0:
            raise ValueError(f"{FIELD_LABELS[field]} must be greater than 0 Ω")


def form_units(form: Mapping[str, str]) -> dict[str, str]:
    return {
        field: form.get(f"{field}_unit", BASE_UNITS[field])
        for field in ALL_FIELDS
    }


def merged_form(form: Mapping[str, str]) -> dict[str, str]:
    """Keep submitted values while filling any hidden fields with defaults."""
    return {**DEFAULT_FORM, **dict(form)}


def calculate_for_mode(mode: str, values: Mapping[str, float]) -> dict:
    if mode == "fixed":
        result = calculate_fixed_bias(**values)
    elif mode == "emitter":
        result = calculate_emitter_bias(**values)
    elif mode == "voltage_divider":
        result = calculate_voltage_divider_bias(**values)
    else:
        raise ValueError(f"Unknown bias mode '{mode}'.")
    return result


def create_app() -> Flask:
    app = Flask(__name__)
    app.add_template_filter(format_resistance, "resistance")

    @app.get("/")
    def index():
        result = calculate_voltage_divider_bias(**parse_form(DEFAULT_FORM))
        return render_template(
            "index.html",
            form=DEFAULT_FORM,
            mode=DEFAULT_MODE,
            mode_labels=MODE_LABELS,
            units=DEFAULT_UNITS,
            result=result,
            error=None,
        )

    @app.post("/")
    def calculate():
        mode = request.form.get("mode", DEFAULT_MODE)
        label = MODE_LABELS.get(mode, mode)
        display_mode = mode if mode in MODE_LABELS else DEFAULT_MODE
        submitted = dict(request.form)
        form = merged_form(submitted)
        units = form_units(form)
        try:
            values = parse_form(submitted, mode)
            validate_values(values, mode)
            result = calculate_for_mode(mode, values)
        except ValueError as error:
            return render_template(
                "index.html",
                form=form,
                mode=display_mode,
                mode_labels=MODE_LABELS,
                units=units,
                result=None,
                error=f"{label}: {error}",
            )
        return render_template(
            "index.html",
            form=form,
            mode=display_mode,
            mode_labels=MODE_LABELS,
            units=units,
            result=result,
            error=None,
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
