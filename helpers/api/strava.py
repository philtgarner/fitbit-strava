import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def get_strava_activities(access_token: str):
    endpoint = 'https://www.strava.com/api/v3/athlete/activities'
    headers = {'Authorization': f'Bearer {access_token}'}
    return requests.get(endpoint, headers=headers).json()


def get_strava_activity_stream(access_token: str, activity_id: str):
    endpoint = f'https://www.strava.com/api/v3/activities/{activity_id}/streams?keys=watts,heartrate,time,distance,altitude,grade_smooth'
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
    distance = list(filter(lambda f: f['type'] == 'distance', cycling_activity_stream))
    altitude = list(filter(lambda f: f['type'] == 'altitude', cycling_activity_stream))
    grade = list(filter(lambda f: f['type'] == 'grade_smooth', cycling_activity_stream))
    empty = [None] * len(time[0]['data'])

    data = {
        'time': time[0]['data'] if len(time) > 0 else empty,
        'power': power[0]['data'] if len(power) > 0 else empty,
        'hr': hr[0]['data'] if len(hr) > 0 else empty,
        'distance': distance[0]['data'] if len(distance) > 0 else empty,
        'altitude': altitude[0]['data'] if len(altitude) > 0 else empty,
        'grade': grade[0]['data'] if len(grade) > 0 else empty
    }

    headers = ['time', 'power', 'hr', 'distance', 'altitude', 'grade']

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

    return list(map(lambda d: d['power'].mean() if not np.isnan(d['power'].mean()) else None, splits))


def get_cycling_gradient_splits(cycling_activity_stream, rolling_window=10):
    df = get_cycling_data_frame(cycling_activity_stream)

    # Get the median gradient over a rolling window (an attempt to smooth things out a bit)
    df['grade_rolling'] = df['grade'].rolling(window=rolling_window).median()

    # Round the gradients to the nearest integer to group things together
    df['grade_round'] = df['grade_rolling'].round()

    # Group by the rounded gradient and perform some aggregations
    mean = df.groupby('grade_round').mean()
    max = df.groupby('grade_round').max()
    count = df.groupby('grade_round').count()

    # Re-index to add any missing gradients
    new_index = pd.Index(np.arange(df['grade_round'].min(), df['grade_round'].max(), 1), name='grade_index')
    mean_reindexed = mean.reindex(new_index)
    max_reindexed = max.reindex(new_index)
    count_reindexed = count.reindex(new_index)

    # Add suffixes to the column names to ensure they're all different (needed before we concatenate them all together)
    mean_reindexed = mean_reindexed.add_suffix('_mean')
    max_reindexed = max_reindexed.add_suffix('_max')
    count_reindexed = count_reindexed.add_suffix('_count')

    # Get the time for each row in the dataframe
    # TODO Assume 1 second for now
    time_interval = 1

    # Add a duration column
    count_reindexed['duration'] = count_reindexed.apply(lambda row: pd.Timedelta(seconds=0) if np.isnan(row['time_count']) else pd.Timedelta(seconds=row['time_count'] / time_interval), axis=1)

    # Concatenate the different aggregates together and pick out the meaningful columns
    return pd.concat([mean_reindexed, max_reindexed, count_reindexed], axis=1, join='inner').filter(['power_mean', 'power_max', 'hr_mean', 'hr_max', 'duration'])
