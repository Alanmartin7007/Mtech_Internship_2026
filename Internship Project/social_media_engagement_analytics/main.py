"""Command-line entry point for Social Media Engagement Analytics."""
from pathlib import Path
import argparse
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from analytics import load_and_clean, create_summaries, model_high_engagement
from dataset_source import ensure_dataset, DEFAULT_DATASET

def save_charts(df, summaries, chart_dir: Path):
    chart_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme()

    def barplot(data, x, y, title, filename, rotate=25):
        if data.empty or x not in data or y not in data:
            return
        plot_data = data.dropna(subset=[x, y]).sort_values(y, ascending=False)
        if plot_data.empty:
            return
        plt.figure(figsize=(10, 5))
        sns.barplot(data=plot_data, x=x, y=y, color="C0")
        plt.title(title)
        plt.xlabel(x.replace("_", " ").title())
        plt.ylabel(y.replace("_", " ").title())
        plt.xticks(rotation=rotate, ha="right")
        plt.tight_layout()
        plt.savefig(chart_dir / filename, dpi=160)
        plt.close()

    barplot(summaries["platform_summary"], "platform", "avg_engagement",
            "Average Engagement by Platform", "engagement_by_platform.png")
    barplot(summaries["content_type_summary"], "content_type", "avg_engagement",
            "Average Engagement by Content Type", "engagement_by_content_type.png")
    barplot(summaries["day_summary"], "post_day", "avg_engagement",
            "Average Engagement by Day", "engagement_by_day.png")
    barplot(summaries["hour_summary"], "post_hour", "avg_engagement",
            "Average Engagement by Posting Hour", "engagement_by_hour.png", rotate=0)
    monthly = summaries["monthly_summary"].copy()
    if not monthly.empty:
        monthly["post_month"] = monthly["post_month"].astype(str)
        plt.figure(figsize=(11, 5))
        sns.lineplot(data=monthly.sort_values("post_month"), x="post_month", y="avg_engagement", marker="o")
        plt.title("Average Engagement Over Time")
        plt.xlabel("Month")
        plt.ylabel("Average Engagement")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(chart_dir / "monthly_engagement_trend.png", dpi=160)
        plt.close()

    if "post_hour" in df and "post_day" in df and df["post_date"].notna().any():
        pivot = df.pivot_table(index="post_day", columns="post_hour", values="total_engagement", aggfunc="mean")
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pivot = pivot.reindex([x for x in order if x in pivot.index])
        if not pivot.empty:
            plt.figure(figsize=(13, 5))
            sns.heatmap(pivot, cmap="YlGnBu", linewidths=.2)
            plt.title("Average Engagement by Day and Hour")
            plt.xlabel("Posting Hour (24-hour)")
            plt.ylabel("Day")
            plt.tight_layout()
            plt.savefig(chart_dir / "day_hour_heatmap.png", dpi=160)
            plt.close()

    if df["engagement_rate_pct"].notna().any():
        plt.figure(figsize=(9, 5))
        sns.histplot(df["engagement_rate_pct"].dropna().clip(upper=df["engagement_rate_pct"].quantile(.99)), bins=35, kde=True, color="C0")
        plt.title("Engagement Rate Distribution (capped at 99th percentile for readability)")
        plt.xlabel("Engagement Rate (%)")
        plt.tight_layout()
        plt.savefig(chart_dir / "engagement_rate_distribution.png", dpi=160)
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Analyze social media post engagement.")
    parser.add_argument("--input", default=str(DEFAULT_DATASET), help="Input CSV path (defaults to the selected GitHub dataset)")
    parser.add_argument("--output", default="outputs", help="Output directory")
    args = parser.parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    if not input_path.exists() and input_path.as_posix() == DEFAULT_DATASET.as_posix():
        try:
            input_path = ensure_dataset(input_path)
        except RuntimeError as exc:
            raise SystemExit(str(exc))
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}. Pass --input path/to/file.csv.")
    output_dir.mkdir(parents=True, exist_ok=True)
    df = load_and_clean(input_path)
    df.to_csv(output_dir / "cleaned_posts.csv", index=False)
    summaries = create_summaries(df)
    for name, summary in summaries.items():
        summary.to_csv(output_dir / f"{name}.csv", index=False)
    save_charts(df, summaries, output_dir / "charts")
    metrics = model_high_engagement(df, output_dir)
    with open(output_dir / "model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    report = {
        "rows_analyzed": int(len(df)),
        "unique_platforms": int(df["platform"].nunique()),
        "average_engagement": float(df["total_engagement"].mean()) if len(df) else 0,
        "median_engagement": float(df["total_engagement"].median()) if len(df) else 0,
        "engagement_rate_available_rows": int(df["engagement_rate_pct"].notna().sum()),
        "model_status": metrics.get("status", "unknown"),
    }
    with open(output_dir / "run_summary.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\nAnalysis completed.")
    print(json.dumps(report, indent=2))
    print(f"\nOutputs saved to: {output_dir.resolve()}")

if __name__ == "__main__":
    main()
