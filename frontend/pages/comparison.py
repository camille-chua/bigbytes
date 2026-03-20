import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output

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
        height=420
    )

    fig.update_yaxes(range=[0, 100])
    fig.update_traces(textposition="outside")
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend_title_text="Listing",
        paper_bgcolor="white",
        plot_bgcolor="white"
    )
    return fig

def value_label(row, cheapest_price):
    if row["price"] == cheapest_price:
        return "Best value among shortlisted options"
    elif row["value_score"] >= 80:
        return "Attractively priced relative to what it offers"
    elif row["value_score"] >= 70:
        return "Reasonably priced with some trade-offs"
    return "Priced at a premium relative to comparable options"

def accessibility_label(row, best_access_score):
    if row["accessibility_score"] == best_access_score:
        return "Strongest accessibility among shortlisted listings"
    elif row["accessibility_score"] >= 80:
        return "Good day-to-day convenience for key amenities"
    return "Less convenient overall, with some accessibility trade-offs"

def fit_label(row, best_fit_score):
    if row["fit_score"] == best_fit_score:
        return "Best match to the stated user preferences"
    elif row["fit_score"] >= 80:
        return "Generally aligns well with the user's priorities"
    return "Suitable, but less aligned with the user's preferred balance of factors"

def metric_card(label, value, subtitle=None):
    children = [
        html.Div(label, style={"fontSize": "14px", "color": "#6b7280", "marginBottom": "6px"}),
        html.Div(value, style={"fontSize": "24px", "fontWeight": "700", "color": "#111827"}),
    ]
    if subtitle:
        children.append(html.Div(subtitle, style={"fontSize": "13px", "color": "#2563eb", "marginTop": "6px"}))
    return html.Div(
        children,
        style={
            "background": "white",
            "border": "1px solid #e5e7eb",
            "borderRadius": "14px",
            "padding": "18px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"
        }
    )

def progress_bar(score):
    return html.Div(
        [
            html.Div(
                style={
                    "width": f"{score}%",
                    "height": "10px",
                    "borderRadius": "999px",
                    "background": "#2563eb"
                }
            )
        ],
        style={
            "width": "100%",
            "background": "#e5e7eb",
            "borderRadius": "999px",
            "height": "10px",
            "overflow": "hidden",
            "marginTop": "6px",
            "marginBottom": "6px"
        }
    )

def listing_card(row, cheapest_price, best_access_score, best_fit_score):
    return html.Div(
        [
            html.H3(row["title"], style={"marginTop": "0", "fontSize": "20px"}),
            html.P([html.B("Town: "), row["town"]]),
            html.P([html.B("Postal Code: "), row["postal"]]),
            html.P([html.B("Price: "), format_currency(row["price"])]),
            html.P([html.B("Flat Type: "), row["flat_type"]]),
            html.P([html.B("Floor Area: "), f'{row["floor_area_sqm"]} sqm']),
            html.P([html.B("Floor Level: "), row["floor_level"]]),
            html.Hr(),

            html.Div([html.B(f'Value-for-money score: {row["value_score"]}/100')]),
            progress_bar(row["value_score"]),
            html.Div(value_label(row, cheapest_price), style={"fontSize": "13px", "color": "#6b7280"}),

            html.Br(),
            html.Div([html.B(f'Accessibility score: {row["accessibility_score"]}/100')]),
            progress_bar(row["accessibility_score"]),
            html.Div(accessibility_label(row, best_access_score), style={"fontSize": "13px", "color": "#6b7280"}),

            html.Br(),
            html.Div([html.B(f'Fit score: {row["fit_score"]}/100')]),
            progress_bar(row["fit_score"]),
            html.Div(fit_label(row, best_fit_score), style={"fontSize": "13px", "color": "#6b7280"}),
        ],
        style={
            "background": "white",
            "border": "1px solid #e5e7eb",
            "borderRadius": "14px",
            "padding": "18px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
            "minWidth": "250px",
            "flex": "1"
        }
    )

app = Dash(__name__)
app.title = "HDB Listing Comparison Tool"

listing_options = [{"label": title, "value": title} for title in df["title"].tolist()]
default_selection = df["title"].tolist()[:3]

app.layout = html.Div(
    [
        html.Div(
            [
                html.H1("HDB Listing Comparison Tool", style={"marginBottom": "6px"}),
                html.P(
                    "Compare shortlisted resale HDB listings by value-for-money, accessibility, and overall fit.",
                    style={"color": "#6b7280", "marginTop": "0"}
                )
            ],
            style={"marginBottom": "24px"}
        ),

        html.Div(
            [
                html.Div(
                    [
                        html.H3("Select Listings to Compare"),
                        dcc.Dropdown(
                            id="listing-selector",
                            options=listing_options,
                            value=default_selection,
                            multi=True,
                            placeholder="Choose 2 to 4 listings"
                        ),
                        html.Div(
                            "Select between 2 and 4 listings.",
                            style={"fontSize": "13px", "color": "#6b7280", "marginTop": "8px"}
                        )
                    ],
                    style={
                        "background": "white",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "14px",
                        "padding": "18px",
                        "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"
                    }
                ),
                html.Div(id="validation-message", style={"marginTop": "14px"})
            ],
            style={"marginBottom": "24px"}
        ),

        html.Div(id="comparison-content")
    ],
    style={
        "maxWidth": "1400px",
        "margin": "0 auto",
        "padding": "24px",
        "background": "#f9fafb",
        "fontFamily": "Arial, sans-serif"
    }
)

@app.callback(
    Output("validation-message", "children"),
    Output("comparison-content", "children"),
    Input("listing-selector", "value")
)
def update_comparison(selected_titles):
    if not selected_titles or len(selected_titles) < 2:
        return (
            html.Div(
                "Please select at least 2 listings to compare.",
                style={
                    "background": "#fef2f2",
                    "color": "#b91c1c",
                    "border": "1px solid #fecaca",
                    "padding": "12px 14px",
                    "borderRadius": "10px"
                }
            ),
            html.Div()
        )

    if len(selected_titles) > 4:
        return (
            html.Div(
                "Please select at most 4 listings for a clean comparison.",
                style={
                    "background": "#fff7ed",
                    "color": "#c2410c",
                    "border": "1px solid #fdba74",
                    "padding": "12px 14px",
                    "borderRadius": "10px"
                }
            ),
            html.Div()
        )

    compare_df = df[df["title"].isin(selected_titles)].reset_index(drop=True)
    compare_df = compute_average_score(compare_df)

    best_overall = compare_df.loc[compare_df["average_score"].idxmax()]
    best_value = compare_df.loc[compare_df["price"].idxmin()]
    best_access = compare_df.loc[compare_df["accessibility_score"].idxmax()]
    best_fit = compare_df.loc[compare_df["fit_score"].idxmax()]

    cards = [
        listing_card(
            row,
            compare_df["price"].min(),
            compare_df["accessibility_score"].max(),
            compare_df["fit_score"].max()
        )
        for _, row in compare_df.iterrows()
    ]

    table_df = compare_df[[
        "title", "price", "town", "postal", "flat_type", "floor_area_sqm",
        "mrt_walk_min", "hawker_walk_min", "park_walk_min", "school_walk_min",
        "value_score", "accessibility_score", "fit_score", "average_score"
    ]].copy()

    table_df["price"] = table_df["price"].apply(format_currency)
    table_df["average_score"] = table_df["average_score"].round(1)

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

    content = html.Div(
        [
            html.H2("Overall Comparison Summary"),
            html.Div(
                [
                    metric_card("Best Overall Option", best_overall["title"], f'{best_overall["average_score"]:.1f}/100'),
                    metric_card("Best Value Option", best_value["title"], format_currency(best_value["price"])),
                    metric_card("Most Accessible Option", best_access["title"], f'{best_access["accessibility_score"]}/100'),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, 1fr)",
                    "gap": "16px",
                    "marginBottom": "16px"
                }
            ),
            html.P([
                "Among your shortlisted flats, ",
                html.B(best_overall["title"]),
                " is the strongest all-round option, ",
                html.B(best_value["title"]),
                " offers the best value for money, and ",
                html.B(best_access["title"]),
                " performs best on accessibility."
            ]),

            html.H2("Side-by-Side Listing Comparison", style={"marginTop": "28px"}),
            html.Div(cards, style={"display": "flex", "gap": "16px", "flexWrap": "wrap"}),

            html.H2("Score Comparison Across Listings", style={"marginTop": "28px"}),
            dcc.Graph(figure=bar_chart(compare_df)),

            html.H2("Comparison Insights", style={"marginTop": "28px"}),
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Value-for-Money Comparison"),
                            html.P([
                                html.B(best_value["title"]),
                                f" appears to offer the best value for money among the shortlisted options, with the lowest asking price at {format_currency(best_value['price'])}."
                            ]),
                            html.P(
                                "This comparison helps users assess whether a flat appears attractively priced, fairly priced, or relatively expensive for what it offers."
                            ),

                            html.H4("Accessibility Comparison", style={"marginTop": "22px"}),
                            html.P([
                                html.B(best_access["title"]),
                                " provides the strongest accessibility, making it the most convenient option for day-to-day travel and access to nearby amenities."
                            ]),
                            html.P(
                                "This output compares how well each shortlisted flat supports daily convenience through proximity to MRT stations, schools, hawker centres, and parks."
                            ),
                        ],
                        style={
                            "background": "white",
                            "border": "1px solid #e5e7eb",
                            "borderRadius": "14px",
                            "padding": "18px",
                            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"
                        }
                    ),
                    html.Div(
                        [
                            html.H4("Fit Comparison"),
                            html.P([
                                html.B(best_fit["title"]),
                                " is the strongest match to the user's stated priorities, based on its balance of affordability, convenience, and flat characteristics."
                            ]),
                            html.P(
                                "This output highlights how closely each listing aligns with the user's preferred balance of key factors."
                            ),

                            html.H4("Trade-off Summary", style={"marginTop": "22px"}),
                            html.P(
                                f"While {best_value['title']} is the most affordable option, it may involve trade-offs in convenience. On the other hand, {best_access['title']} performs strongly on accessibility, but may come at a higher price."
                            ),
                            html.P(
                                "This trade-off summary helps users weigh affordability against convenience and overall suitability, rather than relying only on a single headline score."
                            ),
                        ],
                        style={
                            "background": "white",
                            "border": "1px solid #e5e7eb",
                            "borderRadius": "14px",
                            "padding": "18px",
                            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"
                        }
                    )
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "16px"
                }
            ),

            html.H2("Detailed Breakdown", style={"marginTop": "28px"}),
            dash_table.DataTable(
                data=table_df.to_dict("records"),
                columns=[{"name": col, "id": col} for col in table_df.columns],
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "fontFamily": "Arial",
                    "fontSize": "13px",
                    "whiteSpace": "normal",
                    "height": "auto"
                },
                style_header={
                    "backgroundColor": "#eff6ff",
                    "fontWeight": "bold"
                },
                style_data={
                    "backgroundColor": "white",
                    "border": "1px solid #f1f5f9"
                }
            ),

            html.H2("Recommendation Summary", style={"marginTop": "28px"}),
            html.Div(
                [
                    html.P([html.B(f"Recommended all-round option: {best_overall['title']}")]),
                    html.P(
                        "This listing performs best overall across value-for-money, accessibility, and fit, making it the strongest balanced choice among the shortlisted flats."
                    ),
                    html.Ul(
                        [
                            html.Li(f"Best overall score: {best_overall['average_score']:.1f}/100"),
                            html.Li(f"Price: {format_currency(best_overall['price'])}"),
                            html.Li(f"Why it stands out: {best_overall['why']}"),
                        ]
                    ),
                    html.P(
                        f"If affordability is your main concern, {best_value['title']} may be the better choice. If daily convenience matters most, {best_access['title']} may be the more suitable option."
                    ),
                ],
                style={
                    "background": "white",
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "14px",
                    "padding": "18px",
                    "boxShadow": "0 1px 3px rgba(0,0,0,0.06)"
                }
            ),

            html.Details(
                [
                    html.Summary("How to interpret these scores", style={"cursor": "pointer", "fontWeight": "600"}),
                    html.Ul(
                        [
                            html.Li("Value-for-money score reflects how attractive the asking price is relative to comparable listings or local benchmarks."),
                            html.Li("Accessibility score reflects proximity to key amenities such as MRT stations, schools, hawker centres, and parks."),
                            html.Li("Fit score reflects how well the listing matches the user's stated preferences and priorities."),
                            html.Li("Overall average score gives a simple summary of performance across all three dimensions.")
                        ]
                    )
                ],
                style={
                    "marginTop": "20px",
                    "background": "white",
                    "border": "1px solid #e5e7eb",
                    "borderRadius": "14px",
                    "padding": "18px"
                }
            )
        ]
    )

    return html.Div(), content

if __name__ == "__main__":
    app.run(debug=True)

