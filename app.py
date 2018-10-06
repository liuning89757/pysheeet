"""This is a simple cheatsheet webapp."""

import os

from flask import Flask, abort, send_from_directory
from flask_sslify import SSLify
from flask_seasurf import SeaSurf
from flask_talisman import Talisman

DIR = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.join(DIR, "docs", "_build", "html")


def find_key(token):
    """Find the key from the environment variable."""
    if token == os.environ.get("ACME_TOKEN"):
        return os.environ.get("ACME_KEY")
    for k, v in os.environ.items():
        if v == token and k.startswith("ACME_TOKEN_"):
            n = k.replace("ACME_TOKEN_", "")
            return os.environ.get("ACME_KEY_{}".format(n))


csp = {
    "default-src": "'none'",
    "style-src": ["'self'", "'unsafe-inline'"],
    "script-src": [
        "'self'",
        "*.cloudflare.com",
        "*.googletagmanager.com",
        "*.google-analytics.com",
        "'unsafe-inline'",
        "'unsafe-eval'",
    ],
    "form-action": "'self'",
    "base-uri": "'self'",
    "img-src": "*",
    "frame-src": "ghbtns.com",
    "frame-ancestors": "'none'",
    "object-src": "'none'",
}
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(16)
app.config["SESSION_COOKIE_NAME"] = "__Secure-session"
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["CSRF_COOKIE_NAME"] = "__Secure-csrf-token"
app.config["CSRF_COOKIE_HTTPONLY"] = True
app.config["CSRF_COOKIE_SECURE"] = True
csrf = SeaSurf(app)
talisman = Talisman(app, force_https=False, content_security_policy=csp)

if "DYNO" in os.environ:
    sslify = SSLify(app, skips=[".well-known"])


@app.after_request
def add_feature_policy(response):
    """Add feature policy."""
    response.headers["Feature-Policy"] = "geolocation 'none'"
    return response


@app.route("/<path:path>")
def static_proxy(path):
    """Find static files."""
    return send_from_directory(ROOT, path)


@app.route("/")
def index_redirection():
    """Redirecting index file."""
    return send_from_directory(ROOT, "index.html")


@csrf.exempt
@app.route("/.well-known/acme-challenge/<token>")
def acme(token):
    """Find the acme-key from environment variable."""
    key = find_key(token)
    if key is None:
        abort(404)
    return key


if __name__ == "__main__":
    app.run(debug=False)
