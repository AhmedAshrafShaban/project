"""App factory for the home-value-estimator API."""
import logging

from flask import Flask

from app.core.config import get_settings
from app.services.inference import ModelService


def create_app() -> Flask:
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    _register_cors(app, settings.cors_origins)

    # Load the model once, at startup, and stash it on the app so every
    # request handler can reach it via `current_app.extensions`.
    app.extensions["model_service"] = ModelService(
        model_path=settings.model_path,
        metrics_path=settings.metrics_path,
    )

    from app.api.routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


def _register_cors(app: Flask, allowed_origins: list[str]) -> None:
    """Minimal same-file CORS handling — no extra dependency required."""
    allowed = {o.strip() for o in allowed_origins if o.strip()}

    @app.after_request
    def add_cors_headers(response):
        origin = request_origin()
        if origin and (origin in allowed or "*" in allowed):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response


def request_origin():
    from flask import request
    return request.headers.get("Origin")
