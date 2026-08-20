import json
import logging

import joblib
import pandas as pd

logger = logging.getLogger(__name__)


class ModelService:
    """
    Loads the trained sklearn Pipeline + its metrics once at process
    startup, and exposes a small predict() API used by the /estimate route.
    """

    def __init__(self, model_path: str, metrics_path: str):
        self.model_path = model_path
        self.metrics_path = metrics_path
        self.pipeline = None
        self.metrics = {}
        self.known_neighborhoods = []
        self._load()

    def _load(self):
        logger.info("Loading model pipeline from %s", self.model_path)
        self.pipeline = joblib.load(self.model_path)

        with open(self.metrics_path) as f:
            self.metrics = json.load(f)

        try:
            ohe = self.pipeline.named_steps["prep"].named_transformers_["cat"].named_steps["ohe"]
            self.known_neighborhoods = list(ohe.categories_[0])
        except Exception:  # pragma: no cover - defensive, shouldn't happen with our pipeline
            logger.warning("Could not read neighborhood categories from the pipeline.")

        logger.info(
            "Model loaded: %s (R2=%.3f, MAE=%.0f)",
            self.metrics.get("model_name"),
            self.metrics.get("r2", 0),
            self.metrics.get("mae", 0),
        )

    @property
    def is_ready(self) -> bool:
        return self.pipeline is not None

    def predict(self, row: pd.DataFrame) -> dict:
        neighborhood_used = row.at[0, "neighborhood"]
        if self.known_neighborhoods and neighborhood_used not in self.known_neighborhoods:
            row.at[0, "neighborhood"] = "__unseen__"  # OHE(handle_unknown="ignore") zeros it out
            neighborhood_used = "other"

        point_estimate = float(self.pipeline.predict(row)[0])

        rmse = float(self.metrics.get("rmse", 0))
        low = max(point_estimate - rmse, 0)
        high = point_estimate + rmse

        return {
            "estimated_value": round(point_estimate, -2),
            "range_low": round(low, -2),
            "range_high": round(high, -2),
            "neighborhood_used": neighborhood_used,
            "top_factors": self._top_factors(),
        }

    def _top_factors(self, top_n: int = 4) -> list:
        model = self.pipeline.named_steps["model"]
        if not hasattr(model, "feature_importances_"):
            return []

        num_cols = [
            "sqft_living", "lot_size_sqft", "bedrooms", "bathrooms", "floors", "age",
            "renovated", "condition", "grade", "garage", "basement", "pool",
            "school_score", "bath_bed_ratio", "lot_to_living_ratio",
        ]
        cat_cols = ["neighborhood"]

        try:
            ohe = self.pipeline.named_steps["prep"].named_transformers_["cat"].named_steps["ohe"]
            cat_feature_names = list(ohe.get_feature_names_out(cat_cols))
        except Exception:
            cat_feature_names = []

        feature_names = num_cols + cat_feature_names
        importances = model.feature_importances_

        # roll one-hot neighborhood columns back up into a single "Neighborhood" bucket
        grouped = {}
        for name, imp in zip(feature_names, importances):
            label = "Neighborhood" if name.startswith("neighborhood_") else _pretty(name)
            grouped[label] = grouped.get(label, 0.0) + float(imp)

        total = sum(grouped.values()) or 1.0
        ranked = sorted(grouped.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        return [
            {"label": label, "importance_pct": round(val / total * 100, 1)}
            for label, val in ranked
        ]


def _pretty(name: str) -> str:
    return {
        "sqft_living": "Living area",
        "lot_size_sqft": "Lot size",
        "bedrooms": "Bedrooms",
        "bathrooms": "Bathrooms",
        "floors": "Floors",
        "age": "Age",
        "renovated": "Renovated",
        "condition": "Condition",
        "grade": "Construction grade",
        "garage": "Garage",
        "basement": "Basement",
        "pool": "Pool",
        "school_score": "School score",
        "bath_bed_ratio": "Bath/bed ratio",
        "lot_to_living_ratio": "Lot/living ratio",
    }.get(name, name.replace("_", " ").title())
