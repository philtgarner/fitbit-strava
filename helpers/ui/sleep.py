import dash_core_components as dcc
import helpers.constants as constants
import dash_html_components as html
from datetime import datetime, timedelta
import plotly.figure_factory as ff
import dash_bootstrap_components as dbc


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


def get_detailed_sleep_table(sleep_day):
    total_duration = timedelta(milliseconds=sleep_day['duration'])
    deep_duration = timedelta(minutes=sleep_day['levels']['summary']['deep']['minutes'])
    light_duration = timedelta(minutes=sleep_day['levels']['summary']['light']['minutes'])
    rem_duration = timedelta(minutes=sleep_day['levels']['summary']['rem']['minutes'])
    awake_duration = timedelta(minutes=sleep_day['levels']['summary']['wake']['minutes'])

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Phase'),
                        html.Th('Time'),
                        html.Th('Percentage'),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td('Total'),
                            html.Td(str(total_duration)),
                            html.Td(constants.EMPTY_PLACEHOLDER),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Awake'),
                            html.Td(str(awake_duration)),
                            html.Td(round(awake_duration / total_duration * 100, 1)),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('REM'),
                            html.Td(str(rem_duration)),
                            html.Td(round(rem_duration / total_duration * 100, 1)),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Light'),
                            html.Td(str(light_duration)),
                            html.Td(round(light_duration / total_duration * 100, 1)),
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Deep'),
                            html.Td(str(deep_duration)),
                            html.Td(round(deep_duration / total_duration * 100, 1)),
                        ]
                    ),
                ]
            )
        ],
        className='table table-hover'
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

        fig = ff.create_gantt(gantt_chart_data, group_tasks=True, index_col='Task', colors=colours, title=None, height=None)

        row = dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(figure=fig, id='gantt')
                    ],
                    md=10,
                ),
                dbc.Col(
                    [
                        html.H2('Summary'),
                        get_detailed_sleep_table(sleep_day)
                    ],
                    md=2,
                )
            ]
        )

        graphs.append(row)

    # Reverse the list of graphs to get them in tme order
    return graphs[::-1]





def sleep_period_to_gantt_element(sleep_period):
    start_time = datetime.strptime(sleep_period['dateTime'], constants.FITBIT_SLEEP_TIME)
    end_time = start_time + timedelta(seconds=sleep_period['seconds'])
    current_phase = sleep_period['level']

    return dict(
        Task=get_sleep_name(current_phase),
        Start = start_time.strftime(constants.GANTT_CHART_TIME),
        Finish=end_time.strftime(constants.GANTT_CHART_TIME),
        Level=get_sleep_level(current_phase),
        Description=f'Duration: {str(end_time - start_time)}'
    )


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
