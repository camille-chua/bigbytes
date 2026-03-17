import streamlit as st
import pandas as pd
import numpy as np

st.title("🏠 HDB Resale Price Predictor")

st.write("Estimate the resale value of an HDB flat and view market insights.")

# ---------------------------
# USER INPUTS
# ---------------------------

st.sidebar.header("Flat Details")

town = st.sidebar.selectbox(
    "Town",
    ["Clementi", "Bishan", "Tampines", "Woodlands", "Queenstown"]
)

flat_type = st.sidebar.selectbox(
    "Flat Type",
    ["3 Room", "4 Room", "5 Room"]
)

floor_area = st.sidebar.slider(
    "Floor Area (sqm)",
    60, 150, 90
)

floor_level = st.sidebar.slider(
    "Floor Level",
    1, 40, 10
)

lease_remaining = st.sidebar.slider(
    "Lease Remaining (years)",
    40, 99, 80
)

# ---------------------------
# MOCK PRICE PREDICTION
# ---------------------------

# Mock coefficients
base_price = {
    "Clementi": 600000,
    "Bishan": 700000,
    "Tampines": 550000,
    "Woodlands": 450000,
    "Queenstown": 750000
}

flat_type_adj = {
    "3 Room": -50000,
    "4 Room": 0,
    "5 Room": 80000
}

predicted_price = (
    base_price[town]
    + flat_type_adj[flat_type]
    + (floor_area * 2000)
    + (floor_level * 1000)
    + (lease_remaining * 1500)
)

st.header("💰 Predicted Price")

st.metric(
    "Estimated Resale Price",
    f"${predicted_price:,.0f}"
)

# ---------------------------
# USER INSIGHTS
# ---------------------------

st.header("📊 Market Insights")

# Mock transaction data
data = pd.DataFrame({
    "Town": ["Clementi", "Bishan", "Tampines", "Woodlands", "Queenstown"],
    "Average Price": [850000, 900000, 700000, 600000, 950000]
})

st.subheader("Average Resale Prices by Town")

st.bar_chart(
    data.set_index("Town")
)

# Price comparison insight
town_avg = data[data["Town"] == town]["Average Price"].values[0]

if predicted_price > town_avg:
    st.success("This flat is estimated ABOVE the town average price.")
else:
    st.info("This flat is estimated BELOW the town average price.")

# ---------------------------
# USER ADVICE
# ---------------------------

st.header("💡 Buyer Insight")

if lease_remaining < 60:
    st.warning("⚠️ Flats with low remaining lease may have financing restrictions.")

if floor_level > 20:
    st.write("🌇 High floor units often command a premium due to better views.")

if floor_area > 110:
    st.write("📏 Larger floor area increases property value and family suitability.")