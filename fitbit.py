import requests
from datetime import datetime, timedelta


def get_heart_rate_history(access_token: str, days: int = 30):
    # Get some data
    endpoint = f'https://api.fitbit.com/1/user/-/activities/heart/date/today/{days}d.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()


def get_heart_rate_detailed(access_token: str, day: datetime = None):
    if day is None:
        day = datetime.now() - timedelta(days=1)

    yesterday = datetime.strftime(day, '%Y-%m-%d')

    # Get some data
    endpoint = f'https://api.fitbit.com/1/user/-/activities/heart/date/{yesterday}/1d/1min.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()


def get_sleep_history(access_token: str, end: datetime = None, duration: int = 30):
    if end is None:
        end = datetime.strftime(datetime.now(), '%Y-%m-%d')
    start = datetime.strftime(datetime.now() - timedelta(days=duration), '%Y-%m-%d')

    # Get some data
    endpoint = f'https://api.fitbit.com/1.2/user/-/sleep/date/{start}/{end}.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()
