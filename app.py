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

import helpers.api.strava as api_strava
import helpers.api.fitbit as api_fitbit
import helpers.ui.heartrate as ui_heartrate
import helpers.ui.body_composition as ui_body_composition
import helpers.ui.power as ui_power
import helpers.ui.sleep as ui_sleep
import helpers.ui.strava_activities as ui_strava
from helpers.constants import *


# See here for themes
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
app.config.suppress_callback_exceptions = True

app.server.config["SESSION_PERMANENT"] = False
app.server.config["SESSION_TYPE"] = "filesystem"
Session(app.server)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink('Dashboard', href=URL_DASHBOARD)),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label='Menu',
            children=[
                dbc.DropdownMenuItem(dbc.NavLink('Strava sign in', href='/strava')),
                dbc.DropdownMenuItem(dbc.NavLink('Fitbit sign in', href='/fitbit')),
            ],
        ),
    ],
    brand='Phil Garner fitness dashboard',
    brand_href='#',
    sticky='top',
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
    if session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None) is None:
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
            session[SESSION_FITBIT_ACCESS_TOKEN_KEY] = output['access_token']

            # Access token saved to session for subsequent calls - success
            return True

        # We failed to get an access token for some reason
        # TODO Add some proper error handling here
        return False

    # If we already have an access token then there's no need to look again for one
    return True


def get_strava_access_token(query):
    if session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None) is None:
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
            session[SESSION_STRAVA_ACCESS_TOKEN_KEY] = output['access_token']

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
            dcc.Link('Dashboard', href=URL_DASHBOARD),
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
            dcc.Link('Dashboard', href=URL_DASHBOARD),
            dcc.Link('Home', href='/')
        ])
    return html.Div([
        html.H3('Strava authentication error'),
        html.P('An error occurred')
    ])


def dashboard():
    fitbit_access_token = session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None)
    strava_access_token = session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None)
    if fitbit_access_token is not None and strava_access_token is not None:

        # Get Fitbit data
        heart_rate_history = api_fitbit.get_heart_rate_history(fitbit_access_token)
        heart_rate_details = api_fitbit.get_heart_rate_detailed(fitbit_access_token)
        sleep_history = api_fitbit.get_sleep_history(fitbit_access_token)

        # Get Strava data
        activity_history = api_strava.get_strava_activities(strava_access_token)

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Resting heart rate"),
                                ui_heartrate.get_resting_heart_rate_graph(heart_rate_history)
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
                                ui_heartrate.get_detailed_heart_rate_graph(heart_rate_details)
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
                                ui_sleep.get_sleep_efficiency_graph(sleep_history)
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
                                ui_sleep.get_sleep_history_graph(sleep_history)
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
                                ui_strava.get_activity_history_graph(activity_history)
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
                                ui_strava.get_cycling_activity_history_table(activity_history)
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


def cycling(query):
    fitbit_access_token = session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None)
    strava_access_token = session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None)
    activity_id = get_parameter(query, 'activity')[0]
    if fitbit_access_token is not None and strava_access_token is not None and activity_id is not None:

        cycling_activity = api_strava.get_strava_activity(strava_access_token, activity_id)
        cycling_activity_stream = api_strava.get_strava_activity_stream(strava_access_token, activity_id)
        power_averages = api_strava.get_cycling_activity_power_stats(cycling_activity_stream)

        body_composition = api_fitbit.get_weight(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT))
        day_heartrate = api_fitbit.get_heart_rate_detailed(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT), '1sec')

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(cycling_activity[STRAVA_API_KEY_ACTIVITY_NAME]),
                                html.H2(datetime.strptime(cycling_activity[STRAVA_API_KEY_ACTIVITY_START_LOCAL], UTC_DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)),
                                html.P(cycling_activity[STRAVA_API_KEY_ACTIVITY_DESCRIPTION]),
                            ],
                            md=8,
                        ),
                        dbc.Col(
                            [
                                ui_strava.get_activity_image(cycling_activity)
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
                                ui_strava.get_cycling_summary_table(cycling_activity)
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H3("Body composition"),
                                ui_body_composition.get_body_composition_table(body_composition)
                            ],
                            md=6,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Power vs HR"),
                                ui_strava.get_cycling_activity_graph(cycling_activity_stream)
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
                                ui_power.get_cycling_average_power_table(power_averages, body_composition)
                            ],
                            md=12,
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Recovery heartrate"),
                                ui_heartrate.get_heartrate_recovery(cycling_activity_stream, day_heartrate, datetime.strptime(cycling_activity[STRAVA_API_KEY_ACTIVITY_START], UTC_DATE_FORMAT))
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
    if pathname == URL_BASE:
        return login()
    elif pathname == URL_FITBIT_AUTH:
        return fitbit_auth(search)
    elif pathname == URL_STRAVA_AUTH:
        return strava_auth(search)
    elif pathname == URL_DASHBOARD:
        return dashboard()
    elif pathname == URL_CYCLING:
        return cycling(search)
    else:
        return html.H1('404')


if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
