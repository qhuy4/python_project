from operator import truediv
from math import ceil
from flask import Flask, render_template, request, redirect,flash
from modules.clean import load_data, save_data
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

#Route Index
@app.route("/")
def index():
    df = load_data()
    # lọc dữ liệu
    for col_name in df.columns:
        filter_value = request.args.get(f'filter_{col_name}', '').strip()

        if filter_value:
            if pd.api.types.is_numeric_dtype(df[col_name]):
                try:
                    num_filter_value = pd.to_numeric(filter_value)
                    df = df[df[col_name] == num_filter_value]
                except ValueError:
                    pass
            else:
                df = df[
                    df[col_name].astype(str).str.contains(filter_value, case=False, na=False)
                ]

    # sort nếu có yêu cầu
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')

    if not df.empty and sort_by and sort_by in df.columns:
        ascending = True if sort_order == 'asc' else False
        if pd.api.types.is_numeric_dtype(df[sort_by]):
            df[sort_by] = pd.to_numeric(df[sort_by], errors='coerce')
            df = df.sort_values(by=sort_by, ascending=ascending, na_position='last')
        else:
            df = df.sort_values(by=sort_by, ascending=ascending)

    # Phân trang
    page = int(request.args.get('page', 1))
    per_page = 10
    total_pages = (len(df) + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    cols = {
        "age": "Tuổi",
        "sex": "Giới tính",
        "cp": "Đau ngực",
        "trestbps": "Huyết áp (mmHg)",
        "chol": "Cholesterol (mg/dl)",
        "fbs": "Đường huyết (> 120mg/dl)",
        "restecg": "ECG",
        "thalach": "Nhịp tim",
        "exang": "Đau ngực khi gắng sức",
        "oldpeak": "Độ chênh ST",
        "slope": "Dốc ST",
        "ca": "Số mạch vành bị tắc",
        "thal": "Thalassemia",
        "num": "Kết quả"
    }
    df = df.rename(columns=cols)

    df["Giới tính"] = df["Giới tính"].map({0: "Nữ", 1: "Nam"})

    df["Đau ngực"] = df["Đau ngực"].map({
        1: "Đau thắt ngực điển hình",
        2: "Đau thắt ngực không điển hình",
        3: "Đau không do tim (không liên quan tim)",
        4: "Không có triệu chứng"
    })

    df["Đường huyết (> 120mg/dl)"] = df["Đường huyết (> 120mg/dl)"].map({
        0: "≤ 120 mg/dl",
        1: "> 120 mg/dl"
    })

    # ECG
    df["ECG"] = df["ECG"].map({
        0: "Bình thường",
        1: "Bất thường ST-T",
        2: "Phì đại thất trái"
    })

    df["Đau ngực khi gắng sức"] = df["Đau ngực khi gắng sức"].map({
        0: "Không",
        1: "Có"
    })

    df["Dốc ST"] = df["Dốc ST"].map({
        1: "Dốc lên",
        2: "Phẳng",
        3: "Dốc xuống"
    })

    df["Thalassemia"] = df["Thalassemia"].map({
        3: "Bình thường",
        6: "Khiếm khuyết cố định",
        7: "Khiếm khuyết hồi phục"
    })


    result_map = {
        0: "Không bệnh tim",
        1: "Bệnh tim nhẹ"
    }

    result_map = {
        0: "Không bệnh tim",
        1: "Bệnh tim nhẹ",
        0.0: "Không bệnh tim",
        1.0: "Bệnh tim nhẹ",
        "0.0": "Không bệnh tim",
        "1.0": "Bệnh tim nhẹ",
    }
    df["Kết quả"] = df["Kết quả"].map(result_map).fillna("Bệnh tim nghiêm trọng")

    df_page = df.iloc[start:end]

    # Tạo list of
    columns = [("ID", "STT")]
    for key, label in cols.items():
        columns.append((key, label))
    return render_template("index.html",
                           data=df_page.to_dict(orient='records'),
                           columns=columns,
                           current_sort_by=sort_by,
                           current_sort_order=sort_order,
                           current_page=page,
                           total_pages=total_pages)

@app.route("/add")
def create():
    return render_template("create.html")


#Hàm kiểm tra bệnh tim
    #Params "cp": "Đau ngực", chol: Cholesterol, exang:Đau ngực khi gắng sức ,oldpeak :Độ chênh ST
    # return only 1 or 2 or 3
def compute_num(cp, chol,exang,oldpeak):
    score = 0
    if cp >= 2:
        score += 1
    if chol > 240:
        score += 1
    if oldpeak > 2.0:
        score += 1
    if exang == 1:
        score += 1
    return 1 if score >= 2 else 0

# Create function to save data to CSV file.
@app.route("/create", methods=["POST"])
def save():
    age       = float(request.form["age"])
    sex       = int(request.form["sex"])
    cp        = int(request.form["cp"])
    trestbps  = float(request.form["trestbps"])
    chol      = float(request.form["chol"])
    fbs       = int(request.form["fbs"])
    restecg   = int(request.form["restecg"])
    thalach   = float(request.form["thalach"])
    exang     = int(request.form["exang"])
    oldpeak   = float(request.form["oldpeak"])
    slope     = int(request.form["slope"])
    ca        = int(request.form["ca"])
    thal      = int(request.form["thal"])

    # 4. Lưu bản ghi mới vào CSV
    df = load_data()
    new_record = {
        "age": age,
        "sex": sex,
        "cp": cp,
        "trestbps": trestbps,
        "chol": chol,
        "fbs": fbs,
        "restecg": restecg,
        "thalach": thalach,
        "exang": exang,
        "oldpeak": oldpeak,
        "slope": slope,
        "ca": ca,
        "thal": thal,
        #  num = 1 nếu score>=2 (tạm coi >=2 là có bệnh), else 0
        "num": compute_num(cp, chol,exang,oldpeak)
    }
    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    save_data(df)
    return redirect("/")

#Load Data Edit Function
    # Params Id
    # Return HTML Template with record data
@app.route("/edit/<int:id>")
def edit(id):
    df = load_data()
    df2 = df.set_index('ID')
    record = df2.loc[id].to_dict()
    return render_template("edit.html", record=record, id=id)

#Updated Function
    # Params Id
    # Return HTML Template with record data
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    df = load_data()
    for col in df.columns:
        if col == 'ID':
            continue
        df.loc[df['ID'] == id, col] = request.form[col]

    # Lấy lại bản ghi vừa sửa
    row = df.loc[df['ID'] == id].iloc[0]
    # Tính lại num
    new_num = compute_num(
        cp       = int(row['cp']),
        chol     = float(row['chol']),
        exang    = int(row['exang']),
        oldpeak  = float(row['oldpeak']),
    )
    # Gán num mới
    df.loc[df['ID'] == id, 'num'] = new_num

    save_data(df)
    return redirect("/")

#Delete Function
    # Params Id
    # Return Homepage after delete
@app.route("/delete/<int:id>")
def delete(id):
    df = load_data()
    df = df[df['ID'] != id].reset_index(drop=True)
    df = df.drop(columns=['ID'])
    df.insert(0, 'ID', range(1, len(df) + 1))
    save_data(df)
    return redirect("/")


@app.route("/chart")
def charts():
    df = load_data()
    charts = []

    def plot_to_base64(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    # Chart 1: Phân bố người có bệnh tim vs không có bệnh
    # Chart 1: Phân bố người có bệnh tim vs không có bệnh
    fig1, ax1 = plt.subplots(figsize=(6, 5))  # Tăng kích thước

    # Tạo cột mới: 0 = không bệnh, 1 = có bệnh
    df["Có bệnh tim"] = df["Kết quả"].apply(lambda x: 0 if x == 0 else 1)

    # Đếm số lượng
    counts = df["Có bệnh tim"].value_counts().sort_index()
    counts.index = ["Không bệnh", "Có bệnh"]

    # Vẽ biểu đồ
    bars = ax1.bar(counts.index, counts.values, color=['green', 'red'])
    ax1.set_title("Phân bố người có và không có bệnh tim")
    ax1.set_ylabel("Số lượng bệnh nhân")
    ax1.set_xlabel("Tình trạng bệnh tim")

    # Hiển thị số trên cột
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{int(height)}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 5),  # Dịch lên 5px
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Căn chỉnh layout
    fig1.tight_layout()

    # Thêm vào danh sách biểu đồ
    charts.append(("Phân bố người có và không có bệnh tim", plot_to_base64(fig1)))

    # Chart 2: Giới tính và tỉ lệ bệnh
    fig2, ax2 = plt.subplots()
    df.groupby("Giới tính")["Kết quả"].mean().plot(kind='bar', ax=ax2)
    ax2.set_title("Tỉ lệ bệnh tim theo giới tính")
    charts.append(("Tỉ lệ bệnh tim theo giới tính", plot_to_base64(fig2)))

    # Chart 3: Tuổi trung bình
    fig3, ax3 = plt.subplots()
    df.groupby("Kết quả")["Tuổi"].mean().plot(kind='bar', ax=ax3)
    ax3.set_title("Tuổi trung bình theo kết quả chẩn đoán")
    charts.append(("Tuổi trung bình theo kết quả chẩn đoán", plot_to_base64(fig3)))

    # Chart 4: Boxplot nhịp tim
    fig4, ax4 = plt.subplots()
    df.boxplot(column="Nhịp tim tối đa", by="Kết quả", ax=ax4)
    ax4.set_title("Phân bố nhịp tim theo tình trạng bệnh")
    charts.append(("Phân bố nhịp tim theo tình trạng bệnh", plot_to_base64(fig4)))

    # Chart 5: Mạch vành tắc vs bệnh tim
    fig5, ax5 = plt.subplots()
    df.groupby("Số mạch vành bị tắc")["Kết quả"].mean().plot(kind='bar', ax=ax5)
    ax5.set_title("Tỉ lệ bệnh theo số mạch vành bị tắc")
    charts.append(("Tỉ lệ bệnh theo số mạch vành bị tắc", plot_to_base64(fig5)))

    return render_template("charts.html", charts=charts)


if __name__ == "__main__":
    app.run(debug=True)
