import base64
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs
import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import yaml
import dash_bootstrap_components as dbc
from flask_session import Session
from flask import Flask, session
from datetime import datetime, timedelta

from fitbit import get_sleep_history, get_heart_rate_detailed, get_heart_rate_history, get_weight
from strava import get_strava_activities, get_strava_activity, get_strava_activity_stream, get_cycling_activity_power_stats

FITBIT_ACCESS_TOKEN_KEY = 'fitbit_access_token'
STRAVA_ACCESS_TOKEN_KEY = 'strava_access_token'

DATE_FORMAT = '%b %d %Y %H:%M'

# See here for themes
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
app.config.suppress_callback_exceptions = True

app.server.config["SESSION_PERMANENT"] = False
app.server.config["SESSION_TYPE"] = "filesystem"
Session(app.server)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard")),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                dbc.DropdownMenuItem(dbc.NavLink('Strava sign in', href='/strava')),
                dbc.DropdownMenuItem(dbc.NavLink('Fitbit sign in', href='/fitbit')),
            ],
        ),
    ],
    brand="Phil Garner fitness dashboard",
    brand_href="#",
    sticky="top",
)

app.layout = html.Div([
    # represents the URL bar, doesn't render anything
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


def login():
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("Fitness dashboard")
                        ],
                        md=12,
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Fitbit"),
                            html.A('Log in', href=get_fitbit_login_url())
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.H4("Strava"),
                            html.A('Log in', href=get_strava_login_url())
                        ],
                        md=6,
                    )
                ]
            )
        ]
    )


def get_fitbit_login_url():
    config = yaml.safe_load(open("config.yml"))
    client_id = config['fitbit']['client_id']
    return f'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Ffitbitauth&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'


def get_strava_login_url():
    config = yaml.safe_load(open("config.yml"))
    client_id = config['strava']['client_id']
    return f'http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://127.0.0.1:5000/stravaauth&approval_prompt=auto&scope=read,read_all,activity:read,activity:read_all'


def get_fitbit_access_token(query):
    if session.get(FITBIT_ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['fitbit']['client_id']
        client_secret = config['fitbit']['client_secret']

        # Encode the client ID and secret for authentication when requesting a token
        auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

        # Get the code from the permission request response
        code = get_parameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://api.fitbit.com/oauth2/token"
        data = {'clientId': client_id, 'grant_type': 'authorization_code',
                'redirect_uri': 'http://127.0.0.1:5000/fitbitauth',
                'code': code}
        headers = {"Authorization": f"Basic {auth}",
                   'Content-Type': 'application/x-www-form-urlencoded'}

        output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

        # A successful call returns the following data:
        # - access_token
        # - expires_in
        # - refresh_token
        # - scope
        # - user_id
        if 'access_token' in output:
            session[FITBIT_ACCESS_TOKEN_KEY] = output['access_token']

            # Access token saved to session for subsequent calls - success
            return True

        # We failed to get an access token for some reason
        # TODO Add some proper error handling here
        return False

    # If we already have an access token then there's no need to look again for one
    return True


def get_strava_access_token(query):
    if session.get(STRAVA_ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['strava']['client_id']
        client_secret = config['strava']['client_secret']

        # Get the code from the permission request response
        code = get_parameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://www.strava.com/oauth/token"
        data = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'authorization_code',
                'code': code}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

        # A successful call returns the following data:
        '''{
            "token_type": "Bearer",
            "expires_at": 1562908002,
            "expires_in": 21600,
            "refresh_token": "REFRESHTOKEN",
            "access_token": "ACCESSTOKEN",
            "athlete": {
                "id": 123456,
                "username": "MeowTheCat",
                "resource_state": 2,
                "firstname": "Meow",
                "lastname": "TheCat",
                "city": "",
                "state": "",
                "country": null,
                ...
            }
        }'''
        if 'access_token' in output:
            session[STRAVA_ACCESS_TOKEN_KEY] = output['access_token']

            # Access token saved to session for subsequent calls - success
            return True

        # We failed to get an access token for some reason
        # TODO Add some proper error handling here
        return False

    # If we already have an access token then there's no need to look again for one
    return True


def fitbit_auth(query):
    if get_fitbit_access_token(query):
        return html.Div([
            html.H3('Fitbit authenticated'),
            dcc.Link('Dashboard', href='/dashboard'),
            dcc.Link('Home', href='/')
        ])
    return html.Div([
        html.H3('Fitbit authentication error'),
        html.P('An error occurred')
    ])


def strava_auth(query):
    if get_strava_access_token(query):
        return html.Div([
            html.H3('Strava authenticated'),
            dcc.Link('Dashboard', href='/dashboard'),
            dcc.Link('Home', href='/')
        ])
    return html.Div([
        html.H3('Strava authentication error'),
        html.P('An error occurred')
    ])


def dashboard():
    fitbit_access_token = session.get(FITBIT_ACCESS_TOKEN_KEY, None)
    strava_access_token = session.get(STRAVA_ACCESS_TOKEN_KEY, None)
    if fitbit_access_token is not None and strava_access_token is not None:

        # Get Fitbit data
        heart_rate_history = get_heart_rate_history(fitbit_access_token)
        heart_rate_details = get_heart_rate_detailed(fitbit_access_token)
        sleep_history = get_sleep_history(fitbit_access_token)

        # Get Strava data
        activity_history = get_strava_activities(strava_access_token)

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Resting heart rate"),
                                get_resting_heart_rate_graph(heart_rate_history)
                            ],
                            md=10,
                        ),
                        dbc.Col(
                            [
                                html.H3('Summary')
                            ],
                            md=2
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Yesterday's heart rate"),
                                get_detailed_heart_rate_graph(heart_rate_details)
                            ],
                            md=10
                        ),
                        dbc.Col(
                            [
                                html.H3('Summary')
                            ],
                            md=2
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Sleep efficiency"),
                                get_sleep_efficiency_graph(sleep_history)
                            ],
                            md=10
                        ),
                        dbc.Col(
                            [
                                html.H3('Summary')
                            ],
                            md=2
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Sleep history"),
                                get_sleep_history_graph(sleep_history)
                            ],
                            md=10
                        ),
                        dbc.Col(
                            [
                                html.H3('Summary')
                            ],
                            md=2
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Activities"),
                                get_activity_history_graph(activity_history)
                            ],
                            md=10
                        ),
                        dbc.Col(
                            [
                                html.H3('Summary')
                            ],
                            md=2
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Cycling activities"),
                                get_cycling_activity_history_table(activity_history)
                            ],
                            md=12
                        )
                    ]
                )
            ],
            className="mt-4",
        )

    else:
        return html.Div([
            html.H3('Auth'),
            html.P('An error occurred')
        ])


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
                    'line': {'color': 'red'}
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
                    'line': {'color': 'red'}
                }
            ]
        }
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
                    'line': {'color': 'purple'}
                }
            ]
        }
    )


def get_sleep_history_graph(sleep_history):
    dates = list(map(lambda x: x['dateOfSleep'], sleep_history['sleep']))

    deep = list(map(lambda x: x['levels']['summary'].get('deep', {'minutes': None})['minutes'], sleep_history['sleep']))
    light = list(
        map(lambda x: x['levels']['summary'].get('light', {'minutes': None})['minutes'], sleep_history['sleep']))
    rem = list(map(lambda x: x['levels']['summary'].get('rem', {'minutes': None})['minutes'], sleep_history['sleep']))
    wake = list(map(lambda x: x['levels']['summary'].get('wake', {'minutes': None})['minutes'], sleep_history['sleep']))

    # Data from sleeps not long enough to be tracked with sleep stages
    awake = list(
        map(lambda x: x['levels']['summary'].get('awake', {'minutes': None})['minutes'], sleep_history['sleep']))
    asleep = list(
        map(lambda x: x['levels']['summary'].get('asleep', {'minutes': None})['minutes'], sleep_history['sleep']))
    restless = list(
        map(lambda x: x['levels']['summary'].get('restless', {'minutes': None})['minutes'], sleep_history['sleep']))

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
            html.Td(dcc.Link(cycling_activity['name'], href=f'/cycling?activity={id}')),
            html.Td(datetime.strptime(cycling_activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ').strftime(DATE_FORMAT)),
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
    time = list(map(lambda t: t/60, list(filter(lambda f: f['type'] == 'time', cycling_activity_stream))[0]['data']))
    power = list(filter(lambda f: f['type'] == 'watts', cycling_activity_stream))[0]['data']
    hr = list(filter(lambda f: f['type'] == 'heartrate', cycling_activity_stream))[0]['data']

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

def get_cycling_average_power_table(power_averages, body_composition):
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th('Duration'),
                        html.Th('Power (Watts)'),
                        html.Th('Power:weight (Watts/kg)')
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td('Twenty minutes'),
                            html.Td(round(power_averages['twenty_minute'], 1)),
                            html.Td(round(power_averages['twenty_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Ten minutes'),
                            html.Td(round(power_averages['ten_minute'], 1)),
                            html.Td(round(power_averages['ten_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Five minutes'),
                            html.Td(round(power_averages['five_minute'], 1)),
                            html.Td(round(power_averages['five_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('One minute'),
                            html.Td(round(power_averages['one_minute'], 1)),
                            html.Td(round(power_averages['one_minute'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Thirty seconds'),
                            html.Td(round(power_averages['thirty_second'], 1)),
                            html.Td(round(power_averages['thirty_second'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('Five seconds'),
                            html.Td(round(power_averages['five_second'], 1)),
                            html.Td(round(power_averages['five_second'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    ),
                    html.Tr(
                        [
                            html.Td('One second'),
                            html.Td(round(power_averages['one_second'], 1)),
                            html.Td(round(power_averages['one_second'] / body_composition['weight'], 2) if body_composition['weight'] is not None else '??')
                        ]
                    )

                ]
            )
        ],
        className='table table-hover'
    )


def get_cycling_summary_table(cycling_activity):
    '''

    name
    description
    [photos][primary][urls][600]
    '''
    return html.Table(
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
                    html.Td(cycling_activity['average_heartrate'])
                ]
            ),
            html.Tr(
                [
                    html.Th('Heartrate (max)'),
                    html.Td(cycling_activity['max_heartrate'])
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
        ],
        className='table table-hover'
    )


def cycling(query):
    fitbit_access_token = session.get(FITBIT_ACCESS_TOKEN_KEY, None)
    strava_access_token = session.get(STRAVA_ACCESS_TOKEN_KEY, None)
    activity_id = get_parameter(query, 'activity')[0]
    if fitbit_access_token is not None and strava_access_token is not None and activity_id is not None:

        cycling_activity = get_strava_activity(strava_access_token, activity_id)
        cycling_activity_stream = get_strava_activity_stream(strava_access_token, activity_id)
        power_averages = get_cycling_activity_power_stats(cycling_activity_stream)

        body_composition = get_weight(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ'))

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(cycling_activity['name']),
                                html.H2(cycling_activity['description']),
                                html.H2(datetime.strptime(cycling_activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ').strftime(DATE_FORMAT)),
                            ],
                            md=8,
                        ),
                        dbc.Col(
                            [
                                html.Img(src=cycling_activity['photos']['primary']['urls']['600'], style={'max-width': '100%'})
                            ],
                            md=4,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Summary"),
                                get_cycling_summary_table(cycling_activity)
                            ],
                            md=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Power vs HR"),
                                get_cycling_activity_graph(cycling_activity_stream)
                            ],
                            md=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Maximum power"),
                                get_cycling_average_power_table(power_averages, body_composition)
                            ],
                            md=12,
                        )
                    ]
                ),
            ],
            className="mt-4",
        )

    else:
        return html.Div([
            html.H3('Auth'),
            html.P('An error occurred')
        ])


def get_parameter(query, param):
    url = f'http://example.org{query}'
    parsed = urlparse.urlparse(url)
    try:
        return parse_qs(parsed.query)[param]
    except KeyError:
        return None


@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname'), dash.dependencies.Input('url', 'search')])
def display_page(pathname, search):
    if pathname == '/':
        return login()
    elif pathname == '/fitbitauth':
        return fitbit_auth(search)
    elif pathname == '/stravaauth':
        return strava_auth(search)
    elif pathname == '/dashboard':
        return dashboard()
    elif pathname == '/cycling':
        return cycling(search)
    else:
        return html.H1('404')


if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
