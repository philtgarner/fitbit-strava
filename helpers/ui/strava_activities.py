import dash_core_components as dcc
from helpers.constants import *
import dash_html_components as html
from datetime import datetime, timedelta


def get_activity_history_graph(activity_history):
    virtual_ride_dates = list(map(lambda x: x[STRAVA_API_KEY_ACTIVITY_START_LOCAL], activity_history))
    virtual_ride_times = list(map(lambda x: x[STRAVA_API_KEY_ELAPSED_TIME]/60 if x[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_VIRTUAL_RIDE else None, activity_history))

    run_dates = list(map(lambda x: x[STRAVA_API_KEY_ACTIVITY_START_LOCAL], activity_history))
    run_times = list(map(lambda x: x[STRAVA_API_KEY_ELAPSED_TIME]/60 if x[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_RUN else None, activity_history))

    ride_dates = list(map(lambda x: x[STRAVA_API_KEY_ACTIVITY_START_LOCAL], activity_history))
    ride_times = list(map(lambda x: x[STRAVA_API_KEY_ELAPSED_TIME]/60 if x[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_RIDE else None, activity_history))

    walk_dates = list(map(lambda x: x[STRAVA_API_KEY_ACTIVITY_START_LOCAL], activity_history))
    walk_times = list(map(lambda x: x[STRAVA_API_KEY_ELAPSED_TIME]/60 if x[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_WALK else None, activity_history))

    hike_dates = list(map(lambda x: x[STRAVA_API_KEY_ACTIVITY_START_LOCAL], activity_history))
    hike_times = list(map(lambda x: x[STRAVA_API_KEY_ELAPSED_TIME]/60 if x[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_HIKE else None, activity_history))

    return dcc.Graph(
        id='activity_history',
        figure={
            'data': [
                {
                    'x': virtual_ride_dates,
                    'y': virtual_ride_times,
                    'name': 'Virtual ride',
                    'type': 'bar'
                },
                {
                    'x': ride_dates,
                    'y': ride_times,
                    'name': 'Ride',
                    'type': 'bar'
                },
                {
                    'x': run_dates,
                    'y': run_times,
                    'name': 'Run',
                    'type': 'bar'
                },
                {
                    'x': walk_dates,
                    'y': walk_times,
                    'name': 'Walk',
                    'type': 'bar'
                },
                {
                    'x': hike_dates,
                    'y': hike_times,
                    'name': 'Hike',
                    'type': 'bar'
                }
            ],
            'layout': {
                'barmode': 'stack',
            }
        },
    )


def get_cycling_activity_history_table(activity_history):

    rows = list(map(cycling_activity_to_tr, filter(lambda a: a[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_VIRTUAL_RIDE or a[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_ACTIVITY_RIDE, activity_history)))

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th(TITLE_ACTIVITY_NAME),
                        html.Th(TITLE_START_TIME),
                        html.Th(TITLE_RIDE_TIME),
                        html.Th(TITLE_AVERAGE_POWER),
                        html.Th(TITLE_AVERAGE_WEIGHTED_POWER),
                        html.Th(TITLE_MAX_POWER),
                        html.Th(TITLE_AVERAGE_HEARTRATE),
                        html.Th(TITLE_MAX_HEARTRATE),
                        html.Th(TITLE_SUFFER_SCORE),
                    ]
                )
            ),
            html.Tbody(
                rows
            )
        ],
        className='table table-hover'
    )


def cycling_activity_to_tr(cycling_activity):
    id = cycling_activity[STRAVA_API_KEY_ACTIVITY_ID]
    return html.Tr(
        [
            html.Td(dcc.Link(cycling_activity[STRAVA_API_KEY_ACTIVITY_NAME], href=f'{URL_CYCLING}?activity={id}')),
            html.Td(datetime.strptime(cycling_activity[STRAVA_API_KEY_ACTIVITY_START_LOCAL], UTC_DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)),
            html.Td(str(timedelta(seconds=cycling_activity[STRAVA_API_KEY_MOVING_TIME]))),
            html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_POWER, EMPTY_PLACEHOLDER)),
            html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_WEIGHTED_POWER, EMPTY_PLACEHOLDER)),
            html.Td(cycling_activity.get(STRAVA_API_KEY_MAX_POWER, EMPTY_PLACEHOLDER)),
            html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_HEARTRATE, EMPTY_PLACEHOLDER)),
            html.Td(cycling_activity.get(STRAVA_API_KEY_MAX_HEARTRATE, EMPTY_PLACEHOLDER)),
            html.Td(cycling_activity.get(STRAVA_API_KEY_SUFFER_SCORE, EMPTY_PLACEHOLDER))
        ]
    )


def get_cycling_activity_graph(cycling_activity_stream):

    time = list(filter(lambda f: f[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_API_KEY_DATA_STREAM_TIME, cycling_activity_stream))
    power = list(filter(lambda f: f[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_API_KEY_DATA_STREAM_POWER, cycling_activity_stream))
    hr = list(filter(lambda f: f[STRAVA_API_KEY_DATA_STREAM_TYPE] == STRAVA_API_KEY_DATA_STREAM_HEARTRATE, cycling_activity_stream))

    # Create an empty array of the right same length (we assume we always get time)
    # This will be used if we're missing power and/or HR data
    empty = [None] * len(time[0][STRAVA_API_KEY_DATA_STREAM_DATA])

    time = list(map(lambda t: t / 60, time[0][STRAVA_API_KEY_DATA_STREAM_DATA]))
    power = power[0][STRAVA_API_KEY_DATA_STREAM_DATA] if len(power) > 0 else empty
    hr = list(map(lambda h: h if h > 0 else None, hr[0][STRAVA_API_KEY_DATA_STREAM_DATA])) if len(hr) > 0 else empty

    return dcc.Graph(
        id='cycling-power-hr',
        figure={
            'data': [
                {
                    'x': time,
                    'y': power,
                    'name': 'Power',
                    'mode': 'line',
                    'line': {'color': COLOUR_BLUE}
                },
                {
                    'x': time,
                    'y': hr,
                    'name': 'Heart rate',
                    'mode': 'line',
                    'line': {'color': COLOUR_RED},
                    'yaxis': 'y2'
                }
            ],
            'layout': {
                'yaxis':{
                    'title': 'Power'
                },
                'yaxis2':{
                    'title': 'Heart rate',
                    'overlaying': 'y',
                    'side': 'right'
                }
            }
        }
    )


def get_cycling_route_table(cycling_activity):
    return html.Table(
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Th(TITLE_DISTANCE),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_DISTANCE, EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Elevation gain'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_ELEVATION_GAIN, EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Speed (average)'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_SPEED, EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Speed (max)'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_MAX_SPEED, EMPTY_PLACEHOLDER))
                    ]
                )
            ]
        ),
        className='table table-hover'
    )


def get_cycling_mini_table(cycling_activity):
    return html.Table(
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Th(),
                        html.Th('Avg'),
                        html.Th('Max')
                    ]
                ),
                # speed hr cad pow
                html.Tr(
                    [
                        html.Th('Speed'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_SPEED, EMPTY_PLACEHOLDER)),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_MAX_SPEED, EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Heartrate'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_HEARTRATE, EMPTY_PLACEHOLDER)),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_MAX_HEARTRATE, EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Cadence'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_CADENCE, EMPTY_PLACEHOLDER)),
                        html.Td(EMPTY_PLACEHOLDER)
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Power'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_AVERAGE_POWER, EMPTY_PLACEHOLDER)),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_MAX_POWER, EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Calories'),
                        html.Td(cycling_activity.get(STRAVA_API_KEY_CALORIES, EMPTY_PLACEHOLDER)),
                        html.Td()
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Elapsed time'),
                        html.Td(str(timedelta(seconds=cycling_activity[STRAVA_API_KEY_ELAPSED_TIME]))),
                        html.Td()
                    ]
                ),
            ]
        ),
        className='table table-hover table-sm'
    )



def get_activity_image(strava_activity):
    if strava_activity['photos']['count'] > 0:
        return html.Img(src=strava_activity['photos']['primary']['urls']['600'], style={'max-width': '100%'})
    return None
