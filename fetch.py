import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
headers = {
    'Authorization': GITHUB_TOKEN
}

def fetch_github_contributions_for_user(username, token=GITHUB_TOKEN, today=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), max_retries=3):
    headers = {
        'Authorization': f'Bearer {token}'
    }

    query = """
    query($username: String!, $today: DateTime!) {
      user(login: $username) {
        login
        contributionsCollection(to: $today) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
          commitContributionsByRepository(maxRepositories: 1) {
            contributions(first: 1) {
              nodes {
                occurredAt
              }
            }
          }
        }
      }
    }
    """

    variables = {
        'username': username,
        'today': today + "T23:59:59Z"
    }

    url = 'https://api.github.com/graphql'
    
    for attempt in range(max_retries):
        response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['user'] is not None:
                user = data['data']['user']
                contributionsCollection = user.get('contributionsCollection')
                total_contributions_today = 0
                last_commit_date = None
                last_commit_hour = None

                if contributionsCollection and 'contributionCalendar' in contributionsCollection:
                    contributions = contributionsCollection['contributionCalendar']['weeks']
                    for week in contributions:
                        for day in week['contributionDays']:
                            if day['contributionCount'] > 0:
                                last_commit_date = day['date']
                            if day['date'].startswith(today):
                                total_contributions_today += day['contributionCount']

                commit_contributions = contributionsCollection.get('commitContributionsByRepository') if contributionsCollection else None
                if commit_contributions:
                    last_commit_node = commit_contributions[0]['contributions']['nodes'][0] if commit_contributions[0]['contributions']['nodes'] else None
                    if last_commit_node:
                        last_commit_date_time = last_commit_node['occurredAt']
                        last_commit_hour = datetime.strptime(last_commit_date_time, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')

                return user['login'], total_contributions_today, last_commit_date, last_commit_hour
            else:
                print(f"Unexpected response format or no data for user {username}: {data}")
                return username, 0, None, None
        else:
            print(f"Attempt {attempt + 1} failed to fetch data for {username}: {response.status_code}, Response: {response.content}")

    print(f"All attempts failed for {username}.")
    return username, 0, None, None

def fetch_github_contributions_for_multiple_users(usernames, token):
    today = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    contributions_dict = {}
    last_commit_dict = {}
    for username in usernames:
        login, contributions, last_commit_date, last_commit_hour = fetch_github_contributions_for_user(username, token, today)
        contributions_dict[login] = contributions
        last_commit_dict[login] = (last_commit_date, last_commit_hour)
    return contributions_dict, last_commit_dict


def get_daily_leaderboard(users):
    github_usernames = list(users.keys())
    print(github_usernames)
    leaderboard = fetch_github_contributions_for_multiple_users(github_usernames, GITHUB_TOKEN)
    return leaderboard


if __name__ == '__main__':
    users_to_monitor = {'0xCurtis': "@0xCurtis", 'Delioos': "@delioos", 'leoleducq': "@iziatask", "Rayanworkout": "@Rayanworkout"}

    leaderboard_commit = get_daily_leaderboard(users_to_monitor)
    print(leaderboard_commit)
