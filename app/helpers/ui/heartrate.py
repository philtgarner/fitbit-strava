from datetime import datetime, timedelta
import dash_core_components as dcc
import helpers.constants as constants
from helpers.constants import *


def get_detailed_heart_rate_graph(heart_rate_details):
    start_date = heart_rate_details[FITBIT_API_KEY_HR_ACTIVITY][0][FITBIT_API_KEY_DATETIME]
    dates = list(map(lambda x: datetime.strptime(f'{start_date}T{x[FITBIT_API_KEY_INTRADAY_TIME]}Z', UTC_DATE_FORMAT), heart_rate_details[FITBIT_API_KEY_HR_INTRADAY][FITBIT_API_KEY_INTRADAY_DATASET]))
    detailed_hr = list(map(lambda x: x[FITBIT_API_KEY_INTRADAY_VALUE], heart_rate_details[FITBIT_API_KEY_HR_INTRADAY][FITBIT_API_KEY_INTRADAY_DATASET]))

    return dcc.Graph(
        id='detailed-hr',
        figure={
            'data': [
                {
                    'x': dates,
                    'y': detailed_hr,
                    'name': 'Resting heart rate',
                    'mode': 'line',
                    'line': {'color': constants.COLOUR_RED}
                }
            ]
        }
    )


def get_resting_heart_rate_graph(heart_rate_history):
    dates = list(map(lambda x: x[FITBIT_API_KEY_DATETIME], heart_rate_history[FITBIT_API_KEY_HR_ACTIVITY]))

    # TODO Handle things if there is no resting heart rate for the day (probably caused by not syncing yet?)
    resting_hr = list(map(lambda x: x['value'].get('restingHeartRate', None), heart_rate_history[FITBIT_API_KEY_HR_ACTIVITY]))

    return dcc.Graph(
        id='resting-hr',
        figure={
            'data': [
                {
                    'x': dates,
                    'y': resting_hr,
                    'name': 'Resting heart rate',
                    'mode': 'line',
                    'line': {'color': constants.COLOUR_RED}
                }
            ]
        }
    )


def get_heartrate_recovery(cycling_activity_stream, day_heartrate, activity_start: datetime):
    activity_start_date_string = activity_start.strftime(DATE_ONLY)
    day_dates = list(map(lambda x: datetime.strptime(f'{activity_start_date_string}T{x["time"]}Z', UTC_DATE_FORMAT), day_heartrate['activities-heart-intraday']['dataset']))
    day_hr = list(map(lambda x: x['value'], day_heartrate['activities-heart-intraday']['dataset']))

    activity_dates = list(filter(lambda f: f[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_API_KEY_DATA_STREAM_TIME, cycling_activity_stream))
    activity_hr = list(filter(lambda f: f[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_API_KEY_DATA_STREAM_HEARTRATE, cycling_activity_stream))

    # Create an empty array of the right same length (we assume we always get time)
    # This will be used if we're missing power and/or HR data
    empty = [None] * len(activity_dates[0][STRAVA_API_KEY_DATA_STREAM_DATA])

    activity_dates = list(map(lambda t: (activity_start + timedelta(seconds=t)), activity_dates[0][STRAVA_API_KEY_DATA_STREAM_DATA]))
    activity_hr = list(map(lambda h: h if h > 0 else None, activity_hr[0][STRAVA_API_KEY_DATA_STREAM_DATA])) if len(activity_hr) > 0 else empty

    return dcc.Graph(
        id='detailed-hr',
        figure={
            'data': [
                {
                    'x': day_dates,
                    'y': day_hr,
                    'name': 'Fitbit heartrate',
                    'mode': 'line',
                    'line': {'color': constants.COLOUR_FITBIT_BLUE}
                },
                {
                    'x': activity_dates,
                    'y': activity_hr,
                    'name': 'Strava heartrate',
                    'mode': 'line',
                    'line': {'color': constants.COLOUR_STRAVA_ORANGE}
                }
            ]
        }
    )


