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
from datetime import datetime, timedelta
from flask_session import Session
from flask import Flask, session

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
                            html.A('Log in', href=getFitbitLoginUrl())
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.H4("Strava"),
                            html.A('Log in', href=getStravaLoginUrl())
                        ],
                        md=6,
                    )
                ]
            )
        ]
    )

def getFitbitLoginUrl():
    config = yaml.safe_load(open("config.yml"))
    client_id = config['fitbit']['client_id']
    return f'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Ffitbitauth&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'


def getStravaLoginUrl():
    config = yaml.safe_load(open("config.yml"))
    client_id = config['strava']['client_id']
    return f'http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://127.0.0.1:5000/stravaauth&approval_prompt=force&scope=read,read_all,activity:read,activity:read_all'


def getFitbitAccessToken(query):
    if session.get(FITBIT_ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['fitbit']['client_id']
        client_secret = config['fitbit']['client_secret']

        # Encode the client ID and secret for authentication when requesting a token
        auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

        # Get the code from the permission request response
        code = getParameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://api.fitbit.com/oauth2/token"
        data = {'clientId': client_id, 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/fitbitauth',
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

def getStravaAccessToken(query):
    if session.get(STRAVA_ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['strava']['client_id']
        client_secret = config['strava']['client_secret']

        # Get the code from the permission request response
        code = getParameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://www.strava.com/oauth/token"
        data = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'authorization_code', 'code': code}
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


def fitbitAuth(query):
    if getFitbitAccessToken(query):
        return html.Div([
            html.H3('Fitbit authenticated'),
            dcc.Link('Dashboard', href='/dashboard')
        ])
    return html.Div([
        html.H3('Fitbit authentication error'),
        html.P('An error occurred')
    ])

def stravaAuth(query):
    if getStravaAccessToken(query):
        return html.Div([
            html.H3('Strava authenticated'),
            dcc.Link('Dashboard', href='/dashboard')
        ])
    return html.Div([
        html.H3('Strava authentication error'),
        html.P('An error occurred')
    ])


def dashboard():
    fitbit_access_token = session.get(FITBIT_ACCESS_TOKEN_KEY, None)
    strava_access_token = session.get(STRAVA_ACCESS_TOKEN_KEY, None)
    if fitbit_access_token is not None and strava_access_token is not None:

        activities = getStravaActivities(strava_access_token)

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Resting heart rate"),
                                getRestingHeartRateGraph(fitbit_access_token)
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
                                getDetailedHeartRateGraph(fitbit_access_token)
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
                                html.H3("Sleep scores"),
                                getSleepScoresGraph(fitbit_access_token)
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
                                getSleepHistoryGraph(fitbit_access_token)
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

def getStravaActivities(access_token):
    endpoint = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()


def getDetailedHeartRateGraph(access_token):

    yesterday = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')

    # Get some data
    endpoint = f"https://api.fitbit.com/1/user/-/activities/heart/date/{yesterday}/1d/1min.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    hr = requests.get(endpoint, headers=headers).json()

    dates = list(map(lambda x: x['time'], hr['activities-heart-intraday']['dataset']))
    detailed_hr = list(map(lambda x: x['value'], hr['activities-heart-intraday']['dataset']))

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

def getRestingHeartRateGraph(access_token):

    # Get some data
    endpoint = "https://api.fitbit.com/1/user/-/activities/heart/date/today/30d.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    hr = requests.get(endpoint, headers=headers).json()

    dates = list(map(lambda x: x['dateTime'], hr['activities-heart']))

    # TODO Handle things if there is no resting heart rate for the day (probably caused by not syncing yet?)
    resting_hr = list(map(lambda x: x['value'].get('restingHeartRate', None), hr['activities-heart']))

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

def getSleepScoresGraph(access_token):

    end = datetime.strftime(datetime.now(), '%Y-%m-%d')
    start = datetime.strftime(datetime.now() - timedelta(days=30), '%Y-%m-%d')

    # Get some data
    endpoint = f"https://api.fitbit.com/1.2/user/-/sleep/date/{start}/{end}.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    hr = requests.get(endpoint, headers=headers).json()

    dates = list(map(lambda x: x['dateOfSleep'], hr['sleep']))
    resting_hr = list(map(lambda x: x['efficiency'], hr['sleep']))

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

def getSleepHistoryGraph(access_token):

    end = datetime.strftime(datetime.now(), '%Y-%m-%d')
    start = datetime.strftime(datetime.now() - timedelta(days=30), '%Y-%m-%d')

    # Get some data
    endpoint = f"https://api.fitbit.com/1.2/user/-/sleep/date/{start}/{end}.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    hr = requests.get(endpoint, headers=headers).json()

    dates = list(map(lambda x: x['dateOfSleep'], hr['sleep']))

    deep = list(map(lambda x: x['levels']['summary'].get('deep', {'minutes': None})['minutes'], hr['sleep']))
    light = list(map(lambda x: x['levels']['summary'].get('light', {'minutes': None})['minutes'], hr['sleep']))
    rem = list(map(lambda x: x['levels']['summary'].get('rem', {'minutes': None})['minutes'], hr['sleep']))
    wake = list(map(lambda x: x['levels']['summary'].get('wake', {'minutes': None})['minutes'], hr['sleep']))

    # Data from sleeps not long enough to be tracked with sleep stages
    awake = list(map(lambda x: x['levels']['summary'].get('awake', {'minutes': None})['minutes'], hr['sleep']))
    asleep = list(map(lambda x: x['levels']['summary'].get('asleep', {'minutes': None})['minutes'], hr['sleep']))
    restless = list(map(lambda x: x['levels']['summary'].get('restless', {'minutes': None})['minutes'], hr['sleep']))

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

def getParameter(query, param):
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
        return fitbitAuth(search)
    elif pathname == '/stravaauth':
        return stravaAuth(search)
    elif pathname == '/dashboard':
        return dashboard()
    else:
        return html.H1('404')

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)

