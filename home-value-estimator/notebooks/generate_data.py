"""
generate_data.py
-----------------
Synthesizes a realistic-looking residential housing dataset for the
home-value-estimator project. This is NOT a copy of any public dataset;
the column set, price formula, and noise model are hand-built for this
project so the notebook has something concrete to clean and model.

Run:
    python generate_data.py
Produces:
    data/homes.csv  (8,000 rows)
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_ROWS = 8000

NEIGHBORHOODS = {
    # name: (base $/sqft, desirability multiplier)
    "Brookhaven": (185, 1.15),
    "Cedar Falls": (140, 1.00),
    "Old Mill District": (210, 1.25),
    "Riverside Park": (165, 1.08),
    "Sunridge": (120, 0.90),
    "Harbor Point": (230, 1.30),
    "Maple Grove": (150, 1.02),
    "Northgate": (110, 0.85),
}

CONDITIONS = [1, 2, 3, 4, 5]  # 1 = needs work ... 5 = pristine
GRADES = list(range(3, 11))  # construction/design quality, 3-10


def synth_row():
    neighborhood = RNG.choice(list(NEIGHBORHOODS.keys()))
    base_ppsf, desirability = NEIGHBORHOODS[neighborhood]

    sqft_living = int(np.clip(RNG.normal(1850, 650), 500, 6500))
    lot_size = int(np.clip(sqft_living * RNG.uniform(1.2, 4.0), 800, 40000))
    bedrooms = int(np.clip(round(sqft_living / 650 + RNG.normal(0, 0.6)), 1, 7))
    bathrooms = round(np.clip(bedrooms * 0.75 + RNG.normal(0, 0.5), 1, 6) * 2) / 2
    floors = RNG.choice([1, 1.5, 2, 2.5, 3], p=[0.35, 0.1, 0.35, 0.1, 0.1])
    year_built = int(RNG.integers(1920, 2024))
    age = 2024 - year_built
    renovated = RNG.random() < (0.35 if age > 25 else 0.08)
    condition = int(RNG.choice(CONDITIONS, p=[0.05, 0.15, 0.35, 0.30, 0.15]))
    grade = int(RNG.choice(GRADES))
    has_garage = RNG.random() < 0.72
    has_basement = RNG.random() < 0.45
    has_pool = RNG.random() < 0.08
    school_score = int(np.clip(RNG.normal(6.5, 1.8), 1, 10))

    # --- price formula (the "ground truth" the models must recover) ---
    price = sqft_living * base_ppsf * desirability
    price *= 1 + 0.015 * (grade - 6)
    price *= 1 + 0.01 * (condition - 3)
    price *= 1 - min(age, 80) * 0.0035
    price *= 1.08 if renovated else 1.0
    price *= 1.05 if has_garage else 1.0
    price *= 1.04 if has_basement else 1.0
    price *= 1.12 if has_pool else 1.0
    price *= 1 + 0.02 * (school_score - 6.5)
    price += lot_size * 1.8
    price *= RNG.normal(1.0, 0.09)  # market noise
    price = max(price, 45000)

    # --- messiness, deliberately different from any public dataset ---
    price_display = f"${price/1000:.1f}K" if RNG.random() < 0.5 else round(price, -2)
    area_display = (
        sqft_living if RNG.random() < 0.85 else round(sqft_living * 0.0929, 1)
    )  # some rows sneak in sq. meters
    area_unit = "sqft" if area_display == sqft_living else "sqm"

    return {
        "neighborhood": neighborhood,
        "sqft_living": area_display,
        "area_unit": area_unit,
        "lot_size_sqft": lot_size,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "floors": floors,
        "year_built": year_built,
        "renovated": "Yes" if renovated else "No",
        "condition": condition,
        "grade": grade,
        "garage": "Y" if has_garage else "N",
        "basement": "Y" if has_basement else "N",
        "pool": "Y" if has_pool else "N",
        "school_score": school_score,
        "sale_price": price_display,
    }


def inject_missingness(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col, frac in {
        "school_score": 0.06,
        "basement": 0.03,
        "year_built": 0.02,
        "lot_size_sqft": 0.015,
    }.items():
        mask = RNG.random(len(df)) < frac
        df.loc[mask, col] = np.nan
    return df


def main():
    rows = [synth_row() for _ in range(N_ROWS)]
    df = pd.DataFrame(rows)
    df = inject_missingness(df)
    df.to_csv("data/homes.csv", index=False)
    print(f"Wrote data/homes.csv with {len(df)} rows and {len(df.columns)} columns")


if __name__ == "__main__":
    main()
