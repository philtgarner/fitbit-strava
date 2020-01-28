import requests


def get_strava_activities(access_token: str):
    endpoint = 'https://www.strava.com/api/v3/athlete/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()


def get_strava_activity_stream(access_token: str, activity_id: str):
    endpoint = f'https://www.strava.com/api/v3/activities/{activity_id}/streams?keys=watts,heartrate,time'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()
