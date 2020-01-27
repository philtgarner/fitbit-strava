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

from fitbit import get_sleep_history, get_heart_rate_detailed, get_heart_rate_history
from strava import get_strava_activities

FITBIT_ACCESS_TOKEN_KEY = 'fitbit_access_token'
STRAVA_ACCESS_TOKEN_KEY = 'strava_access_token'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

app.server.config["SESSION_PERMANENT"] = False
app.server.config["SESSION_TYPE"] = "filesystem"
Session(app.server)

app.layout = html.Div([
    # represents the URL bar, doesn't render anything
    dcc.Location(id='url', refresh=False),
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
    return f'http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://127.0.0.1:5000/stravaauth&approval_prompt=force&scope=read,read_all,activity:read,activity:read_all'


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
    else:
        return html.H1('404')


if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
