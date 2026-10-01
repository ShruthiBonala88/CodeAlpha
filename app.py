"""CodeAlpha Backend Internship - Task 1: Simple URL Shortener (Flask + SQLite)."""
import os
import re
import secrets
import sqlite3
import string
from urllib.parse import urlparse

from flask import Flask, g, jsonify, redirect, render_template, request

DATABASE = os.environ.get("DATABASE", "urls.db")
ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
CUSTOM_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
RESERVED = {"api", "static", "favicon.ico"}

app = Flask(__name__)


# ---------- database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config.get("DATABASE", DATABASE))
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(app.config.get("DATABASE", DATABASE)) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS urls (
                   id         INTEGER PRIMARY KEY AUTOINCREMENT,
                   short_code TEXT NOT NULL UNIQUE,
                   long_url   TEXT NOT NULL,
                   clicks     INTEGER NOT NULL DEFAULT 0,
                   created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
               )"""
        )


# ---------- helpers ----------
def is_valid_url(url):
    try:
        p = urlparse(url)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc) and len(url) <= 2048


def generate_code(db):
    for _ in range(10):
        code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
        if not db.execute("SELECT 1 FROM urls WHERE short_code = ?", (code,)).fetchone():
            return code
    raise RuntimeError("Could not generate a unique code")


def row_to_dict(row):
    return {
        "short_code": row["short_code"],
        "short_url": request.host_url + row["short_code"],
        "long_url": row["long_url"],
        "clicks": row["clicks"],
        "created_at": row["created_at"],
    }


# ---------- routes ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/shorten", methods=["POST"])
def shorten():
    data = request.get_json(silent=True) or {}
    long_url = (data.get("url") or "").strip()
    custom = (data.get("custom_code") or "").strip()

    if not long_url:
        return jsonify(error="'url' is required"), 400
    if not is_valid_url(long_url):
        return jsonify(error="Enter a valid http:// or https:// URL"), 400

    db = get_db()

    if custom:
        if not CUSTOM_CODE_RE.match(custom) or custom.lower() in RESERVED:
            return jsonify(error="Custom code must be 3-32 letters, numbers, - or _"), 400
        if db.execute("SELECT 1 FROM urls WHERE short_code = ?", (custom,)).fetchone():
            return jsonify(error="That custom code is already taken"), 409
        code = custom
    else:
        # Reuse the existing short code if this URL was already shortened.
        existing = db.execute(
            "SELECT * FROM urls WHERE long_url = ? ORDER BY id LIMIT 1", (long_url,)
        ).fetchone()
        if existing:
            return jsonify(row_to_dict(existing)), 200
        code = generate_code(db)

    db.execute("INSERT INTO urls (short_code, long_url) VALUES (?, ?)", (code, long_url))
    db.commit()
    row = db.execute("SELECT * FROM urls WHERE short_code = ?", (code,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/urls")
def list_urls():
    rows = get_db().execute("SELECT * FROM urls ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/urls/<code>")
def url_stats(code):
    row = get_db().execute("SELECT * FROM urls WHERE short_code = ?", (code,)).fetchone()
    if row is None:
        return jsonify(error="Short URL not found"), 404
    return jsonify(row_to_dict(row))


@app.route("/<code>")
def follow(code):
    db = get_db()
    row = db.execute("SELECT long_url FROM urls WHERE short_code = ?", (code,)).fetchone()
    if row is None:
        return render_template("index.html", not_found=code), 404
    db.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (code,))
    db.commit()
    return redirect(row["long_url"], code=302)


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
