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
    if session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None) is None:
        config = yaml.safe_load(open("config.yml"))
        client_id = config['strava']['client_id']
        client_secret = config['strava']['client_secret']

        # Get the code from the permission request response
        code = common.get_parameter(query, 'code')

        # Get an authorisation token
        endpoint = "https://www.strava.com/api/v3/oauth/token"
        data = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'authorization_code',
                'code': code}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # Store the time we made the request so we know how long the access token will last for
        request_date = datetime.now()

        output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

        if 'access_token' in output:
            session[SESSION_STRAVA_ACCESS_TOKEN_KEY] = output['access_token']
            session[SESSION_STRAVA_REFRESH_TOKEN_KEY] = output['refresh_token']
            session[SESSION_STRAVA_EXPIRES_KEY] = request_date + timedelta(seconds=output['expires_in'])

            # Access token saved to session for subsequent calls - success
            return True

        # We failed to get an access token for some reason
        # TODO Add some proper error handling here
        return False

    # If we already have an access token then there's no need to look again for one
    return True


def refresh_access_token():
    refresh_token = session.get(SESSION_STRAVA_REFRESH_TOKEN_KEY, None)
    config = yaml.safe_load(open("config.yml"))
    client_id = config['strava']['client_id']
    client_secret = config['strava']['client_secret']

    if refresh_token is not None:
        endpoint = "https://www.strava.com/api/v3/oauth/token"
        data = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'refresh_token',
                'refresh_token': refresh_token}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # Store the time we made the request so we know how long the access token will last for
        request_date = datetime.now()

        output = json.loads(requests.post(endpoint, data=data, headers=headers).text)

        if 'access_token' in output:
            session[SESSION_STRAVA_ACCESS_TOKEN_KEY] = output['access_token']
            session[SESSION_STRAVA_REFRESH_TOKEN_KEY] = output['refresh_token']
            session[SESSION_STRAVA_EXPIRES_KEY] = request_date + timedelta(seconds=output['expires_in'])


def has_valid_access_token():
    # Checks to see whether we have an access token and it hasn't expired yet
    if session.get(SESSION_STRAVA_ACCESS_TOKEN_KEY, None) is not None:
        expires = session.get(SESSION_STRAVA_EXPIRES_KEY, None)
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
