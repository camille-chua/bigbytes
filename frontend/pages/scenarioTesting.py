import streamlit as st
import pandas as pd
import numpy as np

from dataclasses import dataclass
from typing import Optional, Dict, List


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Explore Trade-offs", layout="wide")


# =========================================================
# CUSTOM STYLING
# =========================================================
st.markdown("""
<style>
/* App background */
.stApp {
    background: #F7F5F2;
    color: #2F3A45;
}

/* Main content width feel */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Headers */
h1, h2, h3 {
    color: #243746;
    letter-spacing: -0.02em;
}

h1 {
    font-weight: 800;
}

h2, h3 {
    font-weight: 700;
}

/* Paragraphs / labels */
p, label, div {
    color: #35424D;
}

/* Cards */
.soft-card {
    background: #FFFFFF;
    border: 1px solid #E6E9EC;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: 0 4px 14px rgba(36, 55, 70, 0.05);
    margin-bottom: 0.8rem;
}

.summary-card {
    background: #FFFFFF;
    border: 1px solid #DCE5EA;
    border-left: 6px solid #5B8FA8;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: 0 4px 14px rgba(36, 55, 70, 0.05);
    margin-bottom: 1rem;
}

.success-card {
    background: #F5FAF7;
    border: 1px solid #D7EADF;
    border-left: 6px solid #7BAE8E;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}

.warning-card {
    background: #FFF8EF;
    border: 1px solid #F3DEC1;
    border-left: 6px solid #D9A35F;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
}

/* Metrics */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E3E8EC;
    padding: 1rem;
    border-radius: 18px;
    box-shadow: 0 4px 12px rgba(36, 55, 70, 0.04);
}

/* Buttons */
.stButton > button {
    background: #5B8FA8;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.55rem 1rem;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton > button:hover {
    background: #4B7B92;
    color: white;
}

/* Secondary-looking buttons inside expander can still inherit,
   but bookmark icon buttons remain neat */
button[kind="secondary"] {
    border-radius: 12px;
}

/* Inputs */
.stSelectbox div[data-baseweb="select"] > div,
.stNumberInput div[data-baseweb="input"] > div,
.stTextInput div[data-baseweb="input"] > div {
    border-radius: 12px !important;
}

/* Dataframe container */
[data-testid="stDataFrame"] {
    background: white;
    border: 1px solid #E3E8EC;
    border-radius: 16px;
    padding: 0.4rem;
}

/* Expander */
details {
    background: #FFFFFF;
    border: 1px solid #E3E8EC;
    border-radius: 18px;
    padding: 0.4rem 0.8rem;
    box-shadow: 0 4px 12px rgba(36, 55, 70, 0.04);
    margin-bottom: 1rem;
}

/* Captions */
.small-muted {
    color: #6B7A88;
    font-size: 0.95rem;
}

/* Listing title row */
.listing-title {
    font-weight: 700;
    color: #243746;
    margin-bottom: 0.25rem;
}

.listing-meta {
    color: #5B6975;
    font-size: 0.95rem;
}

/* Section spacing */
.section-gap {
    margin-top: 1rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# MOCK DATA + HELPER LOGIC
# =========================================================

TOWNS = [
    "Punggol",
    "Sengkang",
    "Tampines",
    "Jurong West",
    "Woodlands",
    "Yishun",
    "Toa Payoh",
    "Queenstown",
    "Bukit Merah",
    "Bishan",
]

CHEAPER_TOWN_MAP = {
    "Bishan": "Yishun",
    "Queenstown": "Sengkang",
    "Bukit Merah": "Punggol",
    "Toa Payoh": "Woodlands",
    "Tampines": "Jurong West",
    "Punggol": "Sengkang",
    "Sengkang": "Punggol",
    "Woodlands": "Yishun",
    "Yishun": "Woodlands",
    "Jurong West": "Woodlands",
}

FLAT_TYPES = ["2 ROOM", "3 ROOM", "4 ROOM", "5 ROOM", "EXECUTIVE"]
FLAT_TYPE_TO_INT = {name: i for i, name in enumerate(FLAT_TYPES)}
INT_TO_FLAT_TYPE = {i: name for i, name in enumerate(FLAT_TYPES)}


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


def classify_listing(row):
    pct = row["asking_vs_predicted_pct"]
    if pct <= -5:
        return "Undervalued"
    elif pct <= 5:
        return "Fair"
    return "Overpriced"


def top_priority_keys(w, n=3):
    return sorted(w, key=w.get, reverse=True)[:n]


def top_priority_label(w):
    if not w:
        return "amenities"
    return max(w, key=w.get).upper()


def mock_predict_price(inputs: UserInputs) -> float:
    base = {
        "2 ROOM": 320000,
        "3 ROOM": 410000,
        "4 ROOM": 560000,
        "5 ROOM": 700000,
        "EXECUTIVE": 850000,
    }

    mul = 1.0
    if inputs.town in {"Bishan", "Queenstown", "Bukit Merah", "Kallang/Whampoa", "Toa Payoh"}:
        mul = 1.18
    elif inputs.town in {"Yishun", "Woodlands", "Jurong West", "Choa Chu Kang", "Sembawang"}:
        mul = 0.92

    pred = (
        base[inputs.flat_type] * mul
        + max(0, (inputs.floor_area_sqm - 70) * 3800)
        - max(0, (2026 - inputs.lease_commence_year) * 2500)
        + 70000 * sum(inputs.amenity_weights.values()) / max(len(inputs.amenity_weights), 1)
        + min(len(inputs.landmark_postals), 2) * 15000
    )
    return max(pred, 180000)


def mock_active_listings(inputs: UserInputs) -> pd.DataFrame:
    seed = abs(
        hash(
            (
                inputs.budget,
                inputs.flat_type,
                round(inputs.floor_area_sqm, 1),
                inputs.lease_commence_year,
                inputs.town,
                round(inputs.amenity_weights.get("mrt", 0), 1),
                round(inputs.amenity_weights.get("hawker", 0), 1),
                round(inputs.amenity_weights.get("mall", 0), 1),
            )
        )
    ) % (2**32)

    rng = np.random.default_rng(seed)

    pred = mock_predict_price(inputs)
    town_pool = [inputs.town] if inputs.town else list(rng.choice(TOWNS, 5, replace=False))
    rows = []

    for i in range(8):
        town = str(rng.choice(town_pool))
        asking = pred * rng.uniform(0.88, 1.18)

        rows.append(
            {
                "listing_id": f"LST-{1000+i}",
                "town": town,
                "flat_type": inputs.flat_type,
                "floor_area_sqm": round(inputs.floor_area_sqm + rng.uniform(-8, 8), 1),
                "storey_range": str(rng.choice(["04 TO 06", "07 TO 09", "10 TO 12", "13 TO 15"])),
                "asking_price": round(asking),
                "predicted_price": round(pred * rng.uniform(0.97, 1.03)),
                "recent_median_transacted": round(pred * rng.uniform(0.94, 1.06)),
                "listing_url": f"https://example-property-site.com/listing/{1000+i}",
            }
        )

    df = pd.DataFrame(rows)
    df["asking_vs_predicted_pct"] = (
        (df["asking_price"] - df["predicted_price"]) / df["predicted_price"] * 100
    ).round(1)
    df["valuation_label"] = df.apply(classify_listing, axis=1)
    return df


def compute_listing_scores(df: pd.DataFrame, budget: int, w: Dict[str, float]) -> pd.DataFrame:
    df = df.copy()
    if df.empty:
        return df

    df["value_component"] = (
        100 - df["asking_vs_predicted_pct"].clip(-20, 20).abs() * 2.5
    ).clip(0, 100)

    df["budget_buffer_pct"] = ((budget - df["asking_price"]) / budget * 100).clip(-30, 30)
    df["budget_component"] = (50 + df["budget_buffer_pct"] * 1.5).clip(0, 100)

    top_keys = top_priority_keys(w, 3)
    rng_base = 17
    amenity_scores = []

    for i, _ in df.reset_index(drop=True).iterrows():
        rng = np.random.default_rng(rng_base + i)
        score = sum(w[k] * rng.uniform(60, 95) for k in top_keys)
        amenity_scores.append(score / max(sum(w[k] for k in top_keys), 1e-9))

    df["amenity_fit_score"] = np.round(amenity_scores, 1)
    df["overall_value_score"] = np.round(
        0.45 * df["value_component"]
        + 0.25 * df["budget_component"]
        + 0.30 * df["amenity_fit_score"],
        1,
    )
    return df


def make_inputs(
    budget,
    flat_type,
    floor_area,
    lease_year,
    town,
    mrt,
    hawker,
    mall,
):
    return UserInputs(
        budget=budget,
        flat_type=flat_type,
        floor_area_sqm=floor_area,
        lease_commence_year=lease_year,
        town=town,
        school_scope="Primary",
        amenity_weights={"mrt": mrt, "hawker": hawker, "mall": mall},
        landmark_postals=[],
    )


def run_search(inputs: UserInputs):
    pred = mock_predict_price(inputs)
    df = mock_active_listings(inputs)
    df = compute_listing_scores(df, inputs.budget, inputs.amenity_weights)
    df = df.sort_values("overall_value_score", ascending=False).reset_index(drop=True)
    return pred, df


def listing_payload_from_row(row):
    return {
        "listing_id": row["listing_id"],
        "town": row["town"],
        "flat_type": row["flat_type"],
        "floor_area_sqm": float(row["floor_area_sqm"]),
        "asking_price": int(row["asking_price"]),
        "overall_value_score": float(row["overall_value_score"]),
    }


def save_listing(row):
    payload = listing_payload_from_row(row)
    if payload not in st.session_state.saved_listings:
        st.session_state.saved_listings.append(payload)


def get_metrics(pred, df):
    avg_score = round(df["overall_value_score"].mean(), 1) if not df.empty else 0
    return {
        "pred": pred,
        "count": len(df),
        "avg_score": avg_score,
    }


def build_summary(baseline_inputs, scenario_inputs, baseline_pred, scenario_pred, baseline_df, scenario_df):
    messages = []

    price_diff = scenario_pred - baseline_pred
    listing_diff = len(scenario_df) - len(baseline_df)
    score_diff = scenario_df["overall_value_score"].mean() - baseline_df["overall_value_score"].mean()

    if price_diff > 0:
        messages.append(f"Estimated fair price increases by about ${price_diff:,.0f}.")
    elif price_diff < 0:
        messages.append(f"Estimated fair price decreases by about ${abs(price_diff):,.0f}.")
    else:
        messages.append("Estimated fair price stays about the same.")

    if listing_diff > 0:
        messages.append(f"You unlock {listing_diff} more matching live listings.")
    elif listing_diff < 0:
        messages.append(f"You have {abs(listing_diff)} fewer matching live listings.")
    else:
        messages.append("The number of matching listings stays the same.")

    if scenario_inputs.flat_type != baseline_inputs.flat_type:
        messages.append(
            f"Flat type changes from {baseline_inputs.flat_type} to {scenario_inputs.flat_type}."
        )

    if scenario_inputs.town != baseline_inputs.town:
        messages.append(f"Town changes from {baseline_inputs.town} to {scenario_inputs.town}.")

    area_diff = scenario_inputs.floor_area_sqm - baseline_inputs.floor_area_sqm
    if area_diff > 0:
        messages.append(f"You are asking for about {area_diff:.0f} sqm more space.")
    elif area_diff < 0:
        messages.append(f"You are accepting about {abs(area_diff):.0f} sqm less space.")

    if score_diff > 1:
        messages.append("Average overall value score improves slightly under this scenario.")
    elif score_diff < -1:
        messages.append("Average overall value score weakens slightly under this scenario.")

    return messages


def scenario_downsize_one_room(inputs: UserInputs) -> UserInputs:
    idx = FLAT_TYPE_TO_INT[inputs.flat_type]
    new_idx = max(0, idx - 1)
    return UserInputs(
        budget=inputs.budget,
        flat_type=INT_TO_FLAT_TYPE[new_idx],
        floor_area_sqm=max(40, inputs.floor_area_sqm - 10),
        lease_commence_year=inputs.lease_commence_year,
        town=inputs.town,
        school_scope=inputs.school_scope,
        amenity_weights=inputs.amenity_weights.copy(),
        landmark_postals=inputs.landmark_postals.copy(),
    )


def scenario_increase_budget(inputs: UserInputs, amount: int = 50000) -> UserInputs:
    return UserInputs(
        budget=inputs.budget + amount,
        flat_type=inputs.flat_type,
        floor_area_sqm=inputs.floor_area_sqm,
        lease_commence_year=inputs.lease_commence_year,
        town=inputs.town,
        school_scope=inputs.school_scope,
        amenity_weights=inputs.amenity_weights.copy(),
        landmark_postals=inputs.landmark_postals.copy(),
    )


def scenario_accept_older_lease(inputs: UserInputs, years: int = 10) -> UserInputs:
    return UserInputs(
        budget=inputs.budget,
        flat_type=inputs.flat_type,
        floor_area_sqm=inputs.floor_area_sqm,
        lease_commence_year=max(1980, inputs.lease_commence_year - years),
        town=inputs.town,
        school_scope=inputs.school_scope,
        amenity_weights=inputs.amenity_weights.copy(),
        landmark_postals=inputs.landmark_postals.copy(),
    )


def scenario_cheaper_town(inputs: UserInputs) -> UserInputs:
    cheaper_town = CHEAPER_TOWN_MAP.get(inputs.town, "Woodlands")
    return UserInputs(
        budget=inputs.budget,
        flat_type=inputs.flat_type,
        floor_area_sqm=inputs.floor_area_sqm,
        lease_commence_year=inputs.lease_commence_year,
        town=cheaper_town,
        school_scope=inputs.school_scope,
        amenity_weights=inputs.amenity_weights.copy(),
        landmark_postals=inputs.landmark_postals.copy(),
    )


def scenario_prioritise_affordability(inputs: UserInputs) -> UserInputs:
    return UserInputs(
        budget=inputs.budget,
        flat_type=inputs.flat_type,
        floor_area_sqm=inputs.floor_area_sqm,
        lease_commence_year=inputs.lease_commence_year,
        town=inputs.town,
        school_scope=inputs.school_scope,
        amenity_weights={"mrt": 0.6, "hawker": 0.5, "mall": 0.4},
        landmark_postals=inputs.landmark_postals.copy(),
    )


def best_next_move_text(baseline_inputs: UserInputs):
    candidates = {
        "Downsize one room": scenario_downsize_one_room(baseline_inputs),
        "Increase budget by $50k": scenario_increase_budget(baseline_inputs, 50000),
        "Accept older lease": scenario_accept_older_lease(baseline_inputs, 10),
        "Try a cheaper nearby town": scenario_cheaper_town(baseline_inputs),
    }

    baseline_pred, baseline_df = run_search(baseline_inputs)
    baseline_count = len(baseline_df)

    options = []
    for label, scn in candidates.items():
        pred, df = run_search(scn)
        options.append(
            {
                "label": label,
                "pred_diff": pred - baseline_pred,
                "count_diff": len(df) - baseline_count,
            }
        )

    best_more_options = max(options, key=lambda x: x["count_diff"])
    best_lower_price = min(options, key=lambda x: x["pred_diff"])

    if best_more_options["count_diff"] > 0:
        return (
            f"To unlock more options, try **{best_more_options['label']}** "
            f"({best_more_options['count_diff']:+.0f} listings)."
        )

    if best_lower_price["pred_diff"] < 0:
        return (
            f"To reduce price most, try **{best_lower_price['label']}** "
            f"({best_lower_price['pred_diff']:+,.0f})."
        )

    return "Your current preferences are already relatively balanced. Try adjusting one major constraint such as budget, room count, or town."


# =========================================================
# SESSION STATE
# =========================================================
if "baseline_inputs" not in st.session_state:
    st.session_state.baseline_inputs = None

if "saved_listings" not in st.session_state:
    st.session_state.saved_listings = []

if "show_tradeoffs" not in st.session_state:
    st.session_state.show_tradeoffs = False

if "scenario_override" not in st.session_state:
    st.session_state.scenario_override = None


# =========================================================
# PAGE
# =========================================================
st.markdown('<div class="summary-card"><h1>Explore Trade-offs</h1><p class="small-muted">Search first, then test how changes in budget, room type, town, or space needs affect price and live listings.</p></div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. Search form
# ---------------------------------------------------------
st.markdown('<div class="soft-card">', unsafe_allow_html=True)
st.header("1. Search for current listings")

with st.form("baseline_form"):
    c1, c2 = st.columns(2)

    with c1:
        budget = st.slider("Budget", 300000, 1200000, 700000, step=10000)
        flat_type = st.selectbox("Flat type", FLAT_TYPES, index=2)
        floor_area = st.slider("Preferred floor area (sqm)", 40, 140, 95)
        lease_year = st.slider("Lease commence year", 1980, 2025, 2015)

    with c2:
        town = st.selectbox("Town", TOWNS, index=0)
        mrt = st.slider("MRT priority", 0.0, 1.0, 1.0, 0.1)
        hawker = st.slider("Hawker priority", 0.0, 1.0, 0.8, 0.1)
        mall = st.slider("Mall priority", 0.0, 1.0, 0.7, 0.1)

    searched = st.form_submit_button("Search")
st.markdown('</div>', unsafe_allow_html=True)

if searched:
    st.session_state.baseline_inputs = make_inputs(
        budget, flat_type, floor_area, lease_year, town, mrt, hawker, mall
    )
    st.session_state.show_tradeoffs = False
    st.session_state.scenario_override = None

# ---------------------------------------------------------
# 2. Baseline results
# ---------------------------------------------------------
if st.session_state.baseline_inputs is not None:
    baseline_inputs = st.session_state.baseline_inputs
    baseline_pred, baseline_df = run_search(baseline_inputs)
    baseline_metrics = get_metrics(baseline_pred, baseline_df)

    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.header("2. Recommended live listings")

    m1, m2, m3 = st.columns(3)
    m1.metric("Estimated fair price", f"${baseline_metrics['pred']:,.0f}")
    m2.metric("Matching live listings", baseline_metrics["count"])
    m3.metric("Average value score", baseline_metrics["avg_score"])

    st.markdown(
        f"""
        <div class="summary-card">
            <div><strong>Your current search</strong></div>
            <div class="small-muted">
                Budget: <strong>${baseline_inputs.budget:,.0f}</strong> &nbsp; | &nbsp;
                Flat type: <strong>{baseline_inputs.flat_type}</strong> &nbsp; | &nbsp;
                Town: <strong>{baseline_inputs.town}</strong> &nbsp; | &nbsp;
                Floor area: <strong>{baseline_inputs.floor_area_sqm:.0f} sqm</strong> &nbsp; | &nbsp;
                Top priority: <strong>{top_priority_label(baseline_inputs.amenity_weights)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Top matching listings")
    for _, row in baseline_df.head(5).iterrows():
        col1, col2 = st.columns([9, 1])

        with col1:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="listing-title">{row['listing_id']} · {row['town']}</div>
                    <div class="listing-meta">
                        {row['flat_type']} · {row['floor_area_sqm']} sqm ·
                        Asking: <strong>${row['asking_price']:,.0f}</strong> ·
                        {row['valuation_label']} ·
                        Score: <strong>{row['overall_value_score']}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button(" ", key=f"save_base_{row['listing_id']}", icon=":material/bookmark:"):
                save_listing(row)
                st.toast(f"Saved {row['listing_id']}")

    if st.button("Scenario test", icon=":material/tune:"):
        st.session_state.show_tradeoffs = True
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Trade-offs expander
# ---------------------------------------------------------
if st.session_state.baseline_inputs is not None and st.session_state.show_tradeoffs:
    baseline_inputs = st.session_state.baseline_inputs
    baseline_pred, baseline_df = run_search(baseline_inputs)

    with st.expander("Explore trade-offs", expanded=True, icon=":material/tune:"):
        st.markdown(
            '<div class="success-card"><strong>Tip:</strong> Start with a quick what-if option, then fine-tune using the custom sliders below.</div>',
            unsafe_allow_html=True,
        )

        # Quick presets
        st.subheader("Quick what-if options")
        q1, q2, q3, q4, q5 = st.columns(5)

        with q1:
            if st.button("Downsize one room", key="preset_downsize"):
                st.session_state.scenario_override = scenario_downsize_one_room(baseline_inputs)

        with q2:
            if st.button("Increase budget +$50k", key="preset_budget"):
                st.session_state.scenario_override = scenario_increase_budget(baseline_inputs, 50000)

        with q3:
            if st.button("Accept older lease", key="preset_older"):
                st.session_state.scenario_override = scenario_accept_older_lease(baseline_inputs, 10)

        with q4:
            if st.button("Try cheaper town", key="preset_town"):
                st.session_state.scenario_override = scenario_cheaper_town(baseline_inputs)

        with q5:
            if st.button("Prioritise affordability", key="preset_afford"):
                st.session_state.scenario_override = scenario_prioritise_affordability(baseline_inputs)

        active_scenario_base = st.session_state.scenario_override or baseline_inputs

        # Custom sliders
        st.subheader("Custom trade-off explorer")
        s1, s2 = st.columns(2)

        with s1:
            scenario_budget = st.slider(
                "Scenario budget",
                300000,
                1200000,
                int(active_scenario_base.budget),
                step=10000,
            )
            scenario_flat_type = st.selectbox(
                "Scenario flat type",
                FLAT_TYPES,
                index=FLAT_TYPES.index(active_scenario_base.flat_type),
                key="scenario_flat_type",
            )
            scenario_floor_area = st.slider(
                "Scenario floor area (sqm)",
                40,
                140,
                int(active_scenario_base.floor_area_sqm),
                key="scenario_floor_area",
            )
            scenario_lease_year = st.slider(
                "Scenario lease commence year",
                1980,
                2025,
                int(active_scenario_base.lease_commence_year),
                key="scenario_lease_year",
            )

        with s2:
            scenario_town = st.selectbox(
                "Scenario town",
                TOWNS,
                index=TOWNS.index(active_scenario_base.town),
                key="scenario_town",
            )
            scenario_mrt = st.slider(
                "Scenario MRT priority",
                0.0,
                1.0,
                float(active_scenario_base.amenity_weights.get("mrt", 1.0)),
                0.1,
                key="scenario_mrt",
            )
            scenario_hawker = st.slider(
                "Scenario hawker priority",
                0.0,
                1.0,
                float(active_scenario_base.amenity_weights.get("hawker", 0.8)),
                0.1,
                key="scenario_hawker",
            )
            scenario_mall = st.slider(
                "Scenario mall priority",
                0.0,
                1.0,
                float(active_scenario_base.amenity_weights.get("mall", 0.7)),
                0.1,
                key="scenario_mall",
            )

        scenario_inputs = make_inputs(
            scenario_budget,
            scenario_flat_type,
            scenario_floor_area,
            scenario_lease_year,
            scenario_town,
            scenario_mrt,
            scenario_hawker,
            scenario_mall,
        )

        scenario_pred, scenario_df = run_search(scenario_inputs)

        # What changed
        st.subheader("What changed")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Baseline price", f"${baseline_pred:,.0f}")
        c2.metric("Scenario price", f"${scenario_pred:,.0f}", delta=f"{scenario_pred - baseline_pred:,.0f}")
        c3.metric("Baseline listings", len(baseline_df))
        c4.metric("Scenario listings", len(scenario_df), delta=len(scenario_df) - len(baseline_df))

        for msg in build_summary(
            baseline_inputs,
            scenario_inputs,
            baseline_pred,
            scenario_pred,
            baseline_df,
            scenario_df,
        ):
            st.markdown(f'<div class="warning-card">{msg}</div>', unsafe_allow_html=True)

        # Best next move
        st.subheader("Best next move")
        st.markdown(
            f'<div class="success-card">{best_next_move_text(baseline_inputs)}</div>',
            unsafe_allow_html=True,
        )

        # Side-by-side listings
        st.subheader("Baseline vs scenario listings")
        left, right = st.columns(2)

        with left:
            st.markdown('<div class="soft-card"><strong>Baseline top listings</strong></div>', unsafe_allow_html=True)
            st.dataframe(
                baseline_df[
                    [
                        "listing_id",
                        "town",
                        "flat_type",
                        "floor_area_sqm",
                        "asking_price",
                        "valuation_label",
                        "overall_value_score",
                    ]
                ].head(5),
                use_container_width=True,
            )

        with right:
            st.markdown('<div class="soft-card"><strong>Scenario top listings</strong></div>', unsafe_allow_html=True)
            st.dataframe(
                scenario_df[
                    [
                        "listing_id",
                        "town",
                        "flat_type",
                        "floor_area_sqm",
                        "asking_price",
                        "valuation_label",
                        "overall_value_score",
                    ]
                ].head(5),
                use_container_width=True,
            )

        # Save scenario listings
        st.subheader("Save scenario listings for comparison")
        for _, row in scenario_df.head(5).iterrows():
            col1, col2 = st.columns([9, 1])

            with col1:
                st.markdown(
                    f"""
                    <div class="soft-card">
                        <div class="listing-title">{row['listing_id']} · {row['town']}</div>
                        <div class="listing-meta">
                            {row['flat_type']} · {row['floor_area_sqm']} sqm ·
                            Asking: <strong>${row['asking_price']:,.0f}</strong> ·
                            {row['valuation_label']} ·
                            Score: <strong>{row['overall_value_score']}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col2:
                if st.button(" ", key=f"save_scn_{row['listing_id']}", icon=":material/bookmark:"):
                    save_listing(row)
                    st.toast(f"Saved {row['listing_id']}")

# ---------------------------------------------------------
# 4. Saved listings preview
# ---------------------------------------------------------
st.header("Saved for comparison")
if st.session_state.saved_listings:
    st.dataframe(pd.DataFrame(st.session_state.saved_listings), use_container_width=True)
else:
    st.markdown(
        '<div class="soft-card"><span class="small-muted">No listings saved yet. Use the bookmark icon to build your shortlist for the Comparison tab.</span></div>',
        unsafe_allow_html=True,
    )