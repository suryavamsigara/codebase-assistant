import re
import requests
from urllib.parse import urlparse
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

def sanitize_github_url(url: str) -> str:
    """
    Normalizes and validates a github URL
    - Strips whitespace
    - Ensures it uses https
    - Validates it is a github.com domain
    - Removes trailing .git or slashes
    """

    if not url:
        return None
    
    url = url.strip().lower()

    parsed = urlparse(url)

    if parsed.netloc not in ["github.com", "www.github.com"]:
        return None
    
    clean_path = parsed.path.rstrip('/')
    if clean_path.endswith('.git'):
        clean_path = clean_path[:-4]
    
    if not re.match(r'^/[a-z0-9\-_.]+/[a-z0-9\-_.]+$', clean_path):
        return None
    
    return f"https://github.com{clean_path}"
