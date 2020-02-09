
import dash_core_components as dcc
import helpers.constants as constants

def get_detailed_heart_rate_graph(heart_rate_details):
    dates = list(map(lambda x: x['time'], heart_rate_details['activities-heart-intraday']['dataset']))
    detailed_hr = list(map(lambda x: x['value'], heart_rate_details['activities-heart-intraday']['dataset']))

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
    dates = list(map(lambda x: x['dateTime'], heart_rate_history['activities-heart']))

    # TODO Handle things if there is no resting heart rate for the day (probably caused by not syncing yet?)
    resting_hr = list(map(lambda x: x['value'].get('restingHeartRate', None), heart_rate_history['activities-heart']))

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

