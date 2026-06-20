# 📊 Sales Intelligence Suite

> Automated Data Cleaning + Business Intelligence Dashboard powered by Streamlit, Pandas & Plotly.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white)
![openpyxl](https://img.shields.io/badge/openpyxl-Excel-green)

## StreamLit Link:- https://salesdashboard-hduq4qubt3barwfibzhp6g.streamlit.app/

## ✨ Features

| Feature | Description |
|---|---|
| 🧹 **Auto Clean** | Deduplication, median null-fill, IQR outlier capping, date parsing, profit derivation |
| 📊 **Revenue Charts** | Bar chart by category, donut chart by region |
| 📅 **Trend Analysis** | Monthly revenue line chart, new vs returning customer grouped bars |
| 👥 **Sales Rep Leaderboard** | Ranked table + horizontal bar chart by total revenue |
| 🔍 **Sidebar Filters** | Region multi-select, quarter selector, customer-type radio, one-click reset |
| 📌 **KPI Cards** | Total revenue, transactions, avg order value, top region, avg profit margin |
| 📥 **Excel Export** | 3-sheet .xlsx: cleaned data, pivot table, sales-rep summary |

---

## 🗄️ Dataset

Download the dataset from Kaggle:  
👉 **[kaggle.com/datasets/vinothkannaece/sales-dataset](https://www.kaggle.com/datasets/vinothkannaece/sales-dataset)**

**Expected CSV columns:**

```
Transaction_ID, Date, Sales_Rep, Region, Region_and_Sales_Rep,
Product_Category, Unit_Cost, Unit_Price, Quantity_Sold,
Sales_Amount, Customer_Type
```

---

## 🚀 Run Locally

### 1 — Clone the repository

```bash
git clone https://github.com/Arhaan-H/Sales_Dashboard.git
cd Sales_Dashboard
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Launch the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

---

## ☁️ Deploy on Streamlit Cloud

1. **Push this repo to GitHub** (it must be public, or you must connect a private repo).
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.
3. Click **"New app"** → select your repository.
4. Set **Main file path** to `app.py`.
5. Click **Deploy** — Streamlit Cloud installs `requirements.txt` automatically.

> No secrets or environment variables are required. The app is fully self-contained.

---

## 🗂️ Project Structure

```
Sales_Dashboard/
├── app.py            ← Main Streamlit application
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```

---

## 🛠️ Tech Stack

| Tool | Role |
|---|---|
| **Python 3.9+** | Core language |
| **Streamlit** | Web framework & UI |
| **Pandas** | Data cleaning & aggregation |
| **Plotly Express** | Interactive charts |
| **openpyxl / xlsxwriter** | Excel export engine |
| **NumPy** | Numerical operations |

---

## 📋 Data Cleaning Pipeline

```
Upload CSV
    │
    ▼
① Deduplication        → Drop duplicate Transaction_IDs
    │
    ▼
② Null Imputation      → Median-fill Quantity_Sold, Unit_Price, Unit_Cost
    │
    ▼
③ Outlier Capping      → IQR upper fence on Unit_Price
    │
    ▼
④ Date Parsing         → Extract Month, Month_Num, Quarter
    │
    ▼
⑤ Feature Engineering  → Compute Profit, Profit_Margin_%
    │
    ▼
⑥ Quality Report       → Metrics: dupes removed, nulls filled, outliers capped, clean rows
```

---

## 📄 License

MIT — free to use and modify.
