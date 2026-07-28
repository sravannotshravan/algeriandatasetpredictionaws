from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from flask import Flask, render_template, request


BASE_DIR = Path(__file__).resolve().parent

application = Flask(__name__)
app = application


with (BASE_DIR / "models" / "ridge.pkl").open("rb") as model_file:
    ridge_model = pickle.load(model_file)
with (BASE_DIR / "models" / "linreg.pkl").open("rb") as model_file:
    linear_model = pickle.load(model_file)
with (BASE_DIR / "models" / "scaler.pkl").open("rb") as scaler_file:
    standard_scaler = pickle.load(scaler_file)

MODELS = {
    "ridge": {"label": "Ridge Regression", "model": ridge_model},
    "linear": {"label": "Linear Regression", "model": linear_model},
}


FIELD_SPECS = (
    ("Temperature", "Temperature", "°C", 0, 55),
    ("RH", "Relative humidity", "%", 0, 100),
    ("Ws", "Wind speed", "km/h", 0, 100),
    ("Rain", "Rainfall", "mm", 0, 100),
    ("FFMC", "Fine fuel moisture code", "0–101", 0, 101),
    ("DMC", "Duff moisture code", "index", 0, 500),
    ("ISI", "Initial spread index", "index", 0, 100),
    ("Classes", "Fire observation", "0 or 1", 0, 1),
    ("Region", "Forest region", "0 or 1", 0, 1),
)


def empty_form_data():
    return {name: "" for name, *_ in FIELD_SPECS}


def classify_fire_risk(fwi):
    """Return an interpretable label for the model's continuous FWI estimate."""
    if fwi < 5:
        return "Low", "low", "Conditions are generally stable. Continue routine monitoring."
    if fwi < 10:
        return "Moderate", "moderate", "Stay alert as dry fuel and wind can raise risk quickly."
    if fwi < 20:
        return "High", "high", "Elevated fire-weather conditions. Prepare prevention measures."
    if fwi < 30:
        return "Very high", "very-high", "Severe fire-weather conditions. Restrict ignition sources."
    return "Extreme", "extreme", "Critical fire-weather conditions. Follow local emergency guidance."


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predictdata", methods=["GET", "POST"])
def predict_datapoint():
    form_data = empty_form_data()
    errors = {}
    selected_model = "ridge"

    if request.method == "POST":
        form_data = {name: request.form.get(name, "").strip() for name, *_ in FIELD_SPECS}
        selected_model = request.form.get("model", "ridge")
        values = []

        if selected_model not in MODELS:
            errors["model"] = "Choose one of the available models."
            selected_model = "ridge"

        for name, label, _unit, minimum, maximum in FIELD_SPECS:
            raw_value = form_data[name]
            try:
                value = float(raw_value)
                if not np.isfinite(value):
                    raise ValueError
                if not minimum <= value <= maximum:
                    errors[name] = f"Enter a value from {minimum:g} to {maximum:g}."
                values.append(value)
            except ValueError:
                errors[name] = f"Enter a valid {label.lower()}."

        if not errors:
            feature_names = [name for name, *_ in FIELD_SPECS]
            model_input = pd.DataFrame([values], columns=feature_names)
            scaled_data = standard_scaler.transform(model_input)
            prediction = float(MODELS[selected_model]["model"].predict(scaled_data)[0])
            risk_label, risk_key, guidance = classify_fire_risk(prediction)
            return render_template(
                "home.html",
                form_data=form_data,
                selected_model=selected_model,
                model_options=MODELS,
                model_label=MODELS[selected_model]["label"],
                result=round(prediction, 2),
                risk_label=risk_label,
                risk_key=risk_key,
                guidance=guidance,
                errors=errors,
            )

    return render_template(
        "home.html",
        form_data=form_data,
        selected_model=selected_model,
        model_options=MODELS,
        errors=errors,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
