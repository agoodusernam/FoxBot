from typing import Any
import datetime
import cachetools.func

import requests

@cachetools.func.ttl_cache(maxsize=1, ttl=60*60)
def get_last_commit() -> None | tuple[int, str, dict[str, int]]:
    """
    Get the latest commit info from the FoxBot GitHub repository.
    Returns None if an error occurs.
    Else, it returns a tuple containing the commit timestamp, commit message, and change stats.
    """
    response: requests.Response = requests.get('https://api.github.com/repos/agoodusernam/FoxBot/commits/master', allow_redirects=True)
    
    if not response.ok:
        return None
    
    body: dict[str, Any] = response.json()
    commit = body['commit']
    message = commit['message']
    date = commit['author']['date']
    stats = body['stats']
    change_stats: dict[str, int] = {'additions': stats['additions'], 'deletions': stats['deletions'], 'total': stats['total']}
    return round(datetime.datetime.fromisoformat(date).timestamp()), message, change_stats

