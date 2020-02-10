import dash_core_components as dcc
import helpers.constants as constants
import dash_html_components as html


def get_sleep_history_graph(sleep_history):
    dates = list(map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_DATE], sleep_history[constants.FITBIT_API_KEY_SLEEP]))

    deep = list(map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_DEEP, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))
    light = list(
        map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_LIGHT, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))
    rem = list(map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_REM, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))
    wake = list(map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_WAKE, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))

    # Data from sleeps not long enough to be tracked with sleep stages
    awake = list(
        map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_AWAKE, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))
    asleep = list(
        map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_ASLEEP, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))
    restless = list(
        map(lambda x: x[constants.FITBIT_API_KEY_SLEEP_LEVELS][constants.FITBIT_API_KEY_SLEEP_SUMMARY].get(constants.FITBIT_API_KEY_SLEEP_RESTLESS, {constants.FITBIT_API_KEY_SLEEP_MINUTES: None})[constants.FITBIT_API_KEY_SLEEP_MINUTES], sleep_history[constants.FITBIT_API_KEY_SLEEP]))

    return dcc.Graph(
        id='sleep-history',
        figure={
            'data': [
                {
                    'x': dates,
                    'y': deep,
                    'name': 'Deep',
                    'type': 'bar'
                },
                {
                    'x': dates,
                    'y': light,
                    'name': 'Light',
                    'type': 'bar'
                },
                {
                    'x': dates,
                    'y': rem,
                    'name': 'REM',
                    'type': 'bar',
                },
                {
                    'x': dates,
                    'y': wake,
                    'name': 'Wake',
                    'type': 'bar'
                },
                {
                    'x': dates,
                    'y': asleep,
                    'name': 'Asleep (short sleep)',
                    'type': 'bar'
                },
                {
                    'x': dates,
                    'y': awake,
                    'name': 'Awake (short sleep)',
                    'type': 'bar'
                },
                {
                    'x': dates,
                    'y': restless,
                    'name': 'Restless (short sleep)',
                    'type': 'bar'
                }
            ],
            'layout': {
                'barmode': 'stack',
                'title': '30 day sleep record',
                'colorway': ['#154BA6', '#3F8DFF', '#7EC4FF', '#E73360', '#FF0000', '#00FF00', '#0000FF']
            }
        },
    )


def get_sleep_efficiency_graph(sleep_history):
    dates = list(map(lambda x: x['dateOfSleep'], sleep_history['sleep']))
    resting_hr = list(map(lambda x: x['efficiency'], sleep_history['sleep']))

    return dcc.Graph(
        id='sleep-score',
        figure={
            'data': [
                {
                    'x': dates,
                    'y': resting_hr,
                    'name': 'Resting heart rate',
                    'mode': 'line',
                    'line': {'color': constants.COLOUR_PURPLE}
                }
            ]
        }
    )

