import plotly.io as pio
import plotly.graph_objects as go
import geopandas as gpd

def load_gdf(entry: dict, drop_cols: list = None, maui_only: bool = False) -> gpd.GeoDataFrame:
    """Load a GeoDataFrame from an inputs entry dict, reproject to WGS84, and optionally drop columns."""
    path  = entry["path"]
    layer = entry.get("layer")
    bbox  = (724000, 2263000, 806000, 2334000) if maui_only else None  # Maui bbox EPSG:32604
    gdf   = gpd.read_file(path, layer=layer, bbox=bbox).to_crs(epsg=4326)
    if drop_cols:
        gdf = gdf.drop(columns=drop_cols, errors="ignore")
    print(f"{path.stem:<45} {gdf.shape[0]:>7,} rows × {gdf.shape[1]:>2} columns | CRS: {gdf.crs}")
    return gdf

# ── Color palettes ─────────────────────────────────────────────────────────────

COLORS = {
    # Single accent — histograms, bar charts of continuous vars
    "accent":       "#2E86AB",

    # Sequential — choropleth maps, heatmaps (light → dark)
    "seq":          "Blues",

    # Diverging — depth to water table, elevation relative to sea level, etc.
    "div":          "RdBu",

    # Qualitative — categorical variables with no inherent order
    # (island, analysis_point_source, sma_constraints, etc.)
    "qual": [
        "#2E86AB",  # blue
        "#A23B72",  # plum
        "#F18F01",  # amber
        "#C73E1D",  # rust
        "#3B1F2B",  # near-black
        "#44BBA4",  # teal
        "#E94F37",  # red-orange
    ],

    # Ordered categorical — suitability classes (bad → good)
    "ordered": {
        "low":    "#C73E1D",   # rust red
        "medium": "#F18F01",   # amber
        "high":   "#44BBA4",   # teal
    },

    # Binary flags (True/False, 0/1)
    "binary": {
        0: "#DADADA",   # light gray
        1: "#2E86AB",   # blue
    },

    # Missing values
    "null":         "#F5F5F5",

    # Map tiles
    "mapbox_style": "carto-positron",
}

# ── Base Plotly theme ──────────────────────────────────────────────────────────

BASE_LAYOUT = dict(
    font=dict(family="Arial, sans-serif", size=13, color="#2b2b2b"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    title_font=dict(size=15, color="#2b2b2b"),
    margin=dict(l=60, r=40, t=60, b=60),
    colorway=COLORS["qual"],
    xaxis=dict(
        showgrid=True,
        gridcolor="#ebebeb",
        linecolor="#cccccc",
        zeroline=False,
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#ebebeb",
        linecolor="#cccccc",
        zeroline=False,
    ),
    legend=dict(
        bgcolor="white",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
)

def apply_theme(fig, title=None, xaxis_title=None, yaxis_title=None, height=420):
    """Apply the standard MPAT layout theme to a Plotly figure."""
    updates = BASE_LAYOUT.copy()
    if title:        updates["title"]  = title
    if height:       updates["height"] = height
    fig.update_layout(**updates)
    if xaxis_title:  fig.update_xaxes(title_text=xaxis_title)
    if yaxis_title:  fig.update_yaxes(title_text=yaxis_title)
    return fig

# ── Pandas Styled DataFrame theme ─────────────────────────────────────────────

TABLE_STYLES = [
    {"selector": "caption",
     "props": [("font-size", "14px"), ("font-weight", "bold"),
               ("color", "#2b2b2b"), ("padding-bottom", "8px"),
               ("text-align", "left")]},
    {"selector": "thead th",
     "props": [("background-color", "#2E86AB"), ("color", "white"),
               ("font-weight", "bold"), ("text-align", "left"),
               ("padding", "8px 12px")]},
    {"selector": "tbody td",
     "props": [("padding", "6px 12px"), ("border-bottom", "1px solid #ebebeb")]},
    {"selector": "tbody tr:hover",
     "props": [("background-color", "#f0f8ff")]},
    {"selector": "table",
     "props": [("border-collapse", "collapse"), ("width", "100%")]},
]

def style_table(df, caption=None, bar_cols=None, pct_cols=None, int_cols=None, float_cols=None):
    """
    Apply the standard MPAT styled DataFrame theme.

    Parameters
    ----------
    df        : pd.DataFrame
    caption   : str, optional table caption
    bar_cols  : list of column names to render as bar charts
    pct_cols  : list of column names to format as percentages
    int_cols  : list of column names to format as integers
    float_cols: list of column names to format as 2 decimal floats
    """
    styler = df.style.set_table_styles(TABLE_STYLES).hide(axis="index")
    if caption:
        styler = styler.set_caption(caption)
    if bar_cols:
        for col in bar_cols:
            styler = styler.bar(subset=[col], color=COLORS["accent"], vmin=0)
    if pct_cols:
        styler = styler.format({col: "{:.1f}%" for col in pct_cols})
    if int_cols:
        styler = styler.format({col: "{:,.0f}" for col in int_cols})
    if float_cols:
        styler = styler.format({col: "{:,.2f}" for col in float_cols})
    return styler


# ── Plotly figure helpers ──────────────────────────────────────────────────────

def make_title(title: str, subtitle: str, *, y: float = 0.97) -> dict:
    """Standard MPAT centered title block with subtitle."""
    return dict(
        text=f"<b>{title}</b><br><sup>{subtitle}</sup>",
        x=0.5,
        y=y,
        xanchor="center",
        yanchor="top",
        font=dict(size=18, family="Arial, sans-serif", color="#2b2b2b"),
    )


def make_layout(*, t: int = 60, b: int = 60, l: int = 60, r: int = 40, **kwargs) -> dict:
    """Return a BASE_LAYOUT copy with custom margins and any overrides."""
    layout = BASE_LAYOUT.copy()
    layout["margin"] = dict(l=l, r=r, t=t, b=b)
    layout.update(kwargs)
    return layout