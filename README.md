# CodeAlpha_URLShortener

Task 1 of the CodeAlpha Backend Development internship: a simple URL shortener built with **Flask** and **SQLite**, with a small web frontend.

## Features
- `POST /api/shorten` creates a short code for a long URL (random 6-character base62 code, or your own custom code)
- `GET /<code>` redirects (HTTP 302) to the original URL and counts the click
- `GET /api/urls/<code>` returns stats for one link; `GET /api/urls` lists the 50 most recent
- URL validation (http/https only), duplicate URLs reuse their existing code, collision-safe code generation
- Frontend at `/` to create links, copy them, and see recent ones

## Run it
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## API example
```bash
curl -X POST http://127.0.0.1:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.codealpha.tech"}'
```
Response:
```json
{"short_code": "aB3xYz", "short_url": "http://127.0.0.1:5000/aB3xYz",
 "long_url": "https://www.codealpha.tech", "clicks": 0, "created_at": "2026-10-01 10:00:00"}
```
Optional body field: `"custom_code": "my-link"`.

## Tests
```bash
pytest
```

## Project structure
```
app.py              Flask app, routes, SQLite access
templates/index.html  Frontend
test_app.py         Pytest suite
requirements.txt
```
