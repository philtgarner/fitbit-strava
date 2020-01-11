import base64
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs
import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import yaml

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
login_url = 'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=22BCBG&redirect_uri=http%3A%2F%2F127.0.0.1%3A5000%2Fauth&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
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

def auth(query):
    config = yaml.safe_load(open("config.yml"))
    client_id = config['fitbit']['client_id']
    client_secret = config['fitbit']['client_secret']

    # Encode the client ID and secret for authentication when requesting a token
    auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

    # Get the code from the permission request response
    code = getParameter(query, 'code')

    # Get an authorisation token
    endpoint = "https://api.fitbit.com/oauth2/token"
    data = {'clientId': '22BCBG', 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/auth', 'code': code}
    headers = {"Authorization": f"Basic {auth}",
               'Content-Type': 'application/x-www-form-urlencoded'}

    output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

    # A successful call returns the following data:
    # - access_token
    # - expires_in
    # - refresh_token
    # - scope
    # - user_id
    access_token = output['access_token']

    # Get some data
    endpoint = "https://api.fitbit.com/1/user/-/activities/heart/date/today/30d.json"
    headers = {"Authorization": f"Bearer {access_token}"}

    return html.Div([
        html.H3('Auth'),
        html.Pre(requests.get(endpoint, headers=headers).text)
    ])

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
        return html.Div([
            html.H3('Unknown page')
        ])

if __name__ == '__main__':
    app.run_server(debug=True, port=5000)
