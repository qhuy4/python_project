from operator import truediv
from math import ceil
from flask import Flask, render_template, request, redirect, flash
from modules.clean import load_data, save_data
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Route Index
@app.route("/")
def index():
    """
    Trang chủ hiển thị bảng dữ liệu bệnh tim.

    - Hỗ trợ sắp xếp theo cột (sort_by) và thứ tự (asc/desc).
    - Hỗ trợ tìm kiếm theo giá trị trong cột (search_field, search_value).
    - Phân trang mỗi trang hiển thị 10 bản ghi.
    - Giao diện thân thiện với người Việt nhờ đổi tên cột và ánh xạ giá trị rõ ràng.

    Query Parameters:
        - sort_by (str): Tên cột muốn sắp xếp.
        - sort_order (str): asc hoặc desc.
        - search_field (str): Cột để tìm kiếm.
        - search_value (str): Giá trị tìm kiếm.
        - page (int): Số trang hiện tại.

    Returns:
        Rendered HTML trang index với bảng dữ liệu được lọc, sắp xếp và phân trang.
    """
    df = load_data()

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

    # Map dữ liệu để dễ hiểu
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
        1: "Bệnh tim nhẹ",
        0.0: "Không bệnh tim",
        1.0: "Bệnh tim nhẹ",
        "0.0": "Không bệnh tim",
        "1.0": "Bệnh tim nhẹ",
    }

    df["Kết quả"] = df["Kết quả"].map(result_map).fillna("Bệnh tim nghiêm trọng")

    search_field = request.args.get('search_field', '').strip()
    search_value = request.args.get('search_value', '').strip()

    if search_field and search_value:
            if search_field in df.columns:
                df = df[df[search_field].astype(str).str.contains(search_value, case=False, na=False)]



    # Phân trang
    page = int(request.args.get('page', 1))
    per_page = 10
    total_pages = (len(df) + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page

    # df = df.rename(columns=cols)

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
    """
        Trang hiển thị form để thêm bản ghi bệnh nhân mới.

        Returns:
            Rendered HTML của trang tạo mới (create.html).
    """
    return render_template("create.html")


# Hàm kiểm tra bệnh tim
# Params "cp": "Đau ngực", chol: Cholesterol, exang:Đau ngực khi gắng sức ,oldpeak :Độ chênh ST
# return only 1 or 2 or 3
def compute_num(cp, chol, exang, oldpeak):
    """
        Hàm đơn giản để dự đoán bệnh tim (giả lập).

        Dựa vào một số chỉ số: đau ngực (cp), cholesterol,
        đau ngực khi gắng sức (exang), và độ chênh ST (oldpeak).

        Args:
            cp (int): Loại đau ngực (1–4).
            chol (float): Mức cholesterol.
            exang (int): Có đau ngực khi gắng sức hay không (0/1).
            oldpeak (float): Độ chênh ST.

        Returns:
            int: 1 nếu có dấu hiệu bệnh tim, 0 nếu không.
    """
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
    """
       Hàm xử lý khi người dùng gửi form để thêm bệnh nhân mới.

       - Lấy dữ liệu từ biểu mẫu HTML.
       - Tính toán kết quả bệnh tim (giá trị cột "num") thông qua hàm `compute_num`.
       - Gộp bản ghi mới với dữ liệu cũ rồi lưu lại vào file CSV.
       - Chuyển hướng về trang chủ sau khi lưu thành công.
    """
    age = float(request.form["age"])
    sex = int(request.form["sex"])
    cp = int(request.form["cp"])
    trestbps = float(request.form["trestbps"])
    chol = float(request.form["chol"])
    fbs = int(request.form["fbs"])
    restecg = int(request.form["restecg"])
    thalach = float(request.form["thalach"])
    exang = int(request.form["exang"])
    oldpeak = float(request.form["oldpeak"])
    slope = int(request.form["slope"])
    ca = int(request.form["ca"])
    thal = int(request.form["thal"])

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
        "num": compute_num(cp, chol, exang, oldpeak)
    }
    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    save_data(df)
    return redirect("/")


# Load Data Edit Function
# Params Id
# Return HTML Template with record data
@app.route("/edit/<int:id>")
def edit(id):
    """
       Hiển thị form chỉnh sửa thông tin bệnh nhân theo ID.

       - Tải toàn bộ dữ liệu từ file CSV.
       - Lấy bản ghi tương ứng với ID được truyền từ URL.
       - Truyền dữ liệu bản ghi vào form chỉnh sửa (edit.html).

       Tham số:
           id (int): ID của bản ghi cần chỉnh sửa (lấy từ URL)

       Trả về:
           Trang HTML chứa form chỉnh sửa đã điền sẵn dữ liệu của bản ghi.
    """
    df = load_data()
    df2 = df.set_index('ID')
    record = df2.loc[id].to_dict()
    return render_template("edit.html", record=record, id=id)


# Updated Function
# Params Id
# Return HTML Template with record data
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    """
        Cập nhật thông tin bản ghi bệnh nhân theo ID.

        - Đọc toàn bộ dữ liệu từ CSV.
        - Duyệt qua tất cả các cột (trừ ID) và cập nhật giá trị từ form.
        - Tính lại giá trị 'num' dựa trên các tiêu chí sức khỏe.
        - Lưu dữ liệu đã cập nhật trở lại vào file CSV.

        Tham số:
            id (int): ID của bản ghi cần cập nhật (lấy từ URL)

        Trả về:
            Chuyển hướng về trang chủ sau khi cập nhật thành công.
    """
    df = load_data()
    for col in df.columns:
        if col == 'ID':
            continue
        df.loc[df['ID'] == id, col] = request.form[col]

    # Lấy lại bản ghi vừa sửa
    row = df.loc[df['ID'] == id].iloc[0]
    # Tính lại num
    new_num = compute_num(
        cp=int(row['cp']),
        chol=float(row['chol']),
        exang=int(row['exang']),
        oldpeak=float(row['oldpeak']),
    )
    # Gán num mới
    df.loc[df['ID'] == id, 'num'] = new_num

    save_data(df)
    return redirect("/")


# Delete Function
# Params Id
# Return Homepage after delete
@app.route("/delete/<int:id>")
def delete(id):
    """
      Xoá bản ghi bệnh nhân theo ID.

      - Đọc toàn bộ dữ liệu từ file CSV.
      - Lọc bỏ bản ghi có ID tương ứng.
      - Reset lại chỉ số ID để đảm bảo liên tục (tăng từ 1).
      - Ghi dữ liệu mới trở lại file CSV.

      Tham số:
          id (int): ID của bản ghi cần xoá (lấy từ URL)

      Trả về:
          Chuyển hướng về trang chủ sau khi xoá thành công.
    """
    df = load_data()
    df = df[df['ID'] != id].reset_index(drop=True)
    df = df.drop(columns=['ID'])
    df.insert(0, 'ID', range(1, len(df) + 1))
    save_data(df)
    return redirect("/")


@app.route("/chart")
def charts():
    """
        Sinh các biểu đồ phân tích dữ liệu bệnh tim từ file CSV và render lên trang charts.html.

        Biểu đồ bao gồm:
        1. Phân bố số lượng người có và không mắc bệnh tim.
        2. Tỉ lệ (%) người mắc bệnh tim theo giới tính.
        3. Tuổi trung bình tương ứng với từng mức độ bệnh tim.
        4. Tỉ lệ (%) người mắc bệnh tim theo số mạch vành bị tắc.

        Trả về:
            render_template("charts.html") với danh sách biểu đồ dưới dạng ảnh base64.
    """
    df = load_data()

    # Map các giá trị để hiển thị tiếng Việt
    sex_map = {0: "Nữ", 1: "Nam"}
    num_map = {
        0: "Không bệnh tim",
        1: "Bệnh tim nhẹ",
        2: "Bệnh tim trung bình",
        3: "Bệnh tim nặng (mức 3)",
        4: "Bệnh tim rất nặng (mức 4)"
    }

    charts = []

    def plot_to_base64(fig):
        import io, base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    # Tạo cột Có bệnh tim (0/1)
    df["Có bệnh tim"] = df["num"].apply(lambda x: 0 if x == 0 else 1)

    # Chart 1: Phân bố người có bệnh tim vs không có bệnh
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    counts = df["Có bệnh tim"].value_counts().sort_index()
    counts.index = ["Không mắc bệnh tim", "Mắc bệnh tim"]
    bars = ax1.bar(counts.index, counts.values, color=['green', 'red'])
    ax1.set_title("Tình trạng mắc bệnh tim trong dữ liệu")
    ax1.set_ylabel("Số lượng bệnh nhân")
    ax1.set_xlabel("Tình trạng")
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{int(height)}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 5),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=10, fontweight='bold')
    fig1.tight_layout()
    charts.append(("Tình trạng mắc bệnh tim", plot_to_base64(fig1)))

    # Chart 2: Tỉ lệ mắc bệnh tim trung bình theo giới tính
    # Chart 2: Tỉ lệ (%) người mắc bệnh tim theo giới tính
    fig2, ax2 = plt.subplots()

    # Tạo cột 'Có bệnh tim': 1 nếu num > 0, 0 nếu không
    df["Có bệnh tim"] = df["num"].apply(lambda x: 1 if x > 0 else 0)

    # Tính tỉ lệ phần trăm người mắc bệnh tim theo giới tính
    rate_by_sex = df.dropna(subset=["sex", "Có bệnh tim"]).groupby("sex")["Có bệnh tim"].mean() * 100
    rate_by_sex.index = rate_by_sex.index.map(sex_map).fillna("Khác")

    # Vẽ biểu đồ
    rate_by_sex.plot(kind='bar', ax=ax2, color=['blue', 'orange'])
    ax2.set_title("Tỉ lệ (%) người mắc bệnh tim theo giới tính")
    ax2.set_xlabel("Giới tính")
    ax2.set_ylabel("Tỉ lệ mắc bệnh (%)")
    ax2.set_ylim(0, 100)  # Giới hạn trục Y từ 0 đến 100%

    # Hiển thị nhãn trên đầu cột
    for i, v in enumerate(rate_by_sex.values):
        ax2.text(i, v + 1, f"{v:.1f}%", ha='center', va='bottom', fontweight='bold')

    fig2.tight_layout()
    charts.append(("Tỉ lệ (%) người mắc bệnh tim theo giới tính", plot_to_base64(fig2)))

    # Chart 3: Tuổi trung bình tương ứng với mức độ bệnh tim
    fig3, ax3 = plt.subplots()
    mean_age = df.dropna(subset=["num", "age"]).groupby("num")["age"].mean()
    mean_age.index = mean_age.index.map(num_map).fillna("Không rõ")
    mean_age.plot(kind='bar', ax=ax3, color='purple')
    ax3.set_title("Tuổi trung bình theo mức độ bệnh tim")
    ax3.set_xlabel("Mức độ bệnh tim")
    ax3.set_ylabel("Tuổi trung bình (năm)")
    fig3.tight_layout()
    charts.append(("Tuổi trung bình theo mức độ bệnh tim", plot_to_base64(fig3)))

    # Chart 4: Tỉ lệ mắc bệnh tim theo số mạch vành bị tắc
    # Chart 4: Tỉ lệ (%) người mắc bệnh tim theo số mạch vành bị tắc
    fig5, ax5 = plt.subplots()

    # Đảm bảo cột 'ca' là số và 'Có bệnh tim' là 0/1
    df["ca"] = pd.to_numeric(df["ca"], errors='coerce')
    df["Có bệnh tim"] = df["num"].apply(lambda x: 1 if x > 0 else 0)

    # Tính tỉ lệ phần trăm người mắc bệnh theo số ca mạch vành tắc
    rate_by_ca = df.dropna(subset=["ca", "Có bệnh tim"]).groupby("ca")["Có bệnh tim"].mean() * 100
    rate_by_ca.index = [f"{int(ca)} mạch tắc" for ca in rate_by_ca.index]

    # Vẽ biểu đồ
    rate_by_ca.plot(kind='bar', ax=ax5, color='teal')
    ax5.set_title("Tỉ lệ (%) người mắc bệnh tim theo số mạch vành bị tắc")
    ax5.set_xlabel("Số mạch vành bị tắc")
    ax5.set_ylabel("Tỉ lệ mắc bệnh (%)")
    ax5.set_ylim(0, 100)

    # Thêm nhãn trên mỗi cột
    for i, v in enumerate(rate_by_ca.values):
        ax5.text(i, v + 1, f"{v:.1f}%", ha='center', va='bottom', fontweight='bold')

    fig5.tight_layout()
    charts.append(("Tỉ lệ (%) người mắc bệnh tim theo số mạch vành bị tắc", plot_to_base64(fig5)))

    return render_template("charts.html", charts=charts)


if __name__ == "__main__":
    app.run(debug=True)
