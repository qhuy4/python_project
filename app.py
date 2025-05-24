from operator import truediv
from math import ceil

from flask import Flask, render_template, request, redirect
from modules.load_file import load_data, save_data
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.template_filter('custom_column_name')
def custom_column_name_filter(col_name):
    name_map = {
        'Age': 'Tuổi', 'Sex': 'Giới Tính', 'Cp': 'Loại Đau Ngực', 'Trestbps': 'Huyết Áp Nghỉ',
        'Chol': 'Cholesterol', 'Fbs': 'Đường Huyết Đói', 'Restecg': 'ECG Lúc Nghỉ',
        'Thalach': 'Nhịp Tim Tối Đa', 'Exang': 'Đau Ngực Khi Gắng Sức', 'Oldpeak': 'ST Chênh Lệch',
        'Slope': 'Dốc ST Gắng Sức', 'Ca': 'Số Mạch Vành Tắc', 'Thal': 'Thalassemia',
        'Target': 'Kết Quả Chẩn Đoán'
    }
    return name_map.get(col_name, col_name)

@app.template_filter('custom_cell_value')
def custom_cell_value_filter(value, col_name):
    # ... (đảm bảo hàm này có đầy đủ như phiên bản tôi đã cung cấp)
    if col_name == 'Sex' or col_name == 'Giới tính':
        if value == 0: return 'Nữ'
        elif value == 1: return 'Nam'
        return value
    elif col_name == 'Fbs' or col_name == 'Đường huyết đói':
        return 'Có' if value == 1 else 'Không' if value == 0 else value
    elif col_name == 'Target' or col_name == 'Kết quả chẩn đoán':
        return 'Mắc Bệnh Tim' if value == 1 else 'Không Mắc Bệnh Tim' if value == 0 else value
    elif col_name == 'Cp' or col_name == 'Loại đau ngực':
        if value == 0: return 'Điển hình đau thắt ngực'
        elif value == 1: return 'Đau thắt ngực không điển hình'
        elif value == 2: return 'Đau không đau thắt ngực'
        elif value == 3: return 'Không đau'
        return value
    elif col_name == 'Restecg' or col_name == 'ECG lúc nghỉ':
        if value == 0: return 'Bình thường'
        elif value == 1: return 'Có bất thường ST-T'
        elif value == 2: return 'Phì đại thất trái'
        return value
    elif col_name == 'Exang' or col_name == 'Đau ngực khi gắng sức':
        return 'Có' if value == 1 else 'Không' if value == 0 else value
    elif col_name == 'Slope' or col_name == 'Dốc ST gắng sức':
        if value == 0: return 'Lên dốc'
        elif value == 1: return 'Phẳng'
        elif value == 2: return 'Dốc xuống'
        return value
    elif col_name == 'Ca' or col_name == 'Số mạch vành tắc':
        if value == 0: return '0 mạch'
        elif value == 1: return '1 mạch'
        elif value == 2: return '2 mạch'
        elif value == 3: return '3 mạch'
        elif value == 4: return 'Không xác định'
        return value
    elif col_name == 'Thal' or col_name == 'Thalassemia':
        if value == 1: return 'Bình thường'
        elif value == 2: return 'Khiếm khuyết cố định'
        elif value == 3: return 'Khiếm khuyết có thể đảo ngược'
        return value
    return value

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
    df_page = df.iloc[start:end]

    return render_template("index.html",
                           data=df_page.to_dict(orient='records'),
                           columns=df.columns.tolist(),
                           current_sort_by=sort_by,
                           current_sort_order=sort_order,
                           current_page=page,
                           total_pages=total_pages)


    #return render_template("index.html", data=df.to_dict(orient="records"))

@app.route("/create", methods=["POST"])
def create():
    df = load_data()
    new_entry = {col: request.form[col] for col in df.columns}
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(df)
    return redirect("/")

@app.route("/edit/<int:index>")
def edit(index):
    df = load_data()
    record = df.iloc[index].to_dict()
    return render_template("edit.html", record=record, index=index)

@app.route("/update/<int:index>", methods=["POST"])
def update(index):
    df = load_data()
    for col in df.columns:
        df.at[index, col] = request.form[col]
    save_data(df)
    return redirect("/")

@app.route("/delete/<int:index>")
def delete(index):
    df = load_data()
    df = df.drop(index).reset_index(drop=True)
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
    df["Có bệnh tim"] = df["Kết quả chẩn đoán (1: Mắc bệnh tim)"].apply(lambda x: 0 if x == 0 else 1)

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
    df.groupby("Giới tính (0: Nữ, 1: Nam)")["Kết quả chẩn đoán (1: Mắc bệnh tim)"].mean().plot(kind='bar', ax=ax2)
    ax2.set_title("Tỉ lệ bệnh tim theo giới tính")
    charts.append(("Tỉ lệ bệnh tim theo giới tính", plot_to_base64(fig2)))

    # Chart 3: Tuổi trung bình
    fig3, ax3 = plt.subplots()
    df.groupby("Kết quả chẩn đoán (1: Mắc bệnh tim)")["Tuổi"].mean().plot(kind='bar', ax=ax3)
    ax3.set_title("Tuổi trung bình theo kết quả chẩn đoán")
    charts.append(("Tuổi trung bình theo kết quả chẩn đoán", plot_to_base64(fig3)))

    # Chart 4: Boxplot nhịp tim
    fig4, ax4 = plt.subplots()
    df.boxplot(column="Nhịp tim tối đa", by="Kết quả chẩn đoán (1: Mắc bệnh tim)", ax=ax4)
    ax4.set_title("Phân bố nhịp tim theo tình trạng bệnh")
    charts.append(("Phân bố nhịp tim theo tình trạng bệnh", plot_to_base64(fig4)))

    # Chart 5: Mạch vành tắc vs bệnh tim
    fig5, ax5 = plt.subplots()
    df.groupby("Số mạch vành bị tắc (0–3)")["Kết quả chẩn đoán (1: Mắc bệnh tim)"].mean().plot(kind='bar', ax=ax5)
    ax5.set_title("Tỉ lệ bệnh theo số mạch vành bị tắc")
    charts.append(("Tỉ lệ bệnh theo số mạch vành bị tắc", plot_to_base64(fig5)))

    return render_template("charts.html", charts=charts)


if __name__ == "__main__":
    app.run(debug=True)
