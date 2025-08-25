import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
import sqlite3
import hashlib

# ---------------------------
# Initialize Google AI Client
# ---------------------------
client = genai.Client(api_key="AIzaSyD2zTSTy_jdaW489MqHg-rGJF4nDPoQQQY")  # <-- Replace with your Google AI API key

# ---------------------------
# Database Setup
# ---------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
""")
conn.commit()

# ---------------------------
# Session State Initialization
# ---------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

# ---------------------------
# Helper Functions
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def rerun_app():
    st.session_state['rerun'] = True
    st.stop()  # Stops current run, Streamlit will rerun from the top

# ---------------------------
# Login Page
# ---------------------------
def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username and password:
            hashed = hash_password(password)
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
            if c.fetchone():
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                rerun_app()
            else:
                st.error("Invalid username or password.")
        else:
            st.error("Enter both username and password.")

    st.markdown("Don't have an account? Go to **Signup** tab.")

# ---------------------------
# Signup Page
# ---------------------------
def signup_page():
    st.title("📝 Signup")
    new_user = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    
    if st.button("Signup"):
        if new_user and new_password:
            c.execute("SELECT * FROM users WHERE username=?", (new_user,))
            if c.fetchone():
                st.error("Username already exists. Choose another.")
            else:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_user, hash_password(new_password)))
                conn.commit()
                st.success(f"Account created for {new_user}! Please login.")
                rerun_app()
        else:
            st.error("Enter username and password to signup.")

# ---------------------------
# Dashboard Page
# ---------------------------
def dashboard():
    st.markdown(f"### Welcome, {st.session_state['username']}!")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        rerun_app()
    
    st.markdown("Upload a CSV file, visualize charts, and get AI analysis.")
    
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        try:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except:
                df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
            st.success("File loaded successfully!")
            
            # Dataset Summary
            st.subheader("📈 Dataset Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Rows", df.shape[0])
            col2.metric("Columns", df.shape[1])
            col3.metric("Numeric Columns", len(df.select_dtypes(include=['int64','float64']).columns))
            col4.metric("Categorical Columns", len(df.select_dtypes(include=['object']).columns))
            
            # Tabs: Data, Charts, AI Insights
            tabs = st.tabs(["Data", "Charts", "AI Insights"])
            
            # ---- Data Tab ----
            with tabs[0]:
                st.subheader("Dataset Preview")
                st.dataframe(df, use_container_width=True)
            
            # ---- Charts Tab ----
            with tabs[1]:
                st.subheader("Visualizations")
                numeric_cols = df.select_dtypes(include=['int64','float64']).columns.tolist()
                if not numeric_cols:
                    st.warning("No numeric columns available for plotting.")
                else:
                    chart_type = st.selectbox("Select chart type", ["Line", "Bar", "Pie"])
                    selected_col = st.selectbox("Select column for chart", numeric_cols)
                    
                    fig = None
                    if chart_type == "Line":
                        fig = px.line(df, y=selected_col, title=f"Line Chart - {selected_col}", color_discrete_sequence=px.colors.sequential.Viridis)
                    elif chart_type == "Bar":
                        fig = px.bar(df, y=selected_col, title=f"Bar Chart - {selected_col}", color_discrete_sequence=px.colors.sequential.Plasma)
                    elif chart_type == "Pie":
                        if df[selected_col].nunique() > 20:
                            st.warning("Too many unique values for Pie chart, choose another column.")
                        else:
                            fig = px.pie(df, names=selected_col, title=f"Pie Chart - {selected_col}", color_discrete_sequence=px.colors.sequential.Agsunset)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            # ---- AI Insights Tab ----
            with tabs[2]:
                st.subheader("AI Analysis")
                st.write("Generating insights using Google AI...")
                summary = df.describe(include='all').to_string()
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Analyze this dataset and provide key insights:\n{summary}"
                    )
                    insights_text = response.text
                    st.success("AI Analysis Generated ✅")
                    st.write(insights_text)

                    # Download button
                    st.download_button("📥 Download AI Insights", data=insights_text, file_name="ai_insights.txt", mime="text/plain")
                except Exception as e:
                    st.error(f"Error in AI request: {e}")
                    
        except Exception as e:
            st.error(f"Error loading file: {e}")
    else:
        st.info("Please upload a CSV file to get started.")

# ---------------------------
# Main App
# ---------------------------
def main():
    st.set_page_config(page_title="Data Insights App", layout="wide")
    
    if not st.session_state['logged_in']:
        page = st.sidebar.selectbox("Go to", ["Login", "Signup"])
        if page == "Login":
            login_page()
        else:
            signup_page()
    else:
        dashboard()
    
    # Handle rerun
    if st.session_state['rerun']:
        st.session_state['rerun'] = False
        st.stop()  # Stops current run to allow rerun

if __name__ == "__main__":
    main()
