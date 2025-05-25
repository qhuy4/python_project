import pandas as pd
import os

DATA_PATH = "data/processed.cleveland.data"
CLEAN_PATH = "data/processed.cleveland_updated.data"
COLUMNS = [
    "ID",
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
    "num"
]



def load_data():
    if not os.path.exists(CLEAN_PATH) or os.path.getsize(CLEAN_PATH) == 0:
        df = pd.read_csv(
            DATA_PATH,
            header=None,
            names=COLUMNS[1:],
            na_values="?"
        )
        df.dropna(inplace=True)
        df.insert(0, "ID", range(1, len(df) + 1))
        df.to_csv(CLEAN_PATH, header=COLUMNS, index=False)

    df = pd.read_csv(CLEAN_PATH, header=0)
    df = df.drop(columns=["ID"], errors="ignore")
    df.insert(0, "ID", range(1, len(df) + 1))
    return df



def save_data(df, path=CLEAN_PATH):
    df.to_csv(path, header=COLUMNS, index=False)
