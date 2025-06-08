# File: frontend.py
# Artifact ID: streamlit_farm_data_frontend_20250608_updated
import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

# Streamlit page configuration
st.set_page_config(page_title="Farm Data Dashboard", layout="wide")

# Title
st.title("Farm Data Dashboard")

# Placeholder for data table and chart
table_placeholder = st.empty()
chart_placeholder = st.empty()

# Function to fetch data from receiver server
def fetch_data():
    try:
        response = requests.get("http://localhost:8002/data", timeout=5)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            df = pd.DataFrame(data)
            print(f"Available columns: {list(df.columns)}")
            return df
        else:
            st.warning(data.get("message", "No data received"))
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

# Main loop for real-time updates
while True:
    # Fetch data
    df = fetch_data()
    
    if not df.empty:
        # Define columns to display
        display_columns = ["farm_id", "crop_type", "yield_kg_per_hectare", 
                           "soil_moisture_percent", "soil_pH", "timestamp", "inference"]
        # Filter columns that exist in the DataFrame
        valid_columns = [col for col in display_columns if col in df.columns]
        if len(valid_columns) < len(display_columns):
            st.warning(f"Some columns missing: {set(display_columns) - set(valid_columns)}")
        
        # Display table
        with table_placeholder.container():
            st.subheader("Received Farm Data")
            try:
                st.dataframe(df[valid_columns], use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying table: {str(e)}")
        
        # Display bar chart for yield
        with chart_placeholder.container():
            st.subheader("Yield per Farm")
            try:
                fig = px.bar(df, x="farm_id", y="yield_kg_per_hectare",
                             title="Yield (kg/ha) by Farm",
                             labels={"yield_kg_per_hectare": "Yield (kg/ha)", "farm_id": "Farm ID"})
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error plotting chart: {str(e)}")
    else:
        st.info("Waiting for data from the server...")
    
    # Wait before next update
    time.sleep(5)  # Poll every 5 seconds