# core/loader.py
import pandas as pd

COLUMNS = [
    "Tuổi", "Giới tính (0: Nữ, 1: Nam)", "Loại đau ngực (0-3)",
    "Huyết áp nghỉ (mmHg)", "Cholesterol toàn phần (mg/dl)",
    "Đường huyết đói > 120mg/dl (1: Có)", "ECG lúc nghỉ (0–2)",
    "Nhịp tim tối đa", "Đau ngực khi gắng sức (1: Có)",
    "Độ chênh ST khi gắng sức", "Dốc ST sau gắng sức (0–2)",
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
