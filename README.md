# Emberline — Forest Fire Weather Index Estimator

Emberline is a Flask web application that estimates the **Forest Weather Index (FWI)** from observed weather and fuel conditions. It provides a guided form, validates each input, lets users compare two regression models, and translates the numerical FWI prediction into a readable risk outlook.

> This application supports situational awareness only. It is not an emergency-warning system and must not replace local fire authorities, field procedures, or operational judgement.

## Highlights

- Two selectable regression models: Ridge Regression and Linear Regression
- Nine validated weather, fuel, and location inputs
- Clear risk bands: Low, Moderate, High, Very high, and Extreme
- Responsive Flask/Jinja interface
- Gunicorn entry point and Elastic Beanstalk WSGI configuration for AWS deployment

## How it works

1. Choose a prediction model.
2. Enter the latest observed weather and fuel conditions.
3. The app assembles the inputs in the training feature order, scales them with `models/scaler.pkl`, and sends them to the chosen trained model.
4. The predicted FWI is shown with an explanatory risk band.

The feature order is fixed and shared by both models:

`Temperature, RH, Ws, Rain, FFMC, DMC, ISI, Classes, Region`

## Models

| UI label | Model artifact | Identifier | Purpose |
| --- | --- | --- | --- |
| Ridge Regression | `models/ridge.pkl` | `ridge` | Default regularized regression estimator. |
| Linear Regression | `models/linreg.pkl` | `linear` | Unregularized linear regression estimator for comparison. |

Both models require the same nine scaled features. The shared `StandardScaler` is stored in `models/scaler.pkl`.

## Inputs

| Field | Meaning | Accepted range / values |
| --- | --- | --- |
| Temperature | Air temperature | 0–55 °C |
| RH | Relative humidity | 0–100 % |
| Ws | Wind speed | 0–100 km/h |
| Rain | Rainfall | 0–100 mm |
| FFMC | Fine Fuel Moisture Code | 0–101 |
| DMC | Duff Moisture Code | 0–500 |
| ISI | Initial Spread Index | 0–100 |
| Classes | Observed fire class used by the training data | `0` = not fire; `1` = fire |
| Region | Dataset region code | `0` = Bejaia; `1` = Sidi-Bel Abbes |

The input names and encodings must remain consistent with the data used to train the saved model artifacts. Model training material and the cleaned dataset are in [`notebooks/`](notebooks/).

## Risk interpretation

The app maps its continuous FWI estimate to these display bands:

| FWI estimate | Displayed outlook |
| --- | --- |
| Less than 5 | Low |
| 5 to less than 10 | Moderate |
| 10 to less than 20 | High |
| 20 to less than 30 | Very high |
| 30 or higher | Extreme |

These bands are a UI interpretation layer; they are not a substitute for local warning thresholds or an official fire-danger rating.

## Project structure

```text
.
├── application.py               # Flask app, validation, inference, and risk labels
├── models/
│   ├── scaler.pkl               # Fitted StandardScaler
│   ├── ridge.pkl                # Ridge Regression model
│   └── linreg.pkl               # Linear Regression model
├── templates/
│   ├── index.html               # Landing page
│   └── home.html                # Estimator form and result panel
├── static/
│   └── styles.css               # Responsive UI styling
├── notebooks/                   # Dataset and model-training notebooks
├── Procfile                     # Gunicorn process declaration
├── .ebextensions/python.config  # Elastic Beanstalk WSGI setting
└── requirements.txt             # Python dependencies
```

## Run locally

Prerequisites: Python 3.11+ and `pip`.

```powershell
git clone <your-repository-url>
cd ETEProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python application.py
```

Open `http://127.0.0.1:5000` in a browser. The development server enables Flask debug mode only when `application.py` is run directly.

For a production-like local run, use Gunicorn from a Unix-like environment:

```bash
gunicorn application:application
```

## Routes

| Route | Method | Description |
| --- | --- | --- |
| `/` | `GET` | Emberline landing page. |
| `/predictdata` | `GET` | Displays the estimator form. |
| `/predictdata` | `POST` | Validates the form, runs the selected model, and returns the prediction page. |

This is an HTML form workflow; it does not currently expose a JSON prediction API.

## AWS Elastic Beanstalk deployment

This repository is configured to expose the WSGI callable as `application:application`:

- [`Procfile`](Procfile) starts Gunicorn with `web: gunicorn application:application`.
- [`.ebextensions/python.config`](.ebextensions/python.config) sets the Elastic Beanstalk WSGI path to `application:application`.

Before deploying, ensure all three artifacts in `models/` are included in the source bundle and that `requirements.txt` is current. Do not include local virtual environments such as `eb-env/` or `.venv/`; they are ignored by `.gitignore`.

## Development notes

- Model loading uses paths relative to `application.py`, so the app can be started from another working directory.
- Invalid numeric values, out-of-range values, and unknown model identifiers are rejected before inference.
- The model selector uses an allow-list in `MODELS`; do not load a model file directly from a submitted form value.
- When adding a new model, place its artifact in `models/`, add a named entry to `MODELS` in `application.py`, and confirm it expects the same scaled feature order. If it does not, create a dedicated preprocessing path instead of reusing `scaler.pkl`.

## Verification

Run a quick syntax check after changes:

```powershell
python -m py_compile application.py
```

To manually test inference, open `/predictdata`, choose each model in turn, supply all nine inputs, and confirm the selected model name appears in the result panel.

## License

No license file is currently included. Add one before distributing or open-sourcing the project.
