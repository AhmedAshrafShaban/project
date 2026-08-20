from flask import Blueprint, current_app, jsonify, request

from app.schemas.estimate import EstimateRequest, ValidationError
from app.services.preprocessing import to_feature_row

bp = Blueprint("api", __name__)


@bp.get("/health")
def health():
    service = current_app.extensions["model_service"]
    return jsonify({
        "status": "ok" if service.is_ready else "unavailable",
        "model_loaded": service.is_ready,
        "model_name": service.metrics.get("model_name"),
        "model_version": service.metrics.get("model_version"),
    })


@bp.get("/metrics")
def metrics():
    service = current_app.extensions["model_service"]
    return jsonify(service.metrics)


@bp.post("/estimate")
def estimate():
    service = current_app.extensions["model_service"]
    payload = request.get_json(silent=True) or {}

    try:
        req = EstimateRequest.from_json(payload)
    except ValidationError as exc:
        return jsonify({"error": "validation_failed", "fields": exc.errors}), 422

    row = to_feature_row(req)
    result = service.predict(row)

    return jsonify({
        "estimated_value": result["estimated_value"],
        "estimated_value_formatted": f"${result['estimated_value']:,.0f}",
        "currency": "USD",
        "range_low": result["range_low"],
        "range_high": result["range_high"],
        "neighborhood_used": result["neighborhood_used"],
        "model_name": service.metrics.get("model_name"),
        "model_version": service.metrics.get("model_version"),
        "top_factors": result["top_factors"],
    })
