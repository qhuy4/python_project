from flask import Flask, render_template, request, redirect
import pandas as pd
import os

app = Flask(__name__)
DATA_PATH = "data/heart.csv"

def load_data():
    return pd.read_csv(DATA_PATH)

def save_data(df):
    df.to_csv(DATA_PATH, index=False)

@app.route("/")
def index():
    df = load_data()
    return render_template("index.html", data=df.to_dict(orient="records"))

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

if __name__ == "__main__":
    app.run(debug=True)
