import requests
from logger import logger

def get_estimated_indexing_time(github_url: str) -> int:
    """
    Fetches repo size from GitHub and calculates an estimated indexing time.
    Returns the time in seconds.
    """
    try:
        clean_url = github_url.rstrip('/')
        parts = clean_url.split('/')
        owner, repo = parts[-2], parts[-1]

        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}", 
            timeout=3
        )

        if response.status_code == 200:
            repo_data = response.json()
            size_kb = repo_data.get("size", 0)

            estimated_seconds = int(20 + (size_kb * 0.01))
            return max(15, min(estimated_seconds, 600))
    except Exception as e:
        logger.warning(f"Failed to fetch GitHub repo size for ETA: {e}")
    
    return 45