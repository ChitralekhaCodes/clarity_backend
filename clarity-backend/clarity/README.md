# Clarity - Carbon Emissions Calculator & Regulator
BCA Project-I (BCA-308) | M.M. Institute of Computer Technology & Business Management, MM(DU) Mullana

Team: Bhumika (13250352), Charu (13250356), Chitralekha (13250359) | Guide: Dr. Shikha Verma

Backend: **Python + FastAPI + SQLAlchemy**, database: **PostgreSQL** (SQLite by default so it runs with zero setup),
authentication: **JWT**, tests: **Pytest**. A simple web frontend (HTML/JS + Chart.js) is included and served by the backend.

## Run it
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000** (website) or **http://127.0.0.1:8000/docs** (interactive API docs).
Default admin: `admin@clarity.local` / `admin123` (change via environment variables, see `.env.example`).

### Use PostgreSQL (as in the synopsis)
```bash
pip install psycopg2-binary
# create a database named clarity, then:
set DATABASE_URL=postgresql://postgres:password@localhost:5432/clarity     (Windows)
export DATABASE_URL=postgresql://postgres:password@localhost:5432/clarity  (Linux/Mac)
uvicorn app.main:app --reload
```
Tables and starter data are created automatically on first run.

### Run tests
```bash
pytest -q
```

## Project structure
| File | Synopsis module |
|---|---|
| `app/routers/auth.py`, `security.py` | Authentication & User Management (JWT) |
| `app/routers/activities.py` | Activity/Input Management |
| `app/models.py`, `seed.py`, `routers/admin.py` | Emission Factor Management, Administration |
| `app/services.py` -> `calculate_co2e` | Carbon Calculation Engine |
| `app/services.py` -> `evaluate_targets` + `routers/targets.py` | Regulation/Threshold Engine |
| `app/services.py` -> `recommend`, `ai_explanation` | Recommendation / AI Module (rule-based, optional AI) |
| `app/routers/dashboard.py` | Dashboard & Reporting (totals, trend, CSV) |
| `static/index.html` | Frontend (forms + charts) |

## Main API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | Sign up / log in (returns JWT) |
| GET | `/api/factors` | List emission factors |
| POST/GET | `/api/activities` | Add activity (auto CO2e calculation) / list history |
| PUT/GET | `/api/targets` | Set personal monthly target / list targets |
| GET | `/api/dashboard?month=YYYY-MM` | Totals, category breakdown, status, alerts, recommendations, trend |
| GET | `/api/report/csv?month=YYYY-MM` | Downloadable report |
| POST/PUT | `/api/admin/factors`, `/api/admin/thresholds` | Admin configuration |

**Calculation:** `CO2e (kg) = quantity x emission factor`. Each saved record keeps the factor value and version,
so results stay reproducible even if the factor is later changed.

**Note:** The seeded emission factors are approximate/illustrative. Replace them with official datasets
(CEA, EPA, DEFRA) and record the source and version, as stated in the synopsis. Results are estimates, not certified measurements.
