# careplans (Django app)

Drop-in conversion of the FastAPI `backend_api.py` + `care_plan_engine.py`
+ `Careplan.html` into a Django app. Same routes, same request/response
JSON shapes, same OpenAI-powered logic. Nothing in the care-plan generation
logic itself was changed — `care_plan_engine.py` was moved to
`services.py` as-is.

## 1. Copy the app in

Copy this whole `careplans/` folder into your Django project root (next to
`drugcards/`, `cara/`, etc.), so you get:

```
your_project/
    careplans/
        __init__.py
        apps.py
        services.py
        serializers.py
        views.py
        urls.py
        migrations/__init__.py
        templates/careplans/careplan.html
```

## 2. Install dependencies

```
pip install openai python-dotenv djangorestframework
```

(`djangorestframework` is assumed already installed since the rest of the
project is DRF-based — skip it if so.)

## 3. settings.py

```python
INSTALLED_APPS = [
    ...
    "rest_framework",   # if not already there
    "careplans",
]
```

Set your OpenAI key the same way you already do for `drugcards`/`cara`
(env var `OPENAI_API_KEY`, or however your project loads `.env`).
`services.py` still calls `load_dotenv()` and instantiates `OpenAI()`
lazily on first use, same as before.

## 4. Project urls.py

To keep the exact same paths as the FastAPI version
(`/api/v1/health`, `/api/v1/care-plans`, `/api/v1/care-plans/edit`,
`/api/v1/care-plans/affected-sections`, `/test`), mount at the root:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("", include("careplans.urls")),
]
```

If you'd rather namespace it like your other apps (e.g. everything under
`/careplans/...`), mount with a prefix instead — just know the frontend
HTML's `fetch("/api/v1/care-plans")` call is a relative path, so if you
add a prefix you'll need to update that one line in
`templates/careplans/careplan.html` (search for `fetch(`) to match.

## 5. Migrations

No models — nothing to migrate, `migrations/__init__.py` is just there so
Django recognizes the app cleanly. `python manage.py migrate` needs no
changes for this app.

## 6. CORS

The original FastAPI app added `CORSMiddleware` conditionally based on a
`CORS_ORIGINS` env var. That's dropped here on the assumption your Django
project already has `django-cors-headers` configured project-wide (as
your other apps likely rely on). Add `careplans`' routes to your existing
CORS allow-list if needed — no separate CORS setup lives inside this app.

## Routes (unchanged from the FastAPI version)

| Method | Path                                   | View                    |
|--------|-----------------------------------------|--------------------------|
| GET    | `/api/v1/health`                        | health check             |
| POST   | `/api/v1/care-plans`                    | generate new care plan   |
| POST   | `/api/v1/care-plans/edit`               | edit existing care plan  |
| POST   | `/api/v1/care-plans/affected-sections`  | preview affected sections|
| GET    | `/test`                                 | serves the HTML UI       |

## Notes on the one deliberate difference

FastAPI/Pydantic returns HTTP 422 on bad request bodies; DRF returns 400
by default for serializer validation errors. Everything else — status
codes, response envelopes (`{"data": ..., "meta": ...}`), the 502 on
internal failure, and all care-plan generation/edit behavior — is
identical to the original.
