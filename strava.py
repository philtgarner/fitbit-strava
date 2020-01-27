import requests

def getStravaActivities(access_token):
    endpoint = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()