from flask import Flask, render_template, request
import requests
import json
import base64
import yaml


app = Flask(__name__)

@app.route("/")
@app.route("/login")
def index():
    return render_template('login.html')

@app.route("/auth")
def auth():
    # Get the client ID and secret from the config file
    config = yaml.safe_load(open("config.yml"))
    client_id = config['fitbit']['client_id']
    client_secret = config['fitbit']['client_secret']

    # Encode the client ID and secret for authentication when requesting a token
    auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

    print(f"Basic {auth}")

    # Get the code from the permission request response
    code = request.args.get('code')

    # Get an authorisation token
    endpoint = "https://api.fitbit.com/oauth2/token"
    data = {'clientId': '22BCBG', 'grant_type': 'authorization_code', 'redirect_uri': 'http://127.0.0.1:5000/auth', 'code': code}
    headers = {"Authorization": f"Basic {auth}",
               'Content-Type': 'application/x-www-form-urlencoded'}

    output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

    print(output)

    access_token = output['access_token']

    # Get some data
    endpoint = "https://api.fitbit.com/1/user/-/profile.json"
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get(endpoint, headers=headers).json()


if __name__ == "__main__":
    app.run()
