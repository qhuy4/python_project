# core/loader.py
import pandas as pd

COLUMNS = [
    "Tuổi", "Giới tính", "Đau ngực \nLoại:(0-3)",
    "Huyết áp (mmHg)", "Cholesterol (mg/dl)",
    "Đường huyết \n(> 120mg/dl) ", "ECG (0–2)",
    "Nhịp tim tối đa", "Đau ngực",
    "Độ chênh ST", "Dốc ST (0–2)",
    "Số mạch vành bị tắc (0–3)", "Thalassemia (1–3)",
    "Kết quả chẩn đoán (1: Mắc bệnh tim)"
]

DATA_PATH = "data/processed.cleveland.data"

def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = COLUMNS
    return df

def save_data(df):
    df.to_csv(DATA_PATH, index=False)
