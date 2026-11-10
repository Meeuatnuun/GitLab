from collections.abc import Mapping

from flask import Flask, render_template, request

from bjt_bias import calculate_dc_bias

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "2200",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


def format_resistance(value: str) -> str:
    """แปลงค่าความต้านทานเป็นข้อความ เช่น 47000 -> 47 kΩ"""
    try:
        ohms = float(value)
    except (TypeError, ValueError):
        return str(value)
    if ohms >= 1000:
        return f"{ohms / 1000:g} kΩ"
    return f"{ohms:g} Ω"


def parse_form(form: Mapping[str, str]) -> dict[str, float]:
    """แปลงค่าจากฟอร์ม HTML เป็นตัวเลขสำหรับคำนวณ"""
    values: dict[str, float] = {}
    for field in FIELDS:
        try:
            values[field] = float(form[field])
        except (KeyError, ValueError):
            raise ValueError("กรุณากรอกเป็นตัวเลขทั้งหมด") from None
    return values


def create_app() -> Flask:
    app = Flask(__name__)
    app.add_template_filter(format_resistance, "resistance")

    @app.get("/")
    def index():
        return render_template("index.html", form=DEFAULTS, result=None, error=None)

    @app.post("/")
    def calculate():
        try:
            values = parse_form(request.form)
            result = calculate_dc_bias(**values)
        except ValueError as error:
            return render_template(
                "index.html", form=request.form, result=None, error=str(error)
            )
        return render_template(
            "index.html", form=request.form, result=result, error=None
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
