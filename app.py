import streamlit as st
import pandas as pd
import sqlite3
import io
import re

st.set_page_config(page_title="AI Data Analyst Assistant", layout="wide")
st.title("🧠 AI Data Analyst Assistant")
st.write("Upload any dataset (CSV, Excel, JSON, TXT) and start exploring it with AI!")

# File uploader (supports multiple formats)
uploaded_file = st.file_uploader("📂 Upload your dataset", type=["csv", "xlsx", "xls", "json", "txt"])

def clean_column_names(columns):
    """Standardize column names: lowercase, no spaces, no special chars"""
    cleaned = []
    for col in columns:
        col = col.strip().lower()                  # lowercase
        col = re.sub(r'[^a-zA-Z0-9_]', '_', col)   # replace special chars with _
        col = re.sub(r'__+', '_', col)             # replace multiple _ with single
        cleaned.append(col)
    return cleaned

def load_file(file):
    """Detect file type and load into DataFrame with encoding fallback"""
    name = file.name.lower()

    try:
        if name.endswith(".csv") or name.endswith(".txt"):
            encodings = ["utf-8", "latin1", "cp1252"]  # fallback encodings
            for enc in encodings:
                try:
                    file.seek(0)  # reset file pointer
                    return pd.read_csv(file, encoding=enc, on_bad_lines="skip")
                except Exception:
                    continue
            raise ValueError("Could not decode file with UTF-8, Latin1, or CP1252")

        elif name.endswith((".xls", ".xlsx")):
            return pd.read_excel(file)

        elif name.endswith(".json"):
            return pd.read_json(file)

        else:
            st.error("❌ Unsupported file format. Please upload CSV, Excel, JSON, or TXT.")
            return None

    except Exception as e:
        st.error(f"⚠️ Could not read file: {e}")
        return None



if uploaded_file:
    df = load_file(uploaded_file)

    if df is not None:
        # Clean column names
        df.columns = clean_column_names(df.columns)

        st.subheader("🔍 Dataset Preview (Cleaned)")
        st.dataframe(df.head())

        st.write("**Shape of dataset:**", df.shape)
        st.write("**Cleaned Columns:**", list(df.columns))

        # Save into SQLite
        conn = sqlite3.connect("data.db")
        df.to_sql("dataset", conn, if_exists="replace", index=False)

        # 🔑 Show SQL schema
        schema_query = "PRAGMA table_info(dataset);"
        schema_info = pd.read_sql(schema_query, conn)

        st.subheader("📑 Dataset Schema (SQLite format)")
        st.dataframe(schema_info)

        st.code("\n".join(
            [f"{row['name']} ({row['type']})" for _, row in schema_info.iterrows()]
        ), language="sql")

        st.success("✅ Data loaded successfully into SQLite with schema generated!")
