import requests
import pandas as pd
import numpy as np


def get_strava_activities(access_token: str):
    endpoint = 'https://www.strava.com/api/v3/athlete/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()


def get_strava_activity_stream(access_token: str, activity_id: str):
    endpoint = f'https://www.strava.com/api/v3/activities/{activity_id}/streams?keys=watts,heartrate,time'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()


def get_strava_activity(access_token: str, activity_id: str):
    endpoint = f'https://www.strava.com/api/v3/activities/{activity_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()


def get_strava_athlete(access_token: str):
    endpoint = 'https://www.strava.com/api/v3/athlete'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()


def get_cycling_data_frame(cycling_activity_stream):
    time = list(filter(lambda f: f['type'] == 'time', cycling_activity_stream))
    power = list(filter(lambda f: f['type'] == 'watts', cycling_activity_stream))
    hr = list(filter(lambda f: f['type'] == 'heartrate', cycling_activity_stream))
    empty = [None] * len(time[0]['data'])

    data = {
        'time': time[0]['data'] if len(time) > 0 else empty,
        'power': power[0]['data'] if len(power) > 0 else empty,
        'hr': hr[0]['data'] if len(hr) > 0 else empty
    }

    headers = ['time', 'power', 'hr']

    df = pd.DataFrame(data, columns=headers)

    return df


def get_cycling_power_summary(cycling_activity_stream, ftp):
    # See this article for the maths:
    # https://medium.com/critical-powers/formulas-from-training-and-racing-with-a-power-meter-2a295c661b46

    df = get_cycling_data_frame(cycling_activity_stream)

    # Get the time for each row in the dataframe
    # TODO Assume 1 second for now
    time_interval = 1

    thirty_second_row_count = int(30 / time_interval)

    df['thirty'] = df.power.rolling(window=thirty_second_row_count).mean()
    df['pow4'] = df['thirty']**4

    max_pow = df['pow4'].mean()
    normalised_power = max_pow**0.25
    intensity_factor = normalised_power / ftp
    duration_seconds = df['time'].max()
    tss = (duration_seconds * normalised_power * intensity_factor) / (ftp * 36)

    return {
        'normalised_power': normalised_power,
        'intensity_factor': intensity_factor,
        'tss': tss,
    }

def get_cycling_activity_power_stats(cycling_activity_stream):
    df = get_cycling_data_frame(cycling_activity_stream)

    # Get the time for each row in the dataframe
    # TODO Assume 1 second for now
    time_interval = 1

    twenty_minute_row_count = int((20 * 60) / time_interval)
    ten_minute_row_count = int((10 * 60) / time_interval)
    five_minute_row_count = int((5 * 60) / time_interval)
    one_minute_row_count = int(60 / time_interval)
    thirty_second_row_count = int(30 / time_interval)
    five_second_row_count = int(5 / time_interval)
    one_second_row_count = int(1 / time_interval)

    return {
        'twenty_minute': df.power.rolling(window=twenty_minute_row_count).mean().max(),
        'ten_minute': df.power.rolling(window=ten_minute_row_count).mean().max(),
        'five_minute': df.power.rolling(window=five_minute_row_count).mean().max(),
        'one_minute': df.power.rolling(window=one_minute_row_count).mean().max(),
        'thirty_second': df.power.rolling(window=thirty_second_row_count).mean().max(),
        'five_second': df.power.rolling(window=five_second_row_count).mean().max(),
        'one_second': df.power.rolling(window=one_second_row_count).mean().max(),
    }


def get_cycling_power_splits(cycling_activity_stream, levels=4):
    df = get_cycling_data_frame(cycling_activity_stream)
    output = list()

    split_count = 1
    for level in range(levels):
        splits = get_cycling_power_split(df, split_count)
        output.append({
            'split_count': split_count,
            'splits': splits
        })
        split_count = split_count * 2
    return output


def get_cycling_power_split(df, split_count):
    splits = np.array_split(df, split_count)

    return list(map(lambda d: d['power'].mean(), splits))
