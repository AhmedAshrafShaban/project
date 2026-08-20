"""
Lightweight request validation for /api/estimate.

No external validation library — this is a small, explicit schema so the
whole request/response contract is readable in one file.
"""
from dataclasses import dataclass

ALLOWED_YES_NO = {"Y", "N"}


class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


@dataclass
class EstimateRequest:
    neighborhood: str
    sqft_living: float
    lot_size_sqft: float
    bedrooms: int
    bathrooms: float
    floors: float
    year_built: int
    renovated: str
    condition: int
    grade: int
    garage: str
    basement: str
    pool: str
    school_score: float

    @staticmethod
    def from_json(payload: dict) -> "EstimateRequest":
        errors = {}
        required = [
            "neighborhood", "sqft_living", "lot_size_sqft", "bedrooms", "bathrooms",
            "floors", "year_built", "renovated", "condition", "grade", "garage",
            "basement", "pool", "school_score",
        ]
        for field in required:
            if field not in payload or payload[field] in (None, ""):
                errors[field] = "This field is required."

        if errors:
            raise ValidationError(errors)

        def as_number(name, cast, lo=None, hi=None):
            try:
                val = cast(payload[name])
            except (TypeError, ValueError):
                errors[name] = f"Must be a valid {cast.__name__}."
                return None
            if lo is not None and val < lo:
                errors[name] = f"Must be >= {lo}."
            if hi is not None and val > hi:
                errors[name] = f"Must be <= {hi}."
            return val

        sqft_living = as_number("sqft_living", float, lo=150, hi=20000)
        lot_size_sqft = as_number("lot_size_sqft", float, lo=0, hi=500000)
        bedrooms = as_number("bedrooms", int, lo=0, hi=15)
        bathrooms = as_number("bathrooms", float, lo=0, hi=10)
        floors = as_number("floors", float, lo=1, hi=5)
        year_built = as_number("year_built", int, lo=1850, hi=2026)
        condition = as_number("condition", int, lo=1, hi=5)
        grade = as_number("grade", int, lo=1, hi=10)
        school_score = as_number("school_score", float, lo=1, hi=10)

        for field in ("renovated", "garage", "basement", "pool"):
            val = str(payload[field]).strip().upper()
            if val in ("YES", "Y", "TRUE", "1"):
                payload[field] = "Y"
            elif val in ("NO", "N", "FALSE", "0"):
                payload[field] = "N"
            else:
                errors[field] = "Must be Y/N (or yes/no)."

        if not str(payload["neighborhood"]).strip():
            errors["neighborhood"] = "This field is required."

        if errors:
            raise ValidationError(errors)

        return EstimateRequest(
            neighborhood=str(payload["neighborhood"]).strip(),
            sqft_living=sqft_living,
            lot_size_sqft=lot_size_sqft,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            floors=floors,
            year_built=year_built,
            renovated=payload["renovated"],
            condition=condition,
            grade=grade,
            garage=payload["garage"],
            basement=payload["basement"],
            pool=payload["pool"],
            school_score=school_score,
        )
