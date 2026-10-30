"""Record anonymous visibility, current remote head, and the board's live watch."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
headers = {'User-Agent': 'CodeScythe-access-check/1.0', 'Cache-Control': 'no-cache'}
result = {'fetched_at': datetime.now(timezone.utc).isoformat()}
url = 'https://api.github.com/repos/Kultzuki/speed-demon'
try:
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
        repo = json.load(response)
        result['anonymous_github_status'] = response.status
        result['private'] = repo.get('private')
except urllib.error.HTTPError as error:
    result['anonymous_github_status'] = error.code
result['remote_head'] = subprocess.check_output(
    ['git', 'ls-remote', 'origin', 'refs/heads/speed-demon'], cwd=ROOT, text=True).split()[0]
url = 'https://s3.amazonaws.com/raptors.dev/speeddemon.dev/2026/board/board.json?access-check=' + str(time.time_ns())
with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
    board = json.load(response)
team = next(item for item in board['teams'] if item.get('team', '').lower() == 'codescythe')
result['watch'] = team.get('watch')
result['queue'] = team.get('queue')
checked = datetime.fromisoformat(result['watch']['checked_at'].replace('Z', '+00:00'))
result['watch_age_s'] = (datetime.now(timezone.utc) - checked).total_seconds()
result['watch_matches_remote'] = result['watch'].get('head') == result['remote_head']
result['recent_successful_private_watch'] = (
    result.get('anonymous_github_status') == 404 and result['watch'].get('ok') is True
    and result['watch_matches_remote'] and 0 <= result['watch_age_s'] < 180)
result['scope'] = ('Anonymous 404 is consistent with the user-confirmed private visibility; '
                   'a fresh successful board watch at the same remote head verifies continued read access. '
                   'A scored new push additionally verifies private cloning/building.')
(ROOT / 'validation/private-repository-access.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
