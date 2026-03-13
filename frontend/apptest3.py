from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# =========================================================
# NestWise SG - Production-style Streamlit Prototype
# =========================================================
# RUN:
#   pip install streamlit pandas numpy pydeck requests
#   streamlit run streamlit_hdb_app_production.py
#
# WHAT'S NEW IN THIS VERSION
# - Cleaner structure inside one file (easy to split later)
# - API placeholders for backend integration
# - Better layout and copy for project demo
# - Interactive Singapore map with:
#     * recommended towns OR chosen town focus
#     * user postal-code anchors
#     * top-ranked amenity markers
# - Town recommender automatically hides when a town is chosen
# - Mock fallback mode when backend / map APIs are not connected yet
# =========================================================

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="NestWise SG",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Branding / constants
# -----------------------------
APP_NAME = "NestWise SG"
TAGLINE = "Know the fair price. Spot the steals. Find the right town."

BACKEND_BASE_URL = "http://127.0.0.1:8000"  # replace later
USE_BACKEND = False  # switch to True when your backend is ready
USE_ONEMAP = False   # switch to True when you want live geocoding / amenity lookups
ONEMAP_EMAIL = ""
ONEMAP_PASSWORD = ""
REQUEST_TIMEOUT = 12

TOWNS = [
    "Ang Mo Kio", "Bedok", "Bishan", "Bukit Batok", "Bukit Merah",
    "Bukit Panjang", "Choa Chu Kang", "Clementi", "Geylang", "Hougang",
    "Jurong East", "Jurong West", "Kallang/Whampoa", "Pasir Ris", "Punggol",
    "Queenstown", "Sembawang", "Sengkang", "Serangoon", "Tampines",
    "Toa Payoh", "Woodlands", "Yishun",
]

TOWN_CENTROIDS = {
    "Ang Mo Kio": (1.3691, 103.8454),
    "Bedok": (1.3236, 103.9273),
    "Bishan": (1.3508, 103.8485),
    "Bukit Batok": (1.3496, 103.7528),
    "Bukit Merah": (1.2819, 103.8239),
    "Bukit Panjang": (1.3786, 103.7620),
    "Choa Chu Kang": (1.3854, 103.7443),
    "Clementi": (1.3162, 103.7649),
    "Geylang": (1.3182, 103.8871),
    "Hougang": (1.3612, 103.8925),
    "Jurong East": (1.3331, 103.7437),
    "Jurong West": (1.3396, 103.7073),
    "Kallang/Whampoa": (1.3123, 103.8660),
    "Pasir Ris": (1.3731, 103.9494),
    "Punggol": (1.4043, 103.9020),
    "Queenstown": (1.2942, 103.7860),
    "Sembawang": (1.4491, 103.8201),
    "Sengkang": (1.3916, 103.8950),
    "Serangoon": (1.3523, 103.8730),
    "Tampines": (1.3496, 103.9568),
    "Toa Payoh": (1.3343, 103.8563),
    "Woodlands": (1.4360, 103.7865),
    "Yishun": (1.4294, 103.8354),
}

FLAT_TYPES = ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]
SCHOOL_OPTIONS = ["All schools", "Primary only", "Secondary only", "JC only", "Polytechnic only"]

AMENITY_LABELS = {
    "mrt": "MRT stations",
    "bus": "Bus stops",
    "healthcare": "Hospitals / polyclinics",
    "schools": "Schools",
    "hawker": "Hawker centres",
    "retail": "Shopping malls / supermarkets",
}

AMENITY_COLORS = {
    "mrt": [43, 108, 176, 180],
    "bus": [116, 173, 209, 160],
    "healthcare": [215, 48, 39, 180],
    "schools": [69, 117, 180, 180],
    "hawker": [253, 174, 97, 180],
    "retail": [171, 221, 164, 180],
    "anchor": [128, 0, 128, 220],
    "town": [20, 20, 20, 140],
}


# -----------------------------
# Data models
# -----------------------------
@dataclass
class UserInputs:
    budget: int
    flat_type: str
    floor_area_sqm: float
    lease_commence_year: int
    town: Optional[str]
    school_scope: str
    amenity_weights: Dict[str, float]
    landmark_postals: List[str]


# -----------------------------
# Utilities
# -----------------------------
def fmt_currency(x: float) -> str:
    return f"S${x:,.0f}"


def normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    total = sum(raw.values())
    if total == 0:
        n = len(raw)
        return {k: 1 / n for k in raw}
    return {k: v / total for k, v in raw.items()}


def top_priority_label(weights: Dict[str, float]) -> str:
    top_key = max(weights, key=weights.get)
    return AMENITY_LABELS[top_key]


def top_priority_keys(weights: Dict[str, float], n: int = 3) -> List[str]:
    return [k for k, _ in sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:n]]


def classify_listing(row: pd.Series) -> str:
    gap_pct = (row["asking_price"] - row["predicted_price"]) / row["predicted_price"]
    if gap_pct <= -0.05:
        return "🔥 Steal"
    if gap_pct <= 0.03:
        return "✅ Fair"
    if gap_pct <= 0.10:
        return "⚠️ Slightly overpriced"
    return "🚩 Overpriced"


def latlon_from_town(town: str) -> Tuple[float, float]:
    return TOWN_CENTROIDS.get(town, (1.3521, 103.8198))


def build_payload(inputs: UserInputs) -> Dict[str, Any]:
    return {
        "budget": inputs.budget,
        "flat_type": inputs.flat_type,
        "floor_area_sqm": inputs.floor_area_sqm,
        "lease_commence_year": inputs.lease_commence_year,
        "town": inputs.town,
        "school_scope": inputs.school_scope,
        "amenity_weights": inputs.amenity_weights,
        "postal_codes": inputs.landmark_postals,
    }


# -----------------------------
# API client placeholders
# -----------------------------
def post_json(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_prediction(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_BACKEND:
        raise RuntimeError("Backend mode is off.")
    return post_json("predict-price", payload)


def fetch_recent_transactions(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_BACKEND:
        raise RuntimeError("Backend mode is off.")
    return post_json("recent-transactions", payload)


def fetch_active_listings(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_BACKEND:
        raise RuntimeError("Backend mode is off.")
    return post_json("active-listings", payload)


def fetch_recommendations(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_BACKEND:
        raise RuntimeError("Backend mode is off.")
    return post_json("recommend-towns", payload)


def fetch_amenity_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_BACKEND:
        raise RuntimeError("Backend mode is off.")
    return post_json("amenity-map", payload)


# -----------------------------
# OneMap placeholders
# -----------------------------
def onemap_token() -> Optional[str]:
    if not USE_ONEMAP or not ONEMAP_EMAIL or not ONEMAP_PASSWORD:
        return None
    try:
        response = requests.post(
            "https://www.onemap.gov.sg/api/auth/post/getToken",
            json={"email": ONEMAP_EMAIL, "password": ONEMAP_PASSWORD},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("access_token")
    except Exception:
        return None


def geocode_postal_onemap(postal_code: str) -> Optional[Dict[str, Any]]:
    token = onemap_token()
    if not token:
        return None
    try:
        response = requests.get(
            "https://www.onemap.gov.sg/api/common/elastic/search",
            params={"searchVal": postal_code, "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": 1},
            headers={"Authorization": token},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None
        hit = results[0]
        return {
            "label": postal_code,
            "postal_code": postal_code,
            "lat": float(hit["LATITUDE"]),
            "lon": float(hit["LONGITUDE"]),
            "source": "OneMap",
        }
    except Exception:
        return None


# -----------------------------
# Mock fallback services
# -----------------------------
def mock_predict_price(inputs: UserInputs) -> float:
    base_by_type = {
        "2 ROOM": 320000,
        "3 ROOM": 410000,
        "4 ROOM": 560000,
        "5 ROOM": 700000,
        "EXECUTIVE": 850000,
    }
    town_multiplier = 1.0
    premium_towns = {"Bishan", "Queenstown", "Bukit Merah", "Kallang/Whampoa", "Toa Payoh"}
    affordable_towns = {"Yishun", "Woodlands", "Jurong West", "Choa Chu Kang", "Sembawang"}

    if inputs.town in premium_towns:
        town_multiplier = 1.18
    elif inputs.town in affordable_towns:
        town_multiplier = 0.92

    age_penalty = max(0, (2026 - inputs.lease_commence_year) * 2500)
    area_effect = max(0, (inputs.floor_area_sqm - 70) * 3800)
    amenity_bonus = 70000 * sum(inputs.amenity_weights.values()) / len(inputs.amenity_weights)
    postal_bonus = min(len(inputs.landmark_postals), 2) * 15000

    prediction = base_by_type[inputs.flat_type] * town_multiplier + area_effect - age_penalty + amenity_bonus + postal_bonus
    return max(prediction, 180000)


def mock_recent_transaction_median(inputs: UserInputs) -> float:
    pred = mock_predict_price(inputs)
    return pred * np.random.uniform(0.95, 1.05)


def mock_active_listings(inputs: UserInputs) -> pd.DataFrame:
    pred = mock_predict_price(inputs)
    town_pool = [inputs.town] if inputs.town else list(np.random.choice(TOWNS, 5, replace=False))
    rows = []
    for i in range(8):
        town = str(np.random.choice(town_pool))
        asking = pred * np.random.uniform(0.88, 1.18)
        transacted_proxy = pred * np.random.uniform(0.94, 1.06)
        rows.append({
            "listing_id": f"LST-{1000 + i}",
            "town": town,
            "flat_type": inputs.flat_type,
            "floor_area_sqm": round(inputs.floor_area_sqm + np.random.uniform(-8, 8), 1),
            "storey_range": str(np.random.choice(["04 TO 06", "07 TO 09", "10 TO 12", "13 TO 15"])),
            "asking_price": round(asking, 0),
            "predicted_price": round(pred * np.random.uniform(0.97, 1.03), 0),
            "recent_median_transacted": round(transacted_proxy, 0),
            "listing_url": f"https://example-property-site.com/listing/{1000 + i}",
        })

    df = pd.DataFrame(rows)
    df["asking_vs_predicted_pct"] = ((df["asking_price"] - df["predicted_price"]) / df["predicted_price"] * 100).round(1)
    df["valuation_label"] = df.apply(classify_listing, axis=1)
    return df


def mock_recommend_towns(inputs: UserInputs) -> pd.DataFrame:
    rows = []
    weights = inputs.amenity_weights
    for town in TOWNS:
        affordability = np.random.uniform(0.45, 0.95)
        amenity_fit = (
            weights["mrt"] * np.random.uniform(0.5, 1.0)
            + weights["bus"] * np.random.uniform(0.5, 1.0)
            + weights["healthcare"] * np.random.uniform(0.5, 1.0)
            + weights["schools"] * np.random.uniform(0.5, 1.0)
            + weights["hawker"] * np.random.uniform(0.5, 1.0)
            + weights["retail"] * np.random.uniform(0.5, 1.0)
        )
        landmark_fit = 0.12 if inputs.landmark_postals else 0.0
        score = 0.55 * affordability + 0.35 * amenity_fit + 0.10 * landmark_fit
        est_price = np.random.uniform(inputs.budget * 0.78, inputs.budget * 1.08)
        rows.append({
            "town": town,
            "match_score": round(score * 100, 1),
            "estimated_price": round(est_price, 0),
            "within_budget": bool(est_price <= inputs.budget),
            "why_it_matches": f"Strong fit for {top_priority_label(weights)} and reasonable price alignment.",
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["within_budget", "match_score"], ascending=[False, False]).head(5).reset_index(drop=True)


def mock_anchor_points(postals: List[str]) -> List[Dict[str, Any]]:
    anchors = []
    default_offsets = [(-0.015, 0.020), (0.022, -0.018)]
    for i, postal in enumerate(postals[:2]):
        base_lat, base_lon = 1.3521, 103.8198
        dlat, dlon = default_offsets[i]
        hit = geocode_postal_onemap(postal) if USE_ONEMAP else None
        anchors.append(hit or {
            "label": f"Anchor {i + 1}",
            "postal_code": postal,
            "lat": base_lat + dlat,
            "lon": base_lon + dlon,
            "source": "Mock",
        })
    return anchors


def mock_amenities_for_town(town: str, amenity_keys: List[str]) -> pd.DataFrame:
    center_lat, center_lon = latlon_from_town(town)
    rows = []
    for amenity in amenity_keys:
        for i in range(6):
            lat = center_lat + np.random.uniform(-0.02, 0.02)
            lon = center_lon + np.random.uniform(-0.02, 0.02)
            rows.append({
                "amenity_type": amenity,
                "amenity_label": f"{AMENITY_LABELS[amenity]} {i + 1}",
                "lat": lat,
                "lon": lon,
            })
    return pd.DataFrame(rows)


# -----------------------------
# Service orchestration
# -----------------------------
def get_prediction_bundle(inputs: UserInputs) -> Dict[str, Any]:
    payload = build_payload(inputs)
    if USE_BACKEND:
        try:
            prediction = fetch_prediction(payload)
            recent = fetch_recent_transactions(payload)
            listings = fetch_active_listings(payload)
            recommendations = None if inputs.town else fetch_recommendations(payload)
            return {
                "predicted_price": float(prediction["predicted_price"]),
                "confidence_low": float(prediction.get("confidence_band_low", prediction["predicted_price"])),
                "confidence_high": float(prediction.get("confidence_band_high", prediction["predicted_price"])),
                "recent_median_transacted": float(recent["median_transacted_price"]),
                "recent_period": recent.get("period", "recent period"),
                "listings_df": pd.DataFrame(listings.get("listings", [])),
                "recommendations_df": None if inputs.town else pd.DataFrame(recommendations.get("recommendations", [])),
                "source_mode": "backend",
            }
        except Exception as e:
            st.warning(f"Backend call failed. Falling back to mock data. Error: {e}")

    predicted = mock_predict_price(inputs)
    transacted = mock_recent_transaction_median(inputs)
    listings_df = mock_active_listings(inputs)
    recommendations_df = None if inputs.town else mock_recommend_towns(inputs)
    return {
        "predicted_price": predicted,
        "confidence_low": predicted * 0.96,
        "confidence_high": predicted * 1.04,
        "recent_median_transacted": transacted,
        "recent_period": "last 6 months",
        "listings_df": listings_df,
        "recommendations_df": recommendations_df,
        "source_mode": "mock",
    }


def get_map_bundle(inputs: UserInputs, recommendations_df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    anchor_points = mock_anchor_points(inputs.landmark_postals)
    top_amenities = top_priority_keys(inputs.amenity_weights, n=3)

    if inputs.town:
        center_town = inputs.town
        town_points = pd.DataFrame([{
            "town": center_town,
            "lat": latlon_from_town(center_town)[0],
            "lon": latlon_from_town(center_town)[1],
            "role": "Selected town",
        }])
    else:
        reco = recommendations_df if recommendations_df is not None else pd.DataFrame(columns=["town"])
        town_points = pd.DataFrame([
            {
                "town": row["town"],
                "lat": latlon_from_town(row["town"])[0],
                "lon": latlon_from_town(row["town"])[1],
                "role": "Recommended town",
            }
            for _, row in reco.iterrows()
        ])
        center_town = town_points.iloc[0]["town"] if not town_points.empty else "Singapore"

    amenity_frames = []
    for town_name in town_points["town"].tolist()[:3] if not town_points.empty else ["Tampines"]:
        amenity_frames.append(mock_amenities_for_town(town_name, top_amenities))
    amenities_df = pd.concat(amenity_frames, ignore_index=True) if amenity_frames else pd.DataFrame(columns=["amenity_type", "amenity_label", "lat", "lon"])

    if anchor_points:
        center_lat = float(np.mean([a["lat"] for a in anchor_points]))
        center_lon = float(np.mean([a["lon"] for a in anchor_points]))
    elif not town_points.empty:
        center_lat = float(town_points.iloc[0]["lat"])
        center_lon = float(town_points.iloc[0]["lon"])
    else:
        center_lat, center_lon = 1.3521, 103.8198

    return {
        "center_lat": center_lat,
        "center_lon": center_lon,
        "center_town": center_town,
        "town_points": town_points,
        "amenities_df": amenities_df,
        "anchor_points": anchor_points,
    }


# -----------------------------
# Input section
# -----------------------------
def build_user_inputs() -> UserInputs:
    st.sidebar.header("Tell us your dream flat")

    budget = st.sidebar.slider("Budget (S$)", min_value=250000, max_value=1500000, value=650000, step=10000)
    flat_type = st.sidebar.selectbox("Flat type", FLAT_TYPES, index=2)
    floor_area_sqm = st.sidebar.slider("Preferred floor area (sqm)", min_value=35.0, max_value=160.0, value=92.0, step=1.0)
    lease_commence_year = st.sidebar.slider("Lease commence year", min_value=1966, max_value=2025, value=1998, step=1)

    town_mode = st.sidebar.radio("Town preference", ["I want to choose a town", "Recommend towns for me"], index=1)
    town = st.sidebar.selectbox("Preferred town", TOWNS) if town_mode == "I want to choose a town" else None

    st.sidebar.markdown("### Amenity priorities")
    st.sidebar.caption("Use simple 0–5 sliders. We normalize them into weights behind the scenes.")

    raw_weights = {
        "mrt": st.sidebar.slider("MRT stations", 0, 5, 5),
        "bus": st.sidebar.slider("Bus stops", 0, 5, 3),
        "healthcare": st.sidebar.slider("Hospitals / polyclinics", 0, 5, 2),
        "schools": st.sidebar.slider("Schools", 0, 5, 3),
        "hawker": st.sidebar.slider("Hawker centres", 0, 5, 4),
        "retail": st.sidebar.slider("Shopping malls / supermarkets", 0, 5, 4),
    }
    amenity_weights = normalize_weights(raw_weights)

    school_scope = st.sidebar.selectbox("If schools matter, what kind?", SCHOOL_OPTIONS)

    st.sidebar.markdown("### Specific landmarks")
    st.sidebar.caption("Add up to 2 postal codes, such as your workplace or parents' home.")
    postal_1 = st.sidebar.text_input("Postal code 1 (optional)", placeholder="e.g. 119077")
    postal_2 = st.sidebar.text_input("Postal code 2 (optional)", placeholder="e.g. 560215")
    landmark_postals = [p.strip() for p in [postal_1, postal_2] if p.strip()]

    return UserInputs(
        budget=budget,
        flat_type=flat_type,
        floor_area_sqm=floor_area_sqm,
        lease_commence_year=lease_commence_year,
        town=town,
        school_scope=school_scope,
        amenity_weights=amenity_weights,
        landmark_postals=landmark_postals,
    )


# -----------------------------
# UI sections
# -----------------------------
def render_header():
    st.title(f"🏠 {APP_NAME}")
    st.subheader(TAGLINE)
    st.markdown(
        "This tool helps buyers and sellers compare **fair value**, **current asking prices**, and **recent sold benchmarks** in one place."
    )


def render_user_profile(inputs: UserInputs):
    st.markdown("### Your search profile")
    weights_df = pd.DataFrame({
        "Amenity": [AMENITY_LABELS[k] for k in inputs.amenity_weights.keys()],
        "Weight (%)": [round(v * 100, 1) for v in inputs.amenity_weights.values()],
    }).sort_values("Weight (%)", ascending=False)

    left, right = st.columns([1.25, 1])
    with left:
        st.write(f"**Budget:** {fmt_currency(inputs.budget)}")
        st.write(f"**Flat type:** {inputs.flat_type}")
        st.write(f"**Preferred size:** {inputs.floor_area_sqm} sqm")
        st.write(f"**Lease commence year:** {inputs.lease_commence_year}")
        st.write(f"**Town preference:** {inputs.town if inputs.town else 'Recommendation mode on'}")
        st.write(f"**School scope:** {inputs.school_scope}")
        st.write(f"**Anchor postals:** {', '.join(inputs.landmark_postals) if inputs.landmark_postals else 'None'}")
    with right:
        st.dataframe(weights_df, use_container_width=True, hide_index=True)


def render_value_cards(bundle: Dict[str, Any], budget: int):
    predicted = bundle["predicted_price"]
    transacted = bundle["recent_median_transacted"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Predicted fair value", fmt_currency(predicted))
    c2.metric("Recent transacted median", fmt_currency(transacted), delta=f"{(transacted / predicted - 1) * 100:.1f}% vs predicted")
    c3.metric("Your budget", fmt_currency(budget), delta=f"{(budget / predicted - 1) * 100:.1f}% vs predicted")

    st.caption(f"Data source mode: **{bundle['source_mode']}**")


def render_budget_banner(bundle: Dict[str, Any], budget: int):
    predicted = bundle["predicted_price"]
    gap = (budget - predicted) / predicted
    if gap >= 0.05:
        st.success(f"Good news: your budget is about {gap * 100:.1f}% above the predicted fair value.")
    elif gap >= -0.05:
        st.warning(f"Your budget is close to the predicted fair value ({gap * 100:.1f}%).")
    else:
        st.error(f"Your budget is about {abs(gap) * 100:.1f}% below the predicted fair value. Recommendation mode may help.")


def render_compare_tab(bundle: Dict[str, Any]):
    predicted = bundle["predicted_price"]
    transacted = bundle["recent_median_transacted"]
    conf_low = bundle["confidence_low"]
    conf_high = bundle["confidence_high"]

    compare_df = pd.DataFrame({
        "Metric": ["Predicted fair value", "Recent transacted median", "Confidence low", "Confidence high"],
        "Value": [predicted, transacted, conf_low, conf_high],
    })
    st.bar_chart(compare_df.set_index("Metric"))
    st.markdown(
        f"Our model estimates this flat at **{fmt_currency(predicted)}**. The recent transacted median is **{fmt_currency(transacted)}**, and the model confidence band is roughly **{fmt_currency(conf_low)} to {fmt_currency(conf_high)}**."
    )


def render_listing_tab(listings_df: pd.DataFrame):
    st.markdown("### Listing comparison")
    if listings_df.empty:
        st.info("No listings were returned.")
        return

    display_df = listings_df.copy()
    display_df["asking_price"] = display_df["asking_price"].map(fmt_currency)
    display_df["predicted_price"] = display_df["predicted_price"].map(fmt_currency)
    display_df["recent_median_transacted"] = display_df["recent_median_transacted"].map(fmt_currency)
    display_df["asking_vs_predicted_pct"] = display_df["asking_vs_predicted_pct"].map(lambda x: f"{x:+.1f}%")

    st.dataframe(
        display_df[[
            "listing_id", "town", "flat_type", "floor_area_sqm", "storey_range",
            "asking_price", "predicted_price", "recent_median_transacted",
            "asking_vs_predicted_pct", "valuation_label", "listing_url",
        ]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Most attractive listings")
    steals = listings_df.sort_values("asking_vs_predicted_pct").head(3)
    for _, row in steals.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['listing_id']} · {row['town']} · {row['storey_range']}**")
            st.write(
                f"Asking at **{fmt_currency(row['asking_price'])}**, which is **{abs(row['asking_vs_predicted_pct']):.1f}% {'below' if row['asking_vs_predicted_pct'] < 0 else 'above'}** the model estimate of **{fmt_currency(row['predicted_price'])}**."
            )
            st.link_button("Open original listing", row["listing_url"])


def render_recommendation_tab(inputs: UserInputs, recommendations_df: Optional[pd.DataFrame]):
    st.markdown("### Town recommendation engine")
    if inputs.town:
        st.info("Recommendation mode is hidden because you selected a town. The app is now focused on that chosen town only.")
        return

    if recommendations_df is None or recommendations_df.empty:
        st.info("No town recommendations returned.")
        return

    for _, row in recommendations_df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.markdown(f"**{row['town']}**")
            c1.write(row["why_it_matches"])
            c2.metric("Match score", f"{row['match_score']:.1f}")
            c3.metric("Est. price", fmt_currency(row["estimated_price"]))
            if row["within_budget"]:
                st.success("Within budget")
            else:
                st.warning("Slightly above budget")


def render_map_tab(inputs: UserInputs, map_bundle: Dict[str, Any]):
    st.markdown("### Interactive map")
    st.caption("The map highlights the top-ranked amenities, your anchor postals, and either your selected town or recommended towns.")

    town_points = map_bundle["town_points"]
    amenities_df = map_bundle["amenities_df"]
    anchor_points = map_bundle["anchor_points"]

    top_amenities = top_priority_keys(inputs.amenity_weights, n=3)
    st.write(f"**Default visible amenity layers:** {', '.join(AMENITY_LABELS[k] for k in top_amenities)}")

    visible_layers = st.multiselect(
        "Choose amenity layers to display",
        options=list(AMENITY_LABELS.keys()),
        default=top_amenities,
        format_func=lambda k: AMENITY_LABELS[k],
    )

    filtered_amenities = amenities_df[amenities_df["amenity_type"].isin(visible_layers)].copy() if not amenities_df.empty else amenities_df

    deck_layers = []

    if not town_points.empty:
        deck_layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=town_points,
                get_position="[lon, lat]",
                get_fill_color=AMENITY_COLORS["town"],
                get_radius=1000,
                pickable=True,
            )
        )
        deck_layers.append(
            pdk.Layer(
                "TextLayer",
                data=town_points,
                get_position="[lon, lat]",
                get_text="town",
                get_size=16,
                get_color=[0, 0, 0, 200],
                get_alignment_baseline="bottom",
            )
        )

    if anchor_points:
        anchor_df = pd.DataFrame(anchor_points)
        deck_layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=anchor_df,
                get_position="[lon, lat]",
                get_fill_color=AMENITY_COLORS["anchor"],
                get_radius=600,
                pickable=True,
            )
        )
        deck_layers.append(
            pdk.Layer(
                "TextLayer",
                data=anchor_df,
                get_position="[lon, lat]",
                get_text="label",
                get_size=14,
                get_color=[90, 0, 90, 220],
                get_alignment_baseline="bottom",
            )
        )

    for amenity_key in visible_layers:
        sub = filtered_amenities[filtered_amenities["amenity_type"] == amenity_key].copy() if not filtered_amenities.empty else pd.DataFrame()
        if sub.empty:
            continue
        deck_layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=sub,
                get_position="[lon, lat]",
                get_fill_color=AMENITY_COLORS[amenity_key],
                get_radius=260,
                pickable=True,
            )
        )

    tooltip = {
        "html": "<b>{town}</b><br/>{amenity_label}<br/>{postal_code}",
        "style": {"backgroundColor": "white", "color": "black"},
    }

    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=map_bundle["center_lat"],
            longitude=map_bundle["center_lon"],
            zoom=11.2,
            pitch=0,
        ),
        layers=deck_layers,
        tooltip=tooltip,
    )
    st.pydeck_chart(deck, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Anchor points")
        if anchor_points:
            st.dataframe(pd.DataFrame(anchor_points), use_container_width=True, hide_index=True)
        else:
            st.info("No anchor postal codes entered.")
    with right:
        st.markdown("#### Displayed towns")
        if not town_points.empty:
            st.dataframe(town_points, use_container_width=True, hide_index=True)
        else:
            st.info("No towns to display.")


def render_methodology():
    with st.expander("How this works"):
        st.markdown(
            """
            **Three pricing anchors**
            1. **Predicted fair value** from the hedonic model.
            2. **Recent transacted median** from actual transactions.
            3. **Current asking prices** from active listings.

            **Interpretation layer**
            Instead of making users read raw numbers only, the app translates them into decision labels like:
            - Steal
            - Fair
            - Slightly overpriced
            - Overpriced

            **Location layer**
            If users leave town blank, the recommendation engine suggests matching towns based on budget and amenity priorities.
            If users choose a town, recommendation mode is hidden and the app focuses on that town only.
            """
        )


def render_backend_next_steps():
    with st.expander("Backend integration next steps"):
        st.markdown(
            """
            **1. Finalize your frontend-backend contract**
            Agree on exact endpoint names, request payloads, and response fields.

            **2. Replace the mock functions gradually**
            Swap out:
            - `mock_predict_price`
            - `mock_recent_transaction_median`
            - `mock_active_listings`
            - `mock_recommend_towns`

            with real API calls in the `fetch_*` functions.

            **3. Keep one payload builder**
            The `build_payload()` function should remain the single source of truth for what the frontend sends.

            **4. Let the backend return clean JSON**
            Recommended endpoints:
            - `/predict-price`
            - `/recent-transactions`
            - `/active-listings`
            - `/recommend-towns`
            - `/amenity-map`

            **5. Keep presentation logic in the frontend**
            Labels like *steal* or *overpriced* can stay in the Streamlit layer.

            **6. For maps**
            Best setup: use OneMap for geocoding / location data, then render the map in Streamlit using Pydeck.
            """
        )


# -----------------------------
# Main app
# -----------------------------
def main():
    render_header()
    inputs = build_user_inputs()

    st.markdown("---")
    render_user_profile(inputs)

    run = st.button("Generate housing insights", type="primary", use_container_width=True)
    if not run:
        st.info("Set your preferences on the left, then click Generate housing insights.")
        render_methodology()
        render_backend_next_steps()
        return

    with st.spinner("Generating housing insights..."):
        bundle = get_prediction_bundle(inputs)
        map_bundle = get_map_bundle(inputs, bundle["recommendations_df"])

    st.markdown("---")
    render_value_cards(bundle, inputs.budget)
    render_budget_banner(bundle, inputs.budget)

    compare_tab, listing_tab, reco_tab, map_tab = st.tabs([
        "Compare prices",
        "Explore listings",
        "Town recommendations",
        "Map view",
    ])

    with compare_tab:
        render_compare_tab(bundle)

    with listing_tab:
        render_listing_tab(bundle["listings_df"])

    with reco_tab:
        render_recommendation_tab(inputs, bundle["recommendations_df"])

    with map_tab:
        render_map_tab(inputs, map_bundle)

    render_methodology()
    render_backend_next_steps()


if __name__ == "__main__":
    main()
