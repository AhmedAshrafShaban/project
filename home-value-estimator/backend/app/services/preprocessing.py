import pandas as pd

from app.schemas.estimate import EstimateRequest

YES_NO_TO_INT = {"Y": 1, "N": 0}


def to_feature_row(req: EstimateRequest) -> pd.DataFrame:
    """Mirror the exact feature engineering done in the training notebook."""
    age = 2024 - req.year_built
    bath_bed_ratio = req.bathrooms / (req.bedrooms or 1)
    lot_to_living_ratio = req.lot_size_sqft / req.sqft_living

    row = {
        "neighborhood": req.neighborhood,
        "sqft_living": req.sqft_living,
        "lot_size_sqft": req.lot_size_sqft,
        "bedrooms": req.bedrooms,
        "bathrooms": req.bathrooms,
        "floors": req.floors,
        "age": age,
        "renovated": YES_NO_TO_INT[req.renovated],
        "condition": req.condition,
        "grade": req.grade,
        "garage": YES_NO_TO_INT[req.garage],
        "basement": YES_NO_TO_INT[req.basement],
        "pool": YES_NO_TO_INT[req.pool],
        "school_score": req.school_score,
        "bath_bed_ratio": bath_bed_ratio,
        "lot_to_living_ratio": lot_to_living_ratio,
    }
    return pd.DataFrame([row])
