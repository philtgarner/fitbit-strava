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

ACCESS_TOKEN_KEY = 'access_token'


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
login_url = 'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=22BCBG&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fauth&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'

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
    return html.Div([
        html.H3('Log in'),
        html.A('Log in', href=login_url)
    ])

def getAccessToken(query):

    if session.get(ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['fitbit']['client_id']
        client_secret = config['fitbit']['client_secret']

        # Encode the client ID and secret for authentication when requesting a token
        auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

        # Get the code from the permission request response
        code = getParameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://api.fitbit.com/oauth2/token"
        data = {'clientId': client_id, 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/auth',
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
            session[ACCESS_TOKEN_KEY] = output[ACCESS_TOKEN_KEY]

            # Access token saved to session for subsequent calls - success
            return True

        # We failed to get an access token for some reason
        # TODO Add some proper error handling here
        return False

    # If we already have an access token then there's no need to look again for one
    return True


def auth(query):
    if getAccessToken(query):
        access_token = session.get(ACCESS_TOKEN_KEY, None)

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Resting heart rate"),
                                getRestingHeartRateGraph(access_token)
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
                                getDetailedHeartRateGraph(access_token)
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
                                getSleepScoresGraph(access_token)
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
                                getSleepHistoryGraph(access_token)
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

def getDetailedHeartRateGraph(access_token):

    yesterday = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')

    # Get some data
    endpoint = f"https://api.fitbit.com/1/user/-/activities/heart/date/{yesterday}/1d/1min.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    hr = requests.get(endpoint, headers=headers).json()

    print(hr)

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

    print(hr)

    dates = list(map(lambda x: x['dateTime'], hr['activities-heart']))

    # TODO Handle things if there is no resting heart rate for the day (probably caused by not syncing yet?)
    resting_hr = list(map(lambda x: x['value'].get('restingHeartRate', 0), hr['activities-heart']))

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

    print(hr)

    dates = list(map(lambda x: x['dateOfSleep'], hr['sleep']))

    print(hr['sleep'][0]['levels']['summary'])
    # TODO Not every day has deep sleep recorded
    deep = list(map(lambda x: x['levels']['summary'].get('deep', {'minutes': 0})['minutes'], hr['sleep']))
    light = list(map(lambda x: x['levels']['summary'].get('light', {'minutes': 0})['minutes'], hr['sleep']))
    rem = list(map(lambda x: x['levels']['summary'].get('rem', {'minutes': 0})['minutes'], hr['sleep']))
    wake = list(map(lambda x: x['levels']['summary'].get('wake', {'minutes': 0})['minutes'], hr['sleep']))

    # Data from sleeps not long enough to be tracked with sleep stages
    awake = list(map(lambda x: x['levels']['summary'].get('awake', {'minutes': 0})['minutes'], hr['sleep']))
    asleep = list(map(lambda x: x['levels']['summary'].get('asleep', {'minutes': 0})['minutes'], hr['sleep']))
    restless = list(map(lambda x: x['levels']['summary'].get('restless', {'minutes': 0})['minutes'], hr['sleep']))


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
    elif pathname == '/auth':
        return auth(search)
    else:
        return html.H1('404')

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)

