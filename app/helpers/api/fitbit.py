import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from helpers.constants import *


def get_heart_rate_history(access_token: str, days: int = 30):
    # Get some data
    endpoint = f'https://api.fitbit.com/1/user/-/activities/heart/date/today/{days}d.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()


def get_heart_rate_detailed(access_token: str, day: datetime = None, detail: str = '1min'):
    if day is None:
        day = datetime.now() - timedelta(days=1)

    yesterday = datetime.strftime(day, '%Y-%m-%d')

    # Get some data
    endpoint = f'https://api.fitbit.com/1/user/-/activities/heart/date/{yesterday}/1d/{detail}.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(endpoint, headers=headers).json()
    dataset = response[FITBIT_API_KEY_HR_INTRADAY][FITBIT_API_KEY_INTRADAY_DATASET]

    # Create a dataframe from the heartrate data so we can use other pandas features
    df = pd.DataFrame(
        {
            'hr': list(map(lambda w: w[FITBIT_API_KEY_INTRADAY_VALUE], dataset))
        },
        index=list(map(lambda x: datetime.strptime(f'{yesterday}T{x[FITBIT_API_KEY_INTRADAY_TIME]}Z', UTC_DATE_FORMAT), dataset))
    )

    start = datetime.strptime(f'{yesterday}T00:00:00Z', UTC_DATE_FORMAT)

    # If the detail level is 1 second then we will interpolate across 20 sec to allow for intermittent results
    if detail == '1sec':
        end = datetime.strptime(f'{yesterday}T23:59:59Z', UTC_DATE_FORMAT)
        new_index = pd.Index(np.arange(start, end, timedelta(seconds=1)))
        return df.reindex(new_index).interpolate(limit=20)
    else:
        end = datetime.strptime(f'{yesterday}T23:59:00Z', UTC_DATE_FORMAT)
        new_index = pd.Index(np.arange(start, end, timedelta(minutes=1)))
        return df.reindex(new_index)


def get_sleep_history(access_token: str, end: datetime = None, duration: int = 30):
    if end is None:
        end = datetime.now()

    end_string = datetime.strftime(end, '%Y-%m-%d')
    start = datetime.strftime(end - timedelta(days=duration), '%Y-%m-%d')

    # Get some data
    endpoint = f'https://api.fitbit.com/1.2/user/-/sleep/date/{start}/{end_string}.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()

def get_weight(access_token: str, weight_day: datetime):

    interpolation_window = 30

    # Get weight for the date specified and the month afterwards
    weight_day_formatted = datetime.strftime(weight_day, '%Y-%m-%d')

    endpoint = f'https://api.fitbit.com/1/user/-/body/log/weight/date/{weight_day_formatted}/{interpolation_window}d.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    month_before = requests.get(endpoint, headers=headers).json()

    df_before = pd.DataFrame(
        {
            'fat': list(map(lambda w: w.get('fat', None), month_before['weight'])),
            'weight': list(map(lambda w: w.get('weight', None), month_before['weight']))
        },
        index=list(map(lambda w: datetime.strptime(w['date'], '%Y-%m-%d'), month_before['weight']))
    )

    # Get the data for the preceeding month
    month_before_day_formatted = datetime.strftime(weight_day + timedelta(days=interpolation_window), '%Y-%m-%d')
    endpoint = f'https://api.fitbit.com/1/user/-/body/log/weight/date/{month_before_day_formatted}/{interpolation_window}d.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    month_after = requests.get(endpoint, headers=headers).json()

    df_after = pd.DataFrame(
        {
            'fat': list(map(lambda w: w.get('fat', None), month_after['weight'])),
            'weight': list(map(lambda w: w.get('weight', None), month_after['weight']))
        },
        index=list(map(lambda w: datetime.strptime(w['date'], '%Y-%m-%d'), month_after['weight']))
    )

    # Check whether the date we're asking for happens to be one of the dates we have a weight for
    if weight_day in df_before.index:
        exact_match = df_before.loc[weight_day]
        return {
            'type': 'exact-match',
            'fat': exact_match['fat'],
            'weight': exact_match['weight']
        }
    # If we have data before and none after the date in question then just use the last match
    elif len(df_before.index) > 0 and len(df_after.index) == 0:
        closest_match = df_before.iloc[-1]
        return {
            'type': 'closest-match-recent',
            'fat': closest_match['fat'],
            'weight': closest_match['weight']
        }
    # If we have data after and none before the date in question then just use the last match
    elif len(df_before.index) == 0 and len(df_after.index) > 0:
        closest_match = df_after.iloc[0]
        return {
            'type': 'closest-match-future',
            'fat': closest_match['fat'],
            'weight': closest_match['weight']
        }
    # If we have data before and after then interpolate
    elif len(df_before.index) > 0 and len(df_after.index) > 0:
        # Append the the day in question and interpolate the dataframe
        df = df_before.append(df_after).append(pd.DataFrame([{'fat': None, 'weight': None}], index=[weight_day])).sort_index().interpolate()
        closest_match = df.loc[weight_day]
        return {
            'type': 'interpolation',
            'fat': closest_match['fat'],
            'weight': closest_match['weight']
        }
    else:
        return {
            'type': 'insufficient-data',
            'fat': None,
            'weight': None
        }


def get_device_information(access_token: str):
    # Get some data
    endpoint = 'https://api.fitbit.com/1/user/-/devices.json'
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()