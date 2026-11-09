"""Load the selected GitHub dataset, downloading it when it is not already present."""
from pathlib import Path
import urllib.request

DATASET_URL = (
    "https://raw.githubusercontent.com/abhishek07ma/"
    "Social_Media_Engagement_Dashboard/main/Social_Media_Engagement.csv"
)
DEFAULT_DATASET = Path("data/Social_Media_Engagement.csv")

def ensure_dataset(path: Path = DEFAULT_DATASET) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print("Dataset not found locally. Downloading the GitHub CSV...")
    try:
        request = urllib.request.Request(
            DATASET_URL,
            headers={"User-Agent": "SocialMediaEngagementAnalytics/1.0"}
        )
        with urllib.request.urlopen(request, timeout=45) as response, open(path, "wb") as out:
            out.write(response.read())
    except Exception as exc:
        if path.exists():
            path.unlink()
        raise RuntimeError(
            "Could not download the dataset. Check your internet connection, or download "
            "Social_Media_Engagement.csv from the GitHub repository and save it to "
            f"{path.resolve()}. Source: {DATASET_URL}"
        ) from exc
    return path
