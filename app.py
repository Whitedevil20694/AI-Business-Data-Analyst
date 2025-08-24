import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

st.title("🧠 AI Data Analyst Assistant (Dynamic)")

# Upload CSV
uploaded_file = st.file_uploader("📂 Upload your CSV file", type="csv")

if uploaded_file:
    try:
        # Load CSV safely
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding="latin1")
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.replace(" ", "_").str.lower()
        
        st.write("### Columns in your CSV")
        st.write(df.columns.tolist())

        st.write("### Preview")
        st.dataframe(df.head())

        # Connect to SQLite in-memory
        conn = sqlite3.connect(":memory:")
        table_name = "dataset"
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        st.success(f"✅ Table '{table_name}' loaded!")

        # Identify numeric and text columns
        numeric_cols = df.select_dtypes(include=['int64','float64']).columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()

        # User question
        question = st.text_input("❓ Ask a question about your data")

        if st.button("Run Query") and question.strip():
            question_lower = question.lower()

            # Dynamic SQL generation based on detected columns
            if "top" in question_lower or "highest" in question_lower:
                if numeric_cols:
                    sql = f"SELECT * FROM {table_name} ORDER BY {numeric_cols[0]} DESC LIMIT 5;"
                else:
                    st.error("No numeric column found to sort by.")
                    st.stop()

            elif "average" in question_lower:
                if numeric_cols:
                    sql = f"SELECT AVG({numeric_cols[0]}) AS avg_{numeric_cols[0]} FROM {table_name};"
                else:
                    st.error("No numeric column found for average.")
                    st.stop()

            elif "total" in question_lower or "sum" in question_lower:
                if numeric_cols:
                    sql = f"SELECT SUM({numeric_cols[0]}) AS total_{numeric_cols[0]} FROM {table_name};"
                else:
                    st.error("No numeric column found for sum.")
                    st.stop()

            elif "count" in question_lower or "how many" in question_lower:
                sql = f"SELECT COUNT(*) AS total_rows FROM {table_name};"

            else:
                st.warning("Could not automatically generate SQL for this question.")
                st.stop()

            st.write("Generated SQL:", sql)

            # Execute SQL
            try:
                result = pd.read_sql(sql, conn)
                st.write("### Result")
                st.dataframe(result)

                # Chart if numeric
                result_numeric_cols = result.select_dtypes(include=['int64','float64']).columns.tolist()
                if result_numeric_cols:
                    st.write("### 📊 Chart")
                    fig, ax = plt.subplots()
                    result.plot(kind="bar", x=result.columns[0], y=result_numeric_cols, ax=ax)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

            except Exception as e:
                st.error(f"Error executing SQL: {e}")

    except Exception as e:
        st.error(f"Error loading CSV: {e}")
