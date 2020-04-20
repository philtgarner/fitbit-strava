import dash
import dash_core_components as dcc
import dash_html_components as html
import yaml
import dash_bootstrap_components as dbc
import json
import redis
import urllib.parse
from flask_session import Session
from flask import Flask, session
from datetime import datetime, timedelta
from dash.dependencies import Input, Output, State

import helpers.api.strava as api_strava
import helpers.api.fitbit as api_fitbit
import helpers.ui.heartrate as ui_heartrate
import helpers.ui.body_composition as ui_body_composition
import helpers.ui.power as ui_power
import helpers.ui.sleep as ui_sleep
import helpers.ui.strava_activities as ui_strava
import helpers.common as common
import helpers.auth.strava_auth as auth_strava
import helpers.auth.fitbit_auth as auth_fitbit
from helpers.constants import *


# See here for themes: https://bootswatch.com/cosmo/
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
app.title = TITLE_PAGE
app.config.suppress_callback_exceptions = True

config = yaml.safe_load(open('config.yml'))
session_type = config['session']['type']

if session_type == 'redis':
    app.server.config['SESSION_PERMANENT'] = True
    app.server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    app.server.config['SESSION_TYPE'] = session_type
    app.server.config['SESSION_REDIS'] = redis.Redis(host=config['session']['redis_host'], port=config['session']['redis_port'], db=0)
else:
    app.server.config['SESSION_TYPE'] = 'filesystem'

Session(app.server)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink('Dashboard', href=URL_DASHBOARD)),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label='Menu',
            children=[
                dbc.DropdownMenuItem(dbc.NavLink('Log out', href=URL_LOGOUT)),
            ],
        ),
    ],
    brand=TITLE_PAGE,
    brand_href=URL_DASHBOARD,
    sticky='top',
    fluid=True,
)

app.layout = html.Div([
    # represents the URL bar, doesn't render anything
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


def login():

    buttons = [
        dbc.Button(
            'Fitbit log in',
            href=get_fitbit_login_url(),
            color='dark',
            style={'backgroundColor': COLOUR_FITBIT_BLUE},
            block=True,
            className='mr-1'
        ),
        dbc.Button(
            'Strava log in',
            href=get_strava_login_url(),
            color='dark',
            style={'backgroundColor': COLOUR_STRAVA_ORANGE},
            block=True,
            className='mr-1'
        )
    ]

    if auth_fitbit.ensure_valid_access_token() and auth_strava.ensure_valid_access_token():
        buttons.append(
            dbc.Button(
                'Dashboard',
                href=URL_DASHBOARD,
                color='primary',
                className='mr-1',
                block=True
            )
        )

    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("This probably won't work for you"),
                            html.P(
                                "This is an app that combines Fitbit data and Strava. It uses a special level of API access with Fitbit that means, unless you own this application, it won't work for you."),
                            html.A('Fitbit personal apps',
                                   href='https://dev.fitbit.com/build/reference/web-api/basics/'),
                            html.H2('GitHub'),
                            html.A('GitHub repo', href='https://github.com/philtgarner/fitbit-strava/')
                        ]
                    ),
                    dbc.Col(
                        [
                            *buttons
                        ]
                    )
                ]
            ),
        ]
    )


def logout():
    session.pop(SESSION_FITBIT_ACCESS_TOKEN_KEY, None)
    session.pop(SESSION_FITBIT_REFRESH_TOKEN_KEY, None)
    session.pop(SESSION_FITBIT_EXPIRES_KEY, None)
    session.pop(SESSION_STRAVA_REFRESH_TOKEN_KEY, None)
    session.pop(SESSION_STRAVA_EXPIRES_KEY, None)
    session.pop(SESSION_STRAVA_ACCESS_TOKEN_KEY, None)


def get_fitbit_login_url():
    client_id = config['fitbit']['client_id']
    callback_url = urllib.parse.quote_plus(config['fitbit']['callback_url'])
    url = f'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={callback_url}&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'
    return url


def get_strava_login_url():
    client_id = config['strava']['client_id']
    callback_url = config['strava']['callback_url']
    return f'http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={callback_url}&approval_prompt=auto&scope=read,read_all,activity:read,activity:read_all,profile:read_all'


def fitbit_auth(query):
    if auth_fitbit.parse_query_for_access_token(query):

        buttons = list()
        if auth_strava.ensure_valid_access_token():
            buttons = [
                dbc.Col(
                    [
                        dbc.Button('Dashboard', href=URL_DASHBOARD, color='primary', className='mr-1', block=True),
                    ]
                )
            ]
        else:
            buttons = [
                dbc.Col(
                    [
                        dbc.Button('Home', href=URL_BASE, color='primary', className='mr-1', block=True)
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            'Strava log in',
                            href=get_strava_login_url(),
                            color='dark',
                            style={'backgroundColor': COLOUR_STRAVA_ORANGE},
                            block=True,
                            className='mr-1'
                        )
                    ]
                )
            ]

        return dbc.Container(
            [
                dbc.Row(
                    [
                        html.H3('Fitbit authenticated'),
                    ]
                ),
                dbc.Row(
                    buttons
                ),
            ]
        )
    return dbc.Container(
        [
            dbc.Row(
                [
                    html.H3('Fitbit authentication error'),
                    html.P('An error occurred')
                ]
            ),
            dbc.Row(
                [
                    dbc.Button('Home', href=URL_BASE, color='primary', className='mr-1', block=True)
                ]
            ),
        ]
    )


def strava_auth(query):
    if auth_strava.parse_query_for_access_token(query):

        buttons = list()
        if auth_fitbit.ensure_valid_access_token():
            buttons = [
                dbc.Col(
                    [
                        dbc.Button('Dashboard', href=URL_DASHBOARD, color='primary', className='mr-1', block=True),
                    ]
                )
            ]
        else:
            buttons = [
                dbc.Col(
                    [
                        dbc.Button('Home', href=URL_BASE, color='primary', className='mr-1', block=True)
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Button(
                            'Fitbit log in',
                            href=get_fitbit_login_url(),
                            color='dark',
                            style={'backgroundColor': COLOUR_FITBIT_BLUE},
                            block=True,
                            className='mr-1'
                        )
                    ]
                )
            ]
        return dbc.Container(
            [
                dbc.Row(
                    [
                        html.H3('Strava authenticated'),
                    ]
                ),
                dbc.Row(
                    buttons
                ),
            ]
        )
    return dbc.Container(
        [
            dbc.Row(
                [
                    html.H3('Strava authentication error'),
                    html.P('An error occurred')
                ]
            ),
            dbc.Row(
                [
                    dbc.Button('Home', href=URL_BASE, color='primary', className='mr-1', block=True)
                ]
            ),
        ]
    )


def dashboard():
    if auth_fitbit.ensure_valid_access_token() and auth_strava.ensure_valid_access_token():

        # Get the access tokens (now we have checked to ensure they're valid)
        strava_access_token = session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None)
        fitbit_access_token = session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None)

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
            fluid=True
        )

    else:
        return html.Div([
            html.H3('Auth'),
            html.P('An error occurred')
        ])


def cycling(query):
    activity_id = common.get_parameter(query, 'activity')[0]
    if auth_fitbit.ensure_valid_access_token() and auth_strava.ensure_valid_access_token():

        # Get the access tokens (now we have checked to ensure they're valid)
        strava_access_token = session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None)
        fitbit_access_token = session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None)

        cycling_activity = api_strava.get_strava_activity(strava_access_token, activity_id)
        cycling_activity_stream = api_strava.get_strava_activity_stream(strava_access_token, activity_id)
        power_averages = api_strava.get_cycling_activity_power_stats(cycling_activity_stream)
        athlete = api_strava.get_strava_athlete(strava_access_token)
        power_splits = api_strava.get_cycling_power_splits(cycling_activity_stream)
        gradient_splits = api_strava.get_cycling_gradient_splits(cycling_activity_stream)

        body_composition = api_fitbit.get_weight(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT))
        day_heartrate = api_fitbit.get_heart_rate_detailed(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT), '1sec')
        sleep = api_fitbit.get_sleep_history(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT) + timedelta(days=1), 1)

        # Store the activity stream so we can access it in callbacks
        session[f'{SESSION_STRAVA_ACTIVITY_STREAMS_KEY}-{activity_id}'] = json.dumps(cycling_activity_stream)

        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H1(cycling_activity[STRAVA_API_KEY_ACTIVITY_NAME])
                            ]
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4(datetime.strptime(cycling_activity[STRAVA_API_KEY_ACTIVITY_START_LOCAL], UTC_DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)),
                                html.P(cycling_activity[STRAVA_API_KEY_ACTIVITY_DESCRIPTION]),
                            ]
                        ),
                        dbc.Col(
                            [
                                ui_strava.get_activity_image(cycling_activity)
                            ]
                        ),
                        dbc.Col(
                            [
                                ui_strava.get_cycling_mini_table(cycling_activity)
                            ]
                        )
                    ]
                ),
                dcc.Tabs(
                    [
                        dcc.Tab(
                            label='Summary',
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                ui_strava.get_cycling_activity_graph(cycling_activity_stream)
                                            ],
                                            md=12,
                                        )
                                    ]
                                ),
                            ]
                        ),
                        dcc.Tab(
                            label='Route',
                            children=[
                                dbc.Row(
                                    dbc.Col(
                                        ui_strava.get_cycling_route_table(cycling_activity)
                                    )
                                )
                            ]
                        ),
                        dcc.Tab(
                            label='Body composition',
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                ui_body_composition.get_body_composition_table(body_composition)
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                        dcc.Tab(
                            label='Power',
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.H3('FTP'),
                                                html.P('Set your FTP here to ensure that the summary values are accurate. This value has been taken from Strava.'),
                                                dcc.Input(id='ftp', type='number', placeholder='FTP', value=athlete.get('ftp', '0'))
                                            ],
                                            md=12,
                                        )
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.H3("Power summary"),
                                                html.Div(id='power-zones')
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
                                                html.H3("Power split"),
                                                ui_power.get_cycling_power_splits_table(power_splits)
                                            ],
                                            md=12,
                                        )
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.H3("Gradients"),
                                                ui_power.get_cycling_power_gradient_table(gradient_splits)
                                            ],
                                            md=12,
                                        )
                                    ]
                                ),
                            ]
                        ),
                        dcc.Tab(
                            label='Heartrate',
                            children=[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.H3("Recovery heartrate"),
                                                ui_heartrate.get_heartrate_recovery(cycling_activity_stream,
                                                                                    day_heartrate, datetime.strptime(
                                                        cycling_activity[STRAVA_API_KEY_ACTIVITY_START_LOCAL],
                                                        UTC_DATE_FORMAT))
                                            ],
                                            md=12,
                                        )
                                    ]
                                ),
                            ]
                        ),
                        dcc.Tab(
                            label='Sleep',
                            children=[
                                dbc.Container(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.H3("Sleep"),
                                                    ],
                                                    md=12,
                                                )
                                            ]
                                        ),
                                        *ui_sleep.get_detailed_sleep_graph(sleep)
                                    ]
                                )
                            ]
                        )
                    ]
                ),
            ],
            className="mt-4",
            fluid=True
        )

    else:
        return html.Div([
            html.H3('Auth'),
            html.P('An error occurred')
        ])


@app.callback(Output('power-zones', 'children'), [Input('ftp', "value")], [State('url', 'search')])
def number_render(ftp, query):
    activity_id = common.get_parameter(query, 'activity')[0]

    # Get the activity stream that we serialised in the session
    activity_stream = json.loads(session.get(f'{SESSION_STRAVA_ACTIVITY_STREAMS_KEY}-{activity_id}'))
    power_summary = api_strava.get_cycling_power_summary(activity_stream, int(ftp))
    return ui_power.get_cycling_power_summary_table(power_summary)


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
    elif pathname == URL_LOGOUT:
        logout()
        return login()
    else:
        return html.H1('404')


if __name__ == '__main__':
    host = '127.0.0.1'
    debug = True
    port = 5000
    if 'server' in config:
        host = config['server']['host'] if 'host' in config['server'] else host
        debug = config['server']['debug'] if 'debug' in config['server'] else debug
        port = config['server']['port'] if 'port' in config['server'] else port

    app.run_server(host=host, debug=debug, port=port)
