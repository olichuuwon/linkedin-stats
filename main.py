import re
import io
from datetime import datetime

import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="LinkedIn Analytics Dashboard", layout="wide")
st.title("📊 LinkedIn Analytics Dashboard")

st.caption(
    "Upload both CSVs at once. The app auto-detects files by their names: "
    "one containing 'All posts' and one containing 'Metrics' (case-insensitive)."
)

# -----------------------------
# Helpers
# -----------------------------
POSTS_RENAMES = {
    "Post title": "Post Title",
    "Post link": "Post Link",
    "Post type": "Post Type",
    "Created date": "Created Date",
    "Impressions": "Impressions",
    "Clicks": "Clicks",
    "Click through rate (CTR)": "CTR",
    "Likes": "Likes",
    "Comments": "Comments",
    "Reposts": "Reposts",
    "Follows": "Follows",
    "Engagement rate": "Engagement Rate",
}


def read_posts_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file, skiprows=1)
    df = df.rename(columns=POSTS_RENAMES)
    df["Created Date"] = pd.to_datetime(df.get("Created Date"), errors="coerce")
    for c in [
        "Impressions",
        "Clicks",
        "CTR",
        "Likes",
        "Comments",
        "Reposts",
        "Follows",
        "Engagement Rate",
    ]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # fix CTR → as percentage if <=1
    if "CTR" in df.columns and df["CTR"].max() <= 1:
        df["CTR"] = df["CTR"] * 100
    return df


def read_metrics_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file, skiprows=1)
    if "Date" not in df.columns:
        st.warning("Could not find 'Date' column in Metrics file.")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in df.columns:
        if c != "Date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def extract_hashtags(series: pd.Series) -> list[str]:
    tags = set()
    if series is None:
        return []
    for text in series.dropna().astype(str):
        for tag in re.findall(r"#\w+", text):
            tags.add(tag)
    return sorted(tags, key=str.lower)


def download_csv_button(df: pd.DataFrame, filename: str, label: str):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(
        label, buf.getvalue().encode("utf-8"), file_name=filename, mime="text/csv"
    )


# -----------------------------
# Upload
# -----------------------------
uploaded = st.file_uploader(
    "Upload LinkedIn files (drop both CSVs together)",
    type=["csv"],
    accept_multiple_files=True,
)
boosted_config_file = st.file_uploader(
    "Optional: Upload boosted_config.csv (saved from previous run)", type=["csv"]
)

df_posts, df_metrics, df_boosted_config = None, None, None
if uploaded:
    for f in uploaded:
        name = f.name.lower()
        if "all posts" in name:
            df_posts = read_posts_csv(f)
        elif "metrics" in name:
            df_metrics = read_metrics_csv(f)

if boosted_config_file:
    df_boosted_config = pd.read_csv(boosted_config_file)
    if (
        "Post Title" not in df_boosted_config.columns
        or "Boosted" not in df_boosted_config.columns
    ):
        st.error("⚠️ boosted_config.csv must have 'Post Title' and 'Boosted' columns.")
        df_boosted_config = None

date_range = None

if df_posts is not None:
    # 🚀 Boosted Configuration
    st.markdown("## 🚀 Boosted Configuration")
    boosted_df = df_posts[["Created Date", "Post Title"]].copy()
    boosted_df["Boosted"] = False
    if df_boosted_config is not None:
        boosted_df = boosted_df.merge(
            df_boosted_config[["Post Title", "Boosted"]],
            on="Post Title",
            how="left",
            suffixes=("", "_saved"),
        )
        boosted_df["Boosted"] = boosted_df["Boosted_saved"].combine_first(
            boosted_df["Boosted"]
        )
        boosted_df = boosted_df.drop(columns=["Boosted_saved"])
    boosted_edited = st.data_editor(
        boosted_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Boosted": st.column_config.CheckboxColumn(help="Mark as boosted"),
            "Post Title": st.column_config.TextColumn(width="large"),
        },
    )
    download_csv_button(
        boosted_edited, "boosted_config.csv", "💾 Download Boosted Config"
    )

    # 🔍 Filters
    st.markdown("## 🔍 Filters")
    min_date, max_date = df_posts["Created Date"].min(), df_posts["Created Date"].max()
    if pd.isna(min_date) or pd.isna(max_date):
        min_date = datetime(2000, 1, 1)
        max_date = datetime.today()
    col1, col2 = st.columns([1, 3])
    with col1:
        date_range = st.date_input(
            "📅 Date range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date,
        )
    all_tags = extract_hashtags(df_posts.get("Post Title"))
    with col2:
        selected_tags = st.multiselect(
            "🏷️ Filter by hashtags", options=all_tags, placeholder="#DOTC, #OSIG, ..."
        )

    # apply filters
    filtered = df_posts.copy()
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[
            (filtered["Created Date"] >= start) & (filtered["Created Date"] <= end)
        ]
    if selected_tags:
        pattern = "|".join([re.escape(t) for t in selected_tags])
        mask = (
            filtered["Post Title"]
            .astype(str)
            .str.contains(pattern, case=False, regex=True)
        )
        filtered = filtered[mask]

    # 📈 Benchmarks
    st.markdown("## 📈 Benchmarks")
    cols = st.columns(5)
    metrics = {
        "Avg Engagement Rate": filtered["Engagement Rate"].mean(),
        "Avg CTR": filtered["CTR"].mean(),
        "Avg Impressions": filtered["Impressions"].mean(),
        "Avg Clicks": filtered["Clicks"].mean(),
        "Avg Likes": filtered["Likes"].mean(),
    }
    for col, (k, v) in zip(cols, metrics.items()):
        if "Rate" in k or "CTR" in k:
            col.metric(k, f"{(v or 0):.2f}%")
        else:
            col.metric(k, f"{(v or 0):,.0f}")

    # 🧾 Posts Table with flags
    st.markdown("## 🧾 Posts (Filtered)")

    def flag(value, avg):
        try:
            return "✅ Above Avg" if value >= avg else "❌ Below Avg"
        except Exception:
            return ""

    filtered_display = filtered.copy()
    filtered_display["ER Flag"] = filtered_display["Engagement Rate"].apply(
        lambda x: flag(x, metrics["Avg Engagement Rate"])
    )
    filtered_display["CTR Flag"] = filtered_display["CTR"].apply(
        lambda x: flag(x, metrics["Avg CTR"])
    )
    filtered_display["Impressions Flag"] = filtered_display["Impressions"].apply(
        lambda x: flag(x, metrics["Avg Impressions"])
    )
    filtered_display["Clicks Flag"] = filtered_display["Clicks"].apply(
        lambda x: flag(x, metrics["Avg Clicks"])
    )
    filtered_display["Likes Flag"] = filtered_display["Likes"].apply(
        lambda x: flag(x, metrics["Avg Likes"])
    )

    show_cols = [
        "Created Date",
        "Post Title",
        "Impressions",
        "Impressions Flag",
        "Clicks",
        "Clicks Flag",
        "CTR",
        "CTR Flag",
        "Engagement Rate",
        "ER Flag",
        "Likes",
        "Likes Flag",
        "Comments",
        "Reposts",
        "Follows",
        "Post Type",
        "Post Link",
    ]
    show_cols = [c for c in show_cols if c in filtered_display.columns]

    st.data_editor(
        filtered_display[show_cols], use_container_width=True, hide_index=True
    )

    # 🎯 Scatter
    st.markdown("## 🎯 Post Performance Scatter")
    merged = filtered.merge(
        boosted_edited[["Post Title", "Boosted"]], on="Post Title", how="left"
    )
    merged["Boosted"] = merged["Boosted"].fillna(False)
    scatter = (
        alt.Chart(merged)
        .mark_circle(size=80)
        .encode(
            x=alt.X("Impressions:Q"),
            y=alt.Y("Engagement Rate:Q"),
            color=alt.Color(
                "Boosted:N",
                legend=alt.Legend(title="Boosted"),
                scale=alt.Scale(domain=[True, False], range=["#ff6a00", "#9ca3af"]),
            ),
            tooltip=[
                "Post Title",
                "Created Date",
                "Impressions",
                "Clicks",
                "CTR",
                "Engagement Rate",
                "Boosted",
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(scatter.interactive(), use_container_width=True)

    # 📅 Weekday bar
    st.markdown("## 📅 Engagement by Weekday")
    wk = merged.copy()
    wk["Weekday"] = wk["Created Date"].dt.day_name()
    weekday_avg = wk.groupby("Weekday")["Engagement Rate"].mean().reset_index()
    weekday_avg = weekday_avg.sort_values("Engagement Rate", ascending=False)
    bar = (
        alt.Chart(weekday_avg)
        .mark_bar()
        .encode(
            x=alt.X("Weekday:N", sort=weekday_avg["Weekday"].tolist()),
            y=alt.Y("Engagement Rate:Q"),
            tooltip=["Weekday", "Engagement Rate"],
        )
        .properties(height=320)
    )
    st.altair_chart(bar, use_container_width=True)

# 🌐 Site Engagement Trends
if df_metrics is not None:
    st.markdown("## 🌐 Site Engagement Trends (Multi-Metric)")
    metric_cols = [
        c
        for c in df_metrics.columns
        if c != "Date" and pd.api.types.is_numeric_dtype(df_metrics[c])
    ]
    preferred = [
        "Impressions (total)",
        "Clicks (total)",
        "Reactions (total)",
        "Comments (total)",
        "Reposts (total)",
        "Engagement rate (total)",
    ]
    ordered_metrics = [c for c in preferred if c in metric_cols] + [
        c for c in metric_cols if c not in preferred
    ]
    selected_metrics = st.multiselect(
        "Choose metrics to plot", options=ordered_metrics, default=ordered_metrics[:3]
    )

    dfm = df_metrics.copy()
    if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        dfm = dfm[(dfm["Date"] >= start) & (dfm["Date"] <= end)]

    if selected_metrics:
        long_df = (
            dfm[["Date"] + selected_metrics]
            .melt("Date", var_name="Metric", value_name="Value")
            .dropna()
        )
        line = (
            alt.Chart(long_df)
            .mark_line(point=True)
            .encode(
                x="Date:T",
                y="Value:Q",
                color=alt.Color(
                    "Metric:N",
                    legend=alt.Legend(title="Metrics"),
                    scale=alt.Scale(scheme="category10"),
                ),
                tooltip=["Date:T", "Metric:N", "Value:Q"],
            )
            .properties(height=420)
        )
        st.altair_chart(line.interactive(), use_container_width=True)
    else:
        st.info("Select at least one metric to plot.")
