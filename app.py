import dash
import dash_core_components as dcc
import dash_html_components as html
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
import helpers.common as common
import helpers.auth.strava_auth as auth_strava
import helpers.auth.fitbit_auth as auth_fitbit
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

    buttons = [
        dbc.Row(
            [
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
                    ],
                    md=6,
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
                    ],
                    md=6,
                )
            ]
        )
    ]

    if auth_fitbit.ensure_valid_access_token() and auth_strava.ensure_valid_access_token():
        buttons.append(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Button('Dashboard', href=URL_DASHBOARD, color='primary', className='mr-1', block=True),
                        ]
                    )
                ]
            )
        )

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
            *buttons
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

        body_composition = api_fitbit.get_weight(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT))
        day_heartrate = api_fitbit.get_heart_rate_detailed(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT), '1sec')
        sleep = api_fitbit.get_sleep_history(fitbit_access_token, datetime.strptime(cycling_activity['start_date_local'], UTC_DATE_FORMAT) + timedelta(days=1), 1)

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
                                html.H2(datetime.strptime(cycling_activity[STRAVA_API_KEY_ACTIVITY_START_LOCAL], UTC_DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)),
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
                                                html.H3("Summary"),
                                                ui_strava.get_cycling_summary_table(cycling_activity)
                                            ],
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
                                                html.H3("Maximum power"),
                                                ui_power.get_cycling_average_power_table(power_averages, body_composition)
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
                                                        cycling_activity[STRAVA_API_KEY_ACTIVITY_START],
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
        )

    else:
        return html.Div([
            html.H3('Auth'),
            html.P('An error occurred')
        ])


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
