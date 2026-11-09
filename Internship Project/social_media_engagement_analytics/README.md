# Social Media Engagement Analytics

A runnable Python analytics project for exploring social media post performance, producing charts and Power BI-ready CSVs, and optionally training a high-engagement classifier.

## Features
- Load your own CSV or generate a synthetic example dataset
- Normalize common column names
- Clean data and handle missing values
- Calculate total engagement and engagement rate
- Analyze platform, content type, posting day/hour, hashtags, and trends
- Export cleaned data and summary tables for Power BI
- Train and evaluate a Random Forest classifier without target leakage
- Streamlit dashboard for interactive exploration

## 1. Setup
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2. Dataset
By default, the project uses the public CSV from:
https://github.com/abhishek07ma/Social_Media_Engagement_Dashboard

On first run, `dataset_source.py` downloads `Social_Media_Engagement.csv` into `data/` automatically. This requires an internet connection. If automatic download fails, download the CSV from the repository and place it at `data/Social_Media_Engagement.csv`.

The loader maps `Post ID`, `Post Type`, `Post Timestamp`, and `Post Content` to the normalized project columns. The dataset also includes sentiment and audience attributes.

To use synthetic test data instead:
```bash
python generate_sample_data.py
python main.py --input data/social_media_posts.csv
```

## 3. Run the analysis
```bash
python main.py
```
Optional custom CSV:
```bash
python main.py --input path/to/your_posts.csv --output outputs
```

## 4. Run the interactive dashboard
```bash
streamlit run app.py
```
Upload your CSV in the sidebar or use the sample CSV.

## Expected input columns
The project recognizes common variants of:
- `post_id`
- `platform`
- `post_date` (date/time of publishing)
- `content_type` (image, video, text, carousel, reel, etc.)
- `likes`, `comments`, `shares`
- `impressions` (recommended for engagement rate)
- `reach`, `views`, `caption`, `hashtags`

Minimum useful columns: likes, comments, shares. If impressions are missing, engagement rate is left blank rather than fabricated.

## Outputs
The `outputs/` directory contains:
- `cleaned_posts.csv`
- `platform_summary.csv`
- `content_type_summary.csv`
- `day_summary.csv`
- `hour_summary.csv`
- `hashtag_summary.csv`
- `monthly_summary.csv`
- `model_metrics.json` (if model can be trained)
- `charts/*.png`

Import summary CSV files into Power BI to create interactive report pages.

## Dataset attribution
Dataset source: [Social Media Engagement Dashboard repository](https://github.com/abhishek07ma/Social_Media_Engagement_Dashboard). Review the source repository's license and attribution terms before redistributing the dataset separately.

## Important interpretation notes
- Engagement is defined here as likes + comments + shares.
- Engagement rate by impressions = engagement / impressions * 100.
- Platform metrics are not always defined identically; compare only when definitions are compatible.
- The classifier labels the top 25% of posts by engagement as “high engagement” for this dataset. This is a relative label, not a universal industry benchmark.
- Predictive features exclude likes/comments/shares and other post-publication outcome metrics to reduce leakage. This is an observational project, not proof that a posting time or hashtag causes engagement.
- Hashtag analysis uses hashtags already present in the CSV. It does not fetch live platform data.
