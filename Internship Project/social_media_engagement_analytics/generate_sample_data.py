"""Create a synthetic dataset for demonstrating the analytics pipeline."""
from pathlib import Path
import numpy as np
import pandas as pd

def main():
    rng = np.random.default_rng(42)
    n = 1200
    start = pd.Timestamp("2025-01-01")
    dates = start + pd.to_timedelta(rng.integers(0, 365, size=n), unit="D")
    hours = rng.choice(np.arange(7, 24), size=n, p=np.array(
        [0.03,0.04,0.05,0.07,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.07,0.06,0.05,0.04,0.02,0.01]
    ) / np.sum([0.03,0.04,0.05,0.07,0.08,0.08,0.08,0.08,0.08,0.08,0.08,0.07,0.06,0.05,0.04,0.02,0.01]))
    dates = dates + pd.to_timedelta(hours, unit="h")
    platforms = rng.choice(["Instagram", "Facebook", "LinkedIn", "X"], n, p=[0.36, 0.27, 0.22, 0.15])
    content_types = rng.choice(["Image", "Video", "Text", "Carousel", "Reel"], n, p=[0.27,0.22,0.16,0.17,0.18])
    platform_multiplier = pd.Series(platforms).map({"Instagram":1.25,"Facebook":0.9,"LinkedIn":1.05,"X":0.72}).to_numpy()
    type_multiplier = pd.Series(content_types).map({"Image":1.0,"Video":1.25,"Text":0.72,"Carousel":1.18,"Reel":1.38}).to_numpy()
    weekend = np.isin(dates.dayofweek, [5,6])
    impressions = np.maximum(100, rng.lognormal(mean=7.2, sigma=0.7, size=n) * platform_multiplier)
    impressions *= np.where(weekend, 1.08, 1.0)
    impressions = impressions.astype(int)
    engagement_rate = rng.beta(2.2, 35, size=n) * type_multiplier
    likes = rng.binomial(np.maximum(impressions, 1), np.clip(engagement_rate * 0.72, 0, 0.2))
    comments = rng.binomial(np.maximum(impressions, 1), np.clip(engagement_rate * 0.18, 0, 0.1))
    shares = rng.binomial(np.maximum(impressions, 1), np.clip(engagement_rate * 0.10, 0, 0.1))
    reach = np.maximum(1, (impressions * rng.uniform(0.55, 0.92, size=n))).astype(int)
    topic_pool = ["AI", "technology", "marketing", "career", "travel", "fitness", "education", "design"]
    hashtags = [" ".join("#" + x for x in rng.choice(topic_pool, size=int(rng.integers(1,4)), replace=False)) for _ in range(n)]
    captions = rng.choice([
        "A few lessons learned this week.",
        "Behind the scenes of our latest project.",
        "What do you think about this idea?",
        "Here are three practical tips to try.",
        "Sharing a small milestone with the community.",
        "A quick guide to a common challenge."
    ], n)
    df = pd.DataFrame({
        "post_id": [f"POST-{i+1:05d}" for i in range(n)],
        "platform": platforms,
        "post_date": dates,
        "content_type": content_types,
        "caption": captions,
        "hashtags": hashtags,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "impressions": impressions,
        "reach": reach,
        "views": np.where(np.isin(content_types, ["Video", "Reel"]), (impressions*rng.uniform(.45,1.1,n)).astype(int), np.nan)
    })
    out = Path("data")
    out.mkdir(exist_ok=True)
    df.to_csv(out / "social_media_posts.csv", index=False)
    print(f"Created {out / 'social_media_posts.csv'} with {len(df)} synthetic rows.")

if __name__ == "__main__":
    main()
