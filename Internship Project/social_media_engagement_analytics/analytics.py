"""Reusable cleaning, feature engineering, summaries, and model functions."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd

ALIASES = {
    "post_id": ["post_id", "id", "postid", "post"],
    "platform": ["platform", "social_platform", "network", "channel"],
    "post_date": ["post_date", "post_timestamp", "date", "published_at", "publish_date", "created_at", "datetime", "timestamp"],
    "content_type": ["content_type", "post_type", "media_type", "format", "type"],
    "likes": ["likes", "like_count", "num_likes"],
    "comments": ["comments", "comment_count", "num_comments"],
    "shares": ["shares", "share_count", "num_shares", "reposts", "retweets"],
    "impressions": ["impressions", "impression_count"],
    "reach": ["reach", "accounts_reached"],
    "views": ["views", "video_views", "view_count", "plays"],
    "source_engagement_rate": ["source_engagement_rate", "engagement_rate"],
    "sentiment": ["sentiment", "post_sentiment"],
    "audience_age": ["audience_age", "age"],
    "audience_gender": ["audience_gender", "gender"],
    "audience_location": ["audience_location", "location", "country"],
    "audience_interests": ["audience_interests", "interests", "interest"],
    "campaign_id": ["campaign_id", "campaign"],
    "influencer_id": ["influencer_id"],
    "caption": ["caption", "post_content", "text", "post_text", "message", "content"],
    "hashtags": ["hashtags", "hash_tags", "tags"],
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    lookup = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    rename = {}
    for canonical, candidates in ALIASES.items():
        for candidate in candidates:
            if candidate in lookup:
                rename[lookup[candidate]] = canonical
                break
    return df.rename(columns=rename)

def load_and_clean(source) -> pd.DataFrame:
    df = pd.read_csv(source) if not isinstance(source, pd.DataFrame) else source.copy()
    df = normalize_columns(df)
    required_counts = ["likes", "comments", "shares"]
    missing = [c for c in required_counts if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required engagement columns: " + ", ".join(missing) +
            ". Please provide likes, comments, and shares (or recognized equivalents)."
        )
    if "post_id" not in df.columns:
        df["post_id"] = [f"ROW-{i+1:06d}" for i in range(len(df))]
    if "platform" not in df.columns:
        df["platform"] = "Unknown"
    if "content_type" not in df.columns:
        df["content_type"] = "Unknown"
    if "post_date" not in df.columns:
        df["post_date"] = pd.NaT
    df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce", utc=True).dt.tz_convert(None)
    for col in ["likes", "comments", "shares", "impressions", "reach", "views"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].clip(lower=0)
    for col in required_counts:
        df[col] = df[col].fillna(0)
    for col in ["platform", "content_type"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    for col in ["caption", "hashtags"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    df = df.drop_duplicates(subset=["post_id"], keep="first").reset_index(drop=True)
    df["total_engagement"] = df[["likes", "comments", "shares"]].sum(axis=1)
    if "impressions" in df.columns:
        df["engagement_rate_pct"] = np.where(
            df["impressions"] > 0,
            df["total_engagement"] / df["impressions"] * 100,
            np.nan
        )
    else:
        df["engagement_rate_pct"] = np.nan
    if "post_date" in df.columns:
        df["post_day"] = df["post_date"].dt.day_name()
        df["post_hour"] = df["post_date"].dt.hour
        df["post_month"] = df["post_date"].dt.to_period("M").astype(str)
        df["post_date_only"] = df["post_date"].dt.date.astype("string")
    else:
        df["post_day"], df["post_hour"], df["post_month"], df["post_date_only"] = "Unknown", np.nan, "Unknown", ""
    df["caption_length"] = df["caption"].str.len()
    df["hashtag_count"] = df["hashtags"].apply(lambda x: len(re.findall(r"(?<!\w)#\w+", x)))
    return df

def _safe_group(df, column):
    if column not in df.columns:
        return pd.DataFrame()
    grouped = df.groupby(column, dropna=False).agg(
        post_count=("post_id", "count"),
        avg_engagement=("total_engagement", "mean"),
        median_engagement=("total_engagement", "median"),
        total_engagement=("total_engagement", "sum"),
        avg_likes=("likes", "mean"),
        avg_comments=("comments", "mean"),
        avg_shares=("shares", "mean"),
        avg_engagement_rate_pct=("engagement_rate_pct", "mean"),
    ).reset_index()
    return grouped.sort_values("avg_engagement", ascending=False)

def create_summaries(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    summaries = {
        "platform_summary": _safe_group(df, "platform"),
        "content_type_summary": _safe_group(df, "content_type"),
        "day_summary": _safe_group(df, "post_day"),
        "hour_summary": _safe_group(df, "post_hour"),
        "monthly_summary": _safe_group(df, "post_month"),
        "sentiment_summary": _safe_group(df, "sentiment") if "sentiment" in df.columns else pd.DataFrame(),
        "audience_gender_summary": _safe_group(df, "audience_gender") if "audience_gender" in df.columns else pd.DataFrame(),
        "audience_location_summary": _safe_group(df, "audience_location") if "audience_location" in df.columns else pd.DataFrame(),
    }
    tag_rows = []
    for _, row in df[["hashtags", "total_engagement", "engagement_rate_pct"]].iterrows():
        tags = set(re.findall(r"(?<!\w)#([A-Za-z0-9_]+)", str(row["hashtags"])))
        for tag in tags:
            tag_rows.append((tag.lower(), row["total_engagement"], row["engagement_rate_pct"]))
    if tag_rows:
        tag_df = pd.DataFrame(tag_rows, columns=["hashtag", "total_engagement", "engagement_rate_pct"])
        summaries["hashtag_summary"] = tag_df.groupby("hashtag").agg(
            post_count=("hashtag", "count"),
            avg_engagement=("total_engagement", "mean"),
            median_engagement=("total_engagement", "median"),
            avg_engagement_rate_pct=("engagement_rate_pct", "mean"),
        ).reset_index().sort_values(["post_count", "avg_engagement"], ascending=False)
    else:
        summaries["hashtag_summary"] = pd.DataFrame(columns=[
            "hashtag", "post_count", "avg_engagement", "median_engagement", "avg_engagement_rate_pct"
        ])
    return summaries

def model_high_engagement(df: pd.DataFrame, output_dir: Path) -> dict:
    """Train a leakage-aware classifier using metadata, not engagement outcome counts."""
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
    import joblib

    if len(df) < 40 or df["total_engagement"].nunique() < 2:
        return {"status": "skipped", "reason": "Need at least 40 rows and variation in engagement to train a meaningful model."}
    work = df.copy()
    threshold = work["total_engagement"].quantile(0.75)
    work["high_engagement"] = (work["total_engagement"] >= threshold).astype(int)
    work["post_hour_model"] = work["post_hour"]
    work["post_day_model"] = work["post_day"]
    work["month_num"] = work["post_date"].dt.month if "post_date" in work else np.nan
    features = ["platform", "content_type", "caption_length", "hashtag_count", "post_hour_model", "post_day_model", "month_num"]
    X = work[features]
    y = work["high_engagement"]
    if y.nunique() < 2:
        return {"status": "skipped", "reason": "Target contains only one class."}
    categorical = ["platform", "content_type", "post_day_model"]
    numeric = ["caption_length", "hashtag_count", "post_hour_model", "month_num"]
    preprocessor = ColumnTransformer([
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                                  ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")),
                              ("scale", StandardScaler())]), numeric)
    ])
    model = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=250, random_state=42, class_weight="balanced"))
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "status": "trained",
        "target_definition": "Top quartile of total engagement within this dataset",
        "engagement_threshold": float(threshold),
        "test_rows": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)) if y_test.nunique() > 1 else None,
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "features": features,
        "warning": "Exploratory baseline only. Results depend on dataset size, sampling, and platform mix."
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / "high_engagement_model.joblib")
    return metrics
