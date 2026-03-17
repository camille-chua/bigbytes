import streamlit as st
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="HDB Price Predictor", layout="wide")

st.title("🏠 HDB Resale Price Predictor")
st.write("Estimate the resale value of an HDB flat and gain insights into the surrounding property market.")

# ----------------------------
# SIDEBAR INPUTS
# ----------------------------

st.sidebar.header("Flat Details")

town = st.sidebar.selectbox(
    "Town",
    ["Clementi", "Bishan", "Tampines", "Woodlands", "Queenstown"]
)

postal_code = st.sidebar.text_input("Postal Code", "120345")

flat_type = st.sidebar.selectbox(
    "Flat Type",
    ["3 Room", "4 Room", "5 Room"]
)

floor_area = st.sidebar.slider(
    "Floor Area (sqm)",
    60,150,90
)

floor_level = st.sidebar.slider(
    "Floor Level",
    1,40,10
)

lease_remaining = st.sidebar.slider(
    "Lease Remaining (years)",
    40,99,80
)

# ----------------------------
# MOCK POSTAL CODE → LOCATION
# ----------------------------

def postal_to_coords(postal_code):
    random.seed(int(postal_code[-2:]) if postal_code.isdigit() else 10)
    lat = 1.30 + random.random()*0.05
    lon = 103.75 + random.random()*0.05
    return lat, lon

lat, lon = postal_to_coords(postal_code)

# ----------------------------
# MOCK AMENITY DISTANCES
# ----------------------------

def compute_amenities():
    mrt = random.randint(200,1200)
    school = random.randint(200,1000)
    supermarket = random.randint(100,800)
    park = random.randint(200,1200)
    return mrt, school, supermarket, park

mrt_dist, school_dist, supermarket_dist, park_dist = compute_amenities()

# ----------------------------
# LOCATION SCORE
# ----------------------------

location_score = (
    (2000-mrt_dist)*0.02 +
    (2000-school_dist)*0.01 +
    (2000-supermarket_dist)*0.015 +
    (2000-park_dist)*0.005
)

location_score = max(0, min(100, location_score))

# ----------------------------
# PRICE MODEL (MOCK)
# ----------------------------

base_price = {
    "Clementi":650000,
    "Bishan":750000,
    "Tampines":600000,
    "Woodlands":480000,
    "Queenstown":820000
}

flat_type_adj = {
    "3 Room":-40000,
    "4 Room":0,
    "5 Room":90000
}

predicted_price = (
    base_price[town]
    + flat_type_adj[flat_type]
    + floor_area*2000
    + floor_level*1200
    + lease_remaining*1400
    + location_score*1000
)

# ----------------------------
# PRICE RANGE
# ----------------------------

lower_bound = predicted_price * 0.95
upper_bound = predicted_price * 1.05

# ----------------------------
# MEDIAN PRICES BY TOWN
# ----------------------------

median_prices = {
    "Clementi":820000,
    "Bishan":900000,
    "Tampines":700000,
    "Woodlands":580000,
    "Queenstown":950000
}

median_price = median_prices[town]

percent_diff = ((predicted_price-median_price)/median_price)*100

# ----------------------------
# PRICE PER SQM
# ----------------------------

price_per_sqm = predicted_price / floor_area

town_avg_psqm = {
    "Clementi":8200,
    "Bishan":9000,
    "Tampines":7200,
    "Woodlands":6200,
    "Queenstown":9500
}

# ----------------------------
# MAIN OUTPUT
# ----------------------------

st.header("💰 Predicted Price")

st.metric(
    "Estimated Resale Price",
    f"${predicted_price:,.0f}"
)

st.write(
    f"Estimated price range: **${lower_bound:,.0f} – ${upper_bound:,.0f}**"
)

# ----------------------------
# PRICE COMPARISON
# ----------------------------

st.header("📊 Price Comparison")

if percent_diff > 0:
    st.success(f"This flat is estimated **{percent_diff:.1f}% ABOVE** the median price in {town}.")
else:
    st.info(f"This flat is estimated **{abs(percent_diff):.1f}% BELOW** the median price in {town}.")

# ----------------------------
# PRICE PER SQM
# ----------------------------

st.header("📏 Price per Square Meter")

st.write(f"Predicted price per sqm: **${price_per_sqm:,.0f}**")

st.write(f"Town average price per sqm: **${town_avg_psqm[town]:,}**")

# ----------------------------
# LOCATION SCORE
# ----------------------------

st.header("📍 Location Score")

st.metric("Amenity Score", f"{location_score:.0f}/100")

st.write("Nearby amenities:")

st.write(f"🚆 MRT distance: {mrt_dist} m")
st.write(f"🏫 School distance: {school_dist} m")
st.write(f"🛒 Supermarket distance: {supermarket_dist} m")
st.write(f"🌳 Park distance: {park_dist} m")

# ----------------------------
# BUYER INSIGHTS
# ----------------------------

st.header("💡 Buyer Insights")

if mrt_dist < 400:
    st.write("🚆 Flats within walking distance to MRT stations often command a price premium.")

if school_dist < 500:
    st.write("🏫 Proximity to schools increases demand among families.")

if lease_remaining < 60:
    st.warning("⚠️ Flats with low remaining lease may face financing restrictions.")

if floor_level > 25:
    st.write("🌇 High-floor units often have better views and resale value.")


# ----------------------------
# MOCK PAST TRANSACTIONS
# ----------------------------

def generate_transactions(town, flat_type):

    transactions = []

    for i in range(5):
        price = int(
            predicted_price * random.uniform(0.92, 1.08)
        )

        floor = random.randint(1, 40)
        area = floor_area + random.randint(-10, 10)

        transactions.append({
            "Town": town,
            "Flat Type": flat_type,
            "Block": f"{random.randint(100,999)}",
            "Street": f"{town} Ave {random.randint(1,5)}",
            "Floor Level": f"{floor}",
            "Floor Area": f"{area} sqm",
            "Resale Price": f"${price:,.0f}",
            "Month": f"2024-{random.randint(1,12):02d}"
        })

    return pd.DataFrame(transactions)


transactions_df = generate_transactions(town, flat_type)

# ----------------------------
# PAST TRANSACTIONS DISPLAY
# ----------------------------

st.header("📑 Recent Comparable Transactions")

st.write(
    f"Recent resale transactions for **{flat_type} flats in {town}**:"
)

st.dataframe(transactions_df)

# ----------------------------
# TRANSACTION INSIGHTS
# ----------------------------

prices = [
    int(row.replace("$","").replace(",",""))
    for row in transactions_df["Resale Price"]
]

avg_price = sum(prices) / len(prices)

diff_from_avg = ((predicted_price - avg_price) / avg_price) * 100

if diff_from_avg > 0:
    st.warning(
        f"Your predicted price is **{diff_from_avg:.1f}% higher** than recent transactions."
    )
else:
    st.success(
        f"Your predicted price is **{abs(diff_from_avg):.1f}% lower** than recent transactions."
    )

# ----------------------------
# TOWN PRICE COMPARISON CHART
# ----------------------------

st.header("🏙 Median Prices Across Towns")

town_df = pd.DataFrame({
    "Town": list(median_prices.keys()),
    "Median Price": list(median_prices.values())
})

st.bar_chart(
    town_df.set_index("Town")
)

# ----------------------------
# PRICE TREND CHART
# ----------------------------

st.header("📈 Median Price Trend")

price_trend_data = {
    "Clementi":[720000,750000,780000,800000,820000],
    "Bishan":[800000,830000,860000,880000,900000],
    "Tampines":[600000,630000,660000,680000,700000],
    "Woodlands":[500000,520000,540000,560000,580000],
    "Queenstown":[850000,880000,910000,930000,950000]
}

years = [2020,2021,2022,2023,2024]

trend_df = pd.DataFrame({
    "Year": years,
    "Median Price": price_trend_data[town]
})

st.line_chart(
    trend_df.set_index("Year")
)

growth_rate = (
    (price_trend_data[town][-1] - price_trend_data[town][0])
    / price_trend_data[town][0]
) * 100

st.write(
    f"Median prices in **{town} increased {growth_rate:.1f}% since 2020**."
)