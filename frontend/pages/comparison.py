import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="HDB Listing Comparison Tool", layout="wide")

# -----------------------------
# Mock data
# Replace this later with your real PropertyGuru listing data
# -----------------------------
data = [
    {
        "listing_id": "L1",
        "title": "4-Room Flat at Punggol",
        "price": 568000,
        "town": "Punggol",
        "postal": "821312",
        "flat_type": "4-Room",
        "floor_area_sqm": 92,
        "floor_level": "10-12",
        "mrt_walk_min": 6,
        "hawker_walk_min": 8,
        "park_walk_min": 5,
        "school_walk_min": 9,
        "value_score": 82,
        "accessibility_score": 88,
        "fit_score": 85,
        "why": "Strong MRT access, good park access, and price is reasonable for the area."
    },
    {
        "listing_id": "L2",
        "title": "4-Room Flat at Tampines",
        "price": 610000,
        "town": "Tampines",
        "postal": "520241",
        "flat_type": "4-Room",
        "floor_area_sqm": 95,
        "floor_level": "07-09",
        "mrt_walk_min": 9,
        "hawker_walk_min": 4,
        "park_walk_min": 10,
        "school_walk_min": 6,
        "value_score": 75,
        "accessibility_score": 81,
        "fit_score": 79,
        "why": "Excellent hawker and school access, but slightly pricier than similar nearby options."
    },
    {
        "listing_id": "L3",
        "title": "4-Room Flat at Bishan",
        "price": 720000,
        "town": "Bishan",
        "postal": "570219",
        "flat_type": "4-Room",
        "floor_area_sqm": 88,
        "floor_level": "13-15",
        "mrt_walk_min": 4,
        "hawker_walk_min": 7,
        "park_walk_min": 6,
        "school_walk_min": 5,
        "value_score": 68,
        "accessibility_score": 92,
        "fit_score": 84,
        "why": "Very strong accessibility and central location, but comes at a premium price."
    },
    {
        "listing_id": "L4",
        "title": "4-Room Flat at Sengkang",
        "price": 545000,
        "town": "Sengkang",
        "postal": "541278",
        "flat_type": "4-Room",
        "floor_area_sqm": 93,
        "floor_level": "04-06",
        "mrt_walk_min": 11,
        "hawker_walk_min": 6,
        "park_walk_min": 4,
        "school_walk_min": 7,
        "value_score": 86,
        "accessibility_score": 74,
        "fit_score": 80,
        "why": "Very attractive price and decent amenities, though MRT access is weaker."
    },
]

df = pd.DataFrame(data)

# -----------------------------
# Helper functions
# -----------------------------
def format_currency(x):
    return f"${x:,.0f}"

def compute_average_score(df_compare):
    df_compare = df_compare.copy()
    df_compare["average_score"] = df_compare[
        ["value_score", "accessibility_score", "fit_score"]
    ].mean(axis=1)
    return df_compare

def bar_chart(df_compare):
    plot_df = df_compare.melt(
        id_vars=["title"],
        value_vars=["value_score", "accessibility_score", "fit_score"],
        var_name="Metric",
        value_name="Score"
    )

    metric_map = {
        "value_score": "Value-for-money",
        "accessibility_score": "Accessibility",
        "fit_score": "Fit"
    }
    plot_df["Metric"] = plot_df["Metric"].map(metric_map)

    fig = px.bar(
        plot_df,
        x="Metric",
        y="Score",
        color="title",
        barmode="group",
        text="Score",
        height=450
    )

    fig.update_yaxes(range=[0, 100])
    fig.update_traces(textposition="outside")
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend_title_text="Listing"
    )
    return fig

def value_label(row, cheapest_price):
    if row["price"] == cheapest_price:
        return "Best value among shortlisted options"
    elif row["value_score"] >= 80:
        return "Attractively priced relative to what it offers"
    elif row["value_score"] >= 70:
        return "Reasonably priced with some trade-offs"
    else:
        return "Priced at a premium relative to comparable options"

def accessibility_label(row, best_access_score):
    if row["accessibility_score"] == best_access_score:
        return "Strongest accessibility among shortlisted listings"
    elif row["accessibility_score"] >= 80:
        return "Good day-to-day convenience for key amenities"
    else:
        return "Less convenient overall, with some accessibility trade-offs"

def fit_label(row, best_fit_score):
    if row["fit_score"] == best_fit_score:
        return "Best match to the stated user preferences"
    elif row["fit_score"] >= 80:
        return "Generally aligns well with the user's priorities"
    else:
        return "Suitable, but less aligned with the user's preferred balance of factors"

# -----------------------------
# Header
# -----------------------------
st.title("HDB Listing Comparison Tool")
st.caption(
    "Compare shortlisted resale HDB listings by value-for-money, accessibility, and overall fit."
)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Select Listings to Compare")

listing_options = df["title"].tolist()
default_selection = listing_options[:3]

selected_titles = st.sidebar.multiselect(
    "Choose 2 to 4 listings",
    options=listing_options,
    default=default_selection
)

if len(selected_titles) < 2:
    st.warning("Please select at least 2 listings to compare.")
    st.stop()

if len(selected_titles) > 4:
    st.warning("Please select at most 4 listings for a clean comparison.")
    st.stop()

compare_df = df[df["title"].isin(selected_titles)].reset_index(drop=True)
compare_df = compute_average_score(compare_df)

best_overall = compare_df.loc[compare_df["average_score"].idxmax()]
best_value = compare_df.loc[compare_df["price"].idxmin()]
best_access = compare_df.loc[compare_df["accessibility_score"].idxmax()]
best_fit = compare_df.loc[compare_df["fit_score"].idxmax()]

# -----------------------------
# Overall comparison summary
# -----------------------------
st.subheader("Overall Comparison Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Best Overall Option", best_overall["title"], f'{best_overall["average_score"]:.1f}/100')
col2.metric("Best Value Option", best_value["title"], format_currency(best_value["price"]))
col3.metric("Most Accessible Option", best_access["title"], f'{best_access["accessibility_score"]}/100')

st.markdown(
    f"""
Among your shortlisted flats, **{best_overall['title']}** is the strongest all-round option,  
**{best_value['title']}** offers the best value for money, and **{best_access['title']}** performs best on accessibility.
"""
)

# -----------------------------
# Side-by-side listing cards
# -----------------------------
st.subheader("Side-by-Side Listing Comparison")

cols = st.columns(len(compare_df))
for i, (_, row) in enumerate(compare_df.iterrows()):
    with cols[i]:
        st.markdown(f"### {row['title']}")
        st.write(f"**Town:** {row['town']}")
        st.write(f"**Postal Code:** {row['postal']}")
        st.write(f"**Price:** {format_currency(row['price'])}")
        st.write(f"**Flat Type:** {row['flat_type']}")
        st.write(f"**Floor Area:** {row['floor_area_sqm']} sqm")
        st.write(f"**Floor Level:** {row['floor_level']}")
        st.write("---")

        st.write(f"**Value-for-money score:** {row['value_score']}/100")
        st.progress(int(row["value_score"]))
        st.caption(value_label(row, compare_df["price"].min()))

        st.write(f"**Accessibility score:** {row['accessibility_score']}/100")
        st.progress(int(row["accessibility_score"]))
        st.caption(accessibility_label(row, compare_df["accessibility_score"].max()))

        st.write(f"**Fit score:** {row['fit_score']}/100")
        st.progress(int(row["fit_score"]))
        st.caption(fit_label(row, compare_df["fit_score"].max()))

# -----------------------------
# Score comparison chart
# -----------------------------
st.subheader("Score Comparison Across Listings")
st.plotly_chart(bar_chart(compare_df), use_container_width=True)

# -----------------------------
# Refined output sections
# -----------------------------
st.subheader("Comparison Insights")

left_col, right_col = st.columns(2)

with left_col:
    st.markdown("#### Value-for-Money Comparison")
    st.write(
        f"**{best_value['title']}** appears to offer the best value for money among the shortlisted options, "
        f"with the lowest asking price at **{format_currency(best_value['price'])}**."
    )
    st.write(
        "This comparison helps users assess whether a flat appears attractively priced, fairly priced, "
        "or relatively expensive for what it offers."
    )

    st.markdown("#### Accessibility Comparison")
    st.write(
        f"**{best_access['title']}** provides the strongest accessibility, making it the most convenient option "
        "for day-to-day travel and access to nearby amenities."
    )
    st.write(
        "This output compares how well each shortlisted flat supports daily convenience through proximity "
        "to MRT stations, schools, hawker centres, and parks."
    )

with right_col:
    st.markdown("#### Fit Comparison")
    st.write(
        f"**{best_fit['title']}** is the strongest match to the user's stated priorities, based on its balance "
        "of affordability, convenience, and flat characteristics."
    )
    st.write(
        "This output highlights how closely each listing aligns with the user's preferred balance of key factors."
    )

    st.markdown("#### Trade-off Summary")
    st.write(
        f"While **{best_value['title']}** is the most affordable option, it may involve trade-offs in convenience. "
        f"On the other hand, **{best_access['title']}** performs strongly on accessibility, but may come at a higher price."
    )
    st.write(
        "This trade-off summary helps users weigh affordability against convenience and overall suitability, "
        "rather than relying only on a single headline score."
    )

# -----------------------------
# Detailed breakdown table
# -----------------------------
st.subheader("Detailed Breakdown")

table_df = compare_df[[
    "title", "price", "town", "postal", "flat_type", "floor_area_sqm",
    "mrt_walk_min", "hawker_walk_min", "park_walk_min", "school_walk_min",
    "value_score", "accessibility_score", "fit_score", "average_score"
]].copy()

table_df["price"] = table_df["price"].apply(format_currency)
table_df = table_df.rename(columns={
    "title": "Listing",
    "price": "Price",
    "town": "Town",
    "postal": "Postal Code",
    "flat_type": "Flat Type",
    "floor_area_sqm": "Floor Area (sqm)",
    "mrt_walk_min": "MRT Walk (min)",
    "hawker_walk_min": "Hawker Walk (min)",
    "park_walk_min": "Park Walk (min)",
    "school_walk_min": "School Walk (min)",
    "value_score": "Value-for-money",
    "accessibility_score": "Accessibility",
    "fit_score": "Fit",
    "average_score": "Overall Average Score"
})

table_df["Overall Average Score"] = table_df["Overall Average Score"].round(1)

st.dataframe(table_df, use_container_width=True, hide_index=True)

# -----------------------------
# Recommendation rationale
# -----------------------------
st.subheader("Recommendation Summary")

st.markdown(
    f"""
**Recommended all-round option: {best_overall['title']}**

This listing performs best overall across **value-for-money, accessibility, and fit**, making it the strongest balanced choice among the shortlisted flats.

- **Best overall score:** {best_overall['average_score']:.1f}/100  
- **Price:** {format_currency(best_overall['price'])}  
- **Why it stands out:** {best_overall['why']}  

If affordability is your main concern, **{best_value['title']}** may be the better choice.  
If daily convenience matters most, **{best_access['title']}** may be the more suitable option.
"""
)

with st.expander("How to interpret these scores"):
    st.write("""
- **Value-for-money score** reflects how attractive the asking price is relative to comparable listings or local benchmarks.
- **Accessibility score** reflects proximity to key amenities such as MRT stations, schools, hawker centres, and parks.
- **Fit score** reflects how well the listing matches the user's stated preferences and priorities.
- **Overall average score** gives a simple summary of performance across all three dimensions.
""")
