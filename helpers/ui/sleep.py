import dash_core_components as dcc
import helpers.constants as constants
import dash_html_components as html
from datetime import datetime, timedelta
import plotly.figure_factory as ff


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
                'colorway': [constants.COLOUR_SLEEP_DEEP, constants.COLOUR_SLEEP_LIGHT, constants.COLOUR_SLEEP_REM, constants.COLOUR_SLEEP_WAKE, '#FF0000', '#00FF00', '#0000FF']
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


def get_detailed_sleep_graph(sleep_data):
    graphs = list()
    for sleep_day in sleep_data['sleep']:
        sleep_periods = sleep_day['levels']['data']

        gantt_chart_data = list(map(sleep_period_to_gantt_element, sleep_periods))

        gantt_chart_data = sorted(gantt_chart_data, key=lambda g: g['Level'], reverse=True)

        colours = dict(Awake=constants.COLOUR_SLEEP_WAKE,
                      REM=constants.COLOUR_SLEEP_REM,
                      Deep=constants.COLOUR_SLEEP_DEEP,
                      Light=constants.COLOUR_SLEEP_LIGHT)

        fig = ff.create_gantt(gantt_chart_data, group_tasks=True, index_col='Task', colors=colours, title=None)

        graphs.append(dcc.Graph(figure=fig, id='gantt'))

    # Reverse the list of graphs to get them in tme order
    return graphs[::-1]


def sleep_period_to_gantt_element(sleep_period):
    start_time = datetime.strptime(sleep_period['dateTime'], constants.FITBIT_SLEEP_TIME)
    end_time = start_time + timedelta(seconds=sleep_period['seconds'])
    current_phase = sleep_period['level']

    return dict(Task=get_sleep_name(current_phase), Start = start_time.strftime(constants.GANTT_CHART_TIME), Finish=end_time.strftime(constants.GANTT_CHART_TIME), Level=get_sleep_level(current_phase))


def get_sleep_name(sleep_phase):
    if sleep_phase == 'wake':
        return 'Awake'
    elif sleep_phase == 'rem':
        return 'REM'
    elif sleep_phase == 'deep':
        return 'Deep'
    elif sleep_phase == 'light':
        return 'Light'
    else:
        return 'Unknown'


def get_sleep_level(sleep_phase):
    if sleep_phase == 'wake':
        return 4
    elif sleep_phase == 'rem':
        return 3
    elif sleep_phase == 'deep':
        return 1
    elif sleep_phase == 'light':
        return 2
    else:
        return 999
