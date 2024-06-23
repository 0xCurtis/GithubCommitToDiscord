import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
PREVIOUS_DAYS = 6
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_commit_count(github_user):
    now = datetime.utcnow()
    start_time = now - timedelta(days=PREVIOUS_DAYS)
    
    total_commit_count = 0

    # Get the user's repos
    repos_url = f'https://api.github.com/users/{github_user}/repos'
    repos_response = requests.get(repos_url, headers=HEADERS)
    repos = repos_response.json()

    for repo in repos:
        repo_name = repo['name']
        owner = repo['owner']['login']
        commit_activity_url = f'https://api.github.com/repos/{owner}/{repo_name}/stats/commit_activity'
        
        commit_activity_response = requests.get(commit_activity_url, headers=HEADERS)
        commit_activity = commit_activity_response.json()
        
        for week in commit_activity:
            week_start = datetime.utcfromtimestamp(week['week'])
            if week_start > start_time:
                total_commit_count += week['total']

    return total_commit_count

def get_commit_counts_for_users(users):
    counts = {}
    for github_user, discord_user in users.items():
        counts[discord_user] = get_commit_count(github_user)
    return counts

def send_discord_message(commit_counts):
    sorted_counts = sorted(commit_counts.items(), key=lambda x: x[1], reverse=True)
    description = "\n".join([f"{discord_user}: {count} commits" for discord_user, count in sorted_counts])

    embed = {
        "title": f"GitHub Commit Counts (Last {PREVIOUS_DAYS} days)",
        "description": description,
        "color": 5814783
    }

    data = {
        "embeds": [embed]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")

users_to_monitor = {'0xCurtis': "@0xCurtis"}
commit_counts = get_commit_counts_for_users(users_to_monitor)
send_discord_message(commit_counts)
