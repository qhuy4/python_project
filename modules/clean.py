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
    """
    Tải và làm sạch dữ liệu từ tệp CSV.

    Nếu tệp dữ liệu sạch (`CLEAN_PATH`) chưa tồn tại hoặc rỗng, hàm sẽ:
    - Đọc dữ liệu thô từ `DATA_PATH`
    - Gán tên cột từ `COLUMNS[1:]`
    - Xử lý giá trị thiếu ("?") thành NaN và loại bỏ các dòng chứa NaN
    - Thêm cột ID đánh số từ 1
    - Lưu vào file `CLEAN_PATH`

    Sau đó, luôn đọc lại từ `CLEAN_PATH`, cập nhật lại cột ID (trong trường hợp dữ liệu thay đổi) và trả về DataFrame.

    Returns:
        pd.DataFrame: Dữ liệu đã được làm sạch với cột ID.
    """
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
    """
       Lưu DataFrame vào tệp CSV theo định dạng chuẩn.

       Args:
           df (pd.DataFrame): Dữ liệu cần lưu.
           path (str, optional): Đường dẫn lưu file CSV. Mặc định là `CLEAN_PATH`.
    """
    df.to_csv(path, header=COLUMNS, index=False)
