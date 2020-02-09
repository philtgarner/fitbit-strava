import dash_core_components as dcc
from helpers.constants import *
import dash_html_components as html
from datetime import datetime, timedelta


def get_activity_history_graph(activity_history):
    virtual_ride_dates = list(map(lambda x: x['start_date'], activity_history))
    virtual_ride_times = list(map(lambda x: x['elapsed_time']/60 if x['type'] == 'VirtualRide' else None, activity_history))

    run_dates = list(map(lambda x: x['start_date'], activity_history))
    run_times = list(map(lambda x: x['elapsed_time']/60 if x['type'] == 'Run' else None, activity_history))

    ride_dates = list(map(lambda x: x['start_date'], activity_history))
    ride_times = list(map(lambda x: x['elapsed_time']/60 if x['type'] == 'Ride' else None, activity_history))

    walk_dates = list(map(lambda x: x['start_date'], activity_history))
    walk_times = list(map(lambda x: x['elapsed_time']/60 if x['type'] == 'Walk' else None, activity_history))

    hike_dates = list(map(lambda x: x['start_date'], activity_history))
    hike_times = list(map(lambda x: x['elapsed_time']/60 if x['type'] == 'Hike' else None, activity_history))

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

    rows = list(map(cycling_activity_to_tr, filter(lambda a: a['type'] == 'VirtualRide' or a['type'] == 'Ride', activity_history)))

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Activity name'),
                        html.Th('Start time'),
                        html.Th('Ride time'),
                        html.Th('Average power'),
                        html.Th('Average weighted power'),
                        html.Th('Max power'),
                        html.Th('Average heart rate'),
                        html.Th('Max heart rate'),
                        html.Th('Suffer score'),
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
    # Name
    # Start time
    # Ride time
    # Average power
    # Average weighted power
    # Max power
    # Average HR
    # Max HR
    # Suffer score
    id = cycling_activity['id']
    return html.Tr(
        [
            html.Td(dcc.Link(cycling_activity['name'], href=f'{URL_CYCLING}?activity={id}')),
            html.Td(datetime.strptime(cycling_activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ').strftime(DISPLAY_DATE_FORMAT)),
            html.Td(str(timedelta(seconds=cycling_activity['moving_time']))),
            html.Td(cycling_activity['average_watts']),
            html.Td(cycling_activity['weighted_average_watts']),
            html.Td(cycling_activity['max_watts']),
            html.Td(cycling_activity['average_heartrate']),
            html.Td(cycling_activity['max_heartrate']),
            html.Td(cycling_activity['suffer_score'])
        ]
    )


def get_cycling_activity_graph(cycling_activity_stream):

    time = list(filter(lambda f: f['type'] == 'time', cycling_activity_stream))
    power = list(filter(lambda f: f['type'] == 'watts', cycling_activity_stream))
    hr = list(filter(lambda f: f['type'] == 'heartrate', cycling_activity_stream))
    empty = [None] * len(time[0]['data'])

    time = list(map(lambda t: t / 60, time[0]['data']))
    power = power[0]['data'] if len(power) > 0 else empty
    hr = hr[0]['data'] if len(hr) > 0 else empty

    return dcc.Graph(
        id='cycling-power-hr',
        figure={
            'data': [
                {
                    'x': time,
                    'y': power,
                    'name': 'Power',
                    'mode': 'line',
                    'line': {'color': 'blue'}
                },
                {
                    'x': time,
                    'y': hr,
                    'name': 'Heart rate',
                    'mode': 'line',
                    'line': {'color': 'red'},
                    'yaxis': 'y2'
                }
            ],
            'layout': {
                'yaxis':{
                    'title': 'Power'
                },
                'yaxis2':{
                    'title':'Heart rate',
                    'overlaying':'y',
                    'side':'right'
                }
            }
        }
    )

def get_cycling_summary_table(cycling_activity):
    '''

    name
    description
    [photos][primary][urls][600]
    '''
    return html.Table(
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Th('Distance'),
                        html.Td(cycling_activity['distance'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Time (moving)'),
                        html.Td(cycling_activity['moving_time'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Time (elapsed)'),
                        html.Td(cycling_activity['elapsed_time'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Speed (average)'),
                        html.Td(cycling_activity['average_speed'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Speed (max)'),
                        html.Td(cycling_activity['max_speed'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Power (average)'),
                        html.Td(cycling_activity['average_watts'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Power (weighted average)'),
                        html.Td(cycling_activity['weighted_average_watts'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Power (max)'),
                        html.Td(cycling_activity['max_watts'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Heartrate (average)'),
                        html.Td(cycling_activity.get('average_heartrate', EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Heartrate (max)'),
                        html.Td(cycling_activity.get('max_heartrate', EMPTY_PLACEHOLDER))
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Elevation gain'),
                        html.Td(cycling_activity['total_elevation_gain'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Cadence (average)'),
                        html.Td(cycling_activity['average_cadence'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Calories'),
                        html.Td(cycling_activity['calories'])
                    ]
                ),
                html.Tr(
                    [
                        html.Th('Suffer score'),
                        html.Td(cycling_activity['suffer_score'])
                    ]
                ),
            ]
        ),
        className='table table-hover'
    )


def get_activity_image(strava_activity):
    if strava_activity['photos']['count'] > 0:
        return html.Img(src=strava_activity['photos']['primary']['urls']['600'], style={'max-width': '100%'})
    return None
