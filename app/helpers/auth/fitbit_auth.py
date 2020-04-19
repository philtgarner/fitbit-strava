from flask import Flask, session
import yaml
import json
import base64
import requests
import redis
from datetime import datetime, timedelta

from helpers.constants import *
import helpers.common as common


def parse_query_for_access_token(query):
    if session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['fitbit']['client_id']
        client_secret = config['fitbit']['client_secret']
        callback_url = config['fitbit']['callback_url']

        # Encode the client ID and secret for authentication when requesting a token
        auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

        # Get the code from the permission request response
        code = common.get_parameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://api.fitbit.com/oauth2/token"
        data = {'clientId': client_id, 'grant_type': 'authorization_code',
                'redirect_uri': callback_url,
                'code': code}
        headers = {"Authorization": f"Basic {auth}",
                   'Content-Type': 'application/x-www-form-urlencoded'}

        # Store the time we made the request so we know how long the access token will last for
        request_date = datetime.now()

        output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

        # A successful call returns the following data:
        # - access_token
        # - expires_in
        # - refresh_token
        # - scope
        # - user_id
        if 'access_token' in output:
            session[SESSION_FITBIT_ACCESS_TOKEN_KEY] = output['access_token']
            session[SESSION_FITBIT_REFRESH_TOKEN_KEY] = output['refresh_token']
            session[SESSION_FITBIT_EXPIRES_KEY] = request_date + timedelta(seconds=output['expires_in'])

            # Access token saved to session for subsequent calls - success
            return True

        # We failed to get an access token for some reason
        # TODO Add some proper error handling here
        return False

    # If we already have an access token then there's no need to look again for one
    return True


def refresh_access_token():
    refresh_token = session.get(SESSION_FITBIT_REFRESH_TOKEN_KEY, None)
    config = yaml.safe_load(open("config.yml"))
    client_id = config['fitbit']['client_id']
    client_secret = config['fitbit']['client_secret']
    # Encode the client ID and secret for authentication when requesting a token
    auth = str(base64.b64encode(bytes(f'{client_id}:{client_secret}', 'utf-8')), "utf-8")

    if refresh_token is not None:
        endpoint = "https://api.fitbit.com/oauth2/token"
        data = {'grant_type': 'refresh_token',
                'refresh_token': refresh_token}
        headers = {"Authorization": f"Basic {auth}",
                   'Content-Type': 'application/x-www-form-urlencoded'}

        # Store the time we made the request so we know how long the access token will last for
        request_date = datetime.now()

        output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

        if 'access_token' in output:
            session[SESSION_FITBIT_ACCESS_TOKEN_KEY] = output['access_token']
            session[SESSION_FITBIT_REFRESH_TOKEN_KEY] = output['refresh_token']
            session[SESSION_FITBIT_EXPIRES_KEY] = request_date + timedelta(seconds=output['expires_in'])


def has_valid_access_token():
    # Checks to see whether we have an access token and it hasn't expired yet
    if session.get(SESSION_FITBIT_ACCESS_TOKEN_KEY, None) is not None:
        expires = session.get(SESSION_FITBIT_EXPIRES_KEY, None)
        if expires is not None and expires > datetime.now():
            return True
    return False


def ensure_valid_access_token():
    # Checks whether we have a valid access token, refreshes it if not
    if has_valid_access_token():
        return True
    else:
        refresh_access_token()
        return has_valid_access_token()
