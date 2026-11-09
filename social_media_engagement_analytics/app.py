"""Interactive Streamlit dashboard."""
from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from analytics import load_and_clean, create_summaries
from dataset_source import ensure_dataset, DEFAULT_DATASET

st.set_page_config(page_title="Social Media Engagement Analytics", page_icon="📊", layout="wide")
st.title("📊 Social Media Engagement Analytics")
st.caption("Explore engagement patterns across platforms, content formats, posting times, and hashtags.")

uploaded = st.sidebar.file_uploader("Upload a social media CSV", type=["csv"])
sample_path = DEFAULT_DATASET
if uploaded is not None:
    source = uploaded
else:
    try:
        source = ensure_dataset(sample_path)
        st.sidebar.success("Using the GitHub social media engagement dataset.")
    except RuntimeError as exc:
        st.warning(str(exc))
        st.stop()

try:
    df = load_and_clean(source)
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

platforms = sorted(df["platform"].dropna().unique().tolist())
types = sorted(df["content_type"].dropna().unique().tolist())
selected_platforms = st.sidebar.multiselect("Platform", platforms, default=platforms)
selected_types = st.sidebar.multiselect("Content type", types, default=types)
filtered = df[df["platform"].isin(selected_platforms) & df["content_type"].isin(selected_types)].copy()
if filtered.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Posts", f"{len(filtered):,}")
c2.metric("Total engagement", f"{filtered['total_engagement'].sum():,.0f}")
c3.metric("Avg. engagement/post", f"{filtered['total_engagement'].mean():,.1f}")
rate = filtered["engagement_rate_pct"].mean()
c4.metric("Avg. engagement rate", f"{rate:.2f}%" if pd.notna(rate) else "Not available")

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Timing", "Hashtags", "Data"])
with tab1:
    left, right = st.columns(2)
    with left:
        st.subheader("Average engagement by platform")
        p = filtered.groupby("platform", as_index=False)["total_engagement"].mean().sort_values("total_engagement", ascending=False)
        fig, ax = plt.subplots(figsize=(7,4))
        sns.barplot(data=p, x="platform", y="total_engagement", ax=ax)
        ax.set_ylabel("Average total engagement")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
        st.pyplot(fig)
        plt.close(fig)
    with right:
        st.subheader("Average engagement by content type")
        p = filtered.groupby("content_type", as_index=False)["total_engagement"].mean().sort_values("total_engagement", ascending=False)
        fig, ax = plt.subplots(figsize=(7,4))
        sns.barplot(data=p, x="content_type", y="total_engagement", ax=ax)
        ax.set_ylabel("Average total engagement")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
        st.pyplot(fig)
        plt.close(fig)
    st.subheader("Monthly engagement trend")
    dated = filtered.dropna(subset=["post_date"]).copy()
    if not dated.empty:
        trend = dated.groupby(dated["post_date"].dt.to_period("M").astype(str), as_index=False)["total_engagement"].mean()
        trend.columns = ["month", "average_engagement"]
        st.line_chart(trend.set_index("month"))
    else:
        st.info("No usable post dates are available.")
    if "sentiment" in filtered.columns:
        st.subheader("Engagement by sentiment")
        sentiment_summary = filtered.groupby("sentiment", dropna=False)["total_engagement"].mean().sort_values(ascending=False)
        st.bar_chart(sentiment_summary)
    if "audience_gender" in filtered.columns:
        st.subheader("Audience gender distribution")
        st.bar_chart(filtered["audience_gender"].fillna("Unknown").value_counts())
with tab2:
    st.subheader("Average engagement by posting hour")
    timed = filtered.dropna(subset=["post_hour"])
    if not timed.empty:
        by_hour = timed.groupby("post_hour", as_index=False)["total_engagement"].mean().sort_values("post_hour")
        st.bar_chart(by_hour.set_index("post_hour"))
        heat = timed.pivot_table(index="post_day", columns="post_hour", values="total_engagement", aggfunc="mean")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heat = heat.reindex([d for d in day_order if d in heat.index])
        fig, ax = plt.subplots(figsize=(12,4))
        sns.heatmap(heat, cmap="YlGnBu", ax=ax)
        ax.set_title("Average engagement by day and hour")
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("Posting timestamps are missing or could not be parsed.")
with tab3:
    st.subheader("Hashtag performance")
    tags = []
    import re
    for _, row in filtered.iterrows():
        for tag in set(re.findall(r"(?<!\w)#([A-Za-z0-9_]+)", str(row["hashtags"]))):
            tags.append({"hashtag": tag.lower(), "engagement": row["total_engagement"], "rate": row["engagement_rate_pct"]})
    if tags:
        tag_df = pd.DataFrame(tags).groupby("hashtag").agg(
            post_count=("hashtag","count"),
            avg_engagement=("engagement","mean"),
            avg_engagement_rate_pct=("rate","mean")
        ).reset_index().sort_values(["post_count","avg_engagement"], ascending=False)
        st.dataframe(tag_df, use_container_width=True)
    else:
        st.info("No hashtags found. Ensure hashtags are in a column such as `hashtags` or included with # in the caption.")
with tab4:
    st.subheader("Filtered cleaned data")
    st.dataframe(filtered, use_container_width=True)
    st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8"), "filtered_social_media_posts.csv", "text/csv")
    st.subheader("Summary table")
    st.dataframe(create_summaries(filtered)["platform_summary"], use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("Engagement = likes + comments + shares. Rate requires impressions. Results describe the uploaded data and do not establish causation.")
