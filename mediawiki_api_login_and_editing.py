#!/usr/bin/python3

import password_data
import requests

"""
    login.py

    MediaWiki API Demos
    Demo of `Login` module: Sending post request to login
    MIT license
    https://www.mediawiki.org/wiki/API:Login#Python
    https://wiki.openstreetmap.org/wiki/Special:BotPasswords
"""
def login_and_create_session(username, password, URL="https://wiki.openstreetmap.org/w/api.php"):
    S = requests.Session()
    LOGIN_TOKEN = obtain_login_token(S, URL)

    # Send a post request to login. Using the main account for login is not
    # supported. Obtain credentials via Special:BotPasswords
    # (https://www.mediawiki.org/wiki/Special:BotPasswords) for lgname & lgpassword

    return login_with_login_token(S, username, password, LOGIN_TOKEN, URL)

def login_with_login_token(S, username, password, LOGIN_TOKEN, URL):
    PARAMS_1 = {
        'action':"login",
        'lgname': username,
        'lgpassword': password,
        'lgtoken':LOGIN_TOKEN,
        'format':"json"
    }

    R = S.post(URL, data=PARAMS_1)
    DATA = R.json()
    # TODO - handle failure?
    return S

def create_page(S, page_title, page_text, edit_summary, URL="https://wiki.openstreetmap.org/w/api.php"):
    # Step 4: POST request to edit a page
    PARAMS_3 = {
        "action": "edit",
        "title": page_title,
        "token": obtain_csrf_token(S, URL),
        "format": "json",
        "text": page_text,
        "summary": edit_summary,
        "createonly": "1",
    }

    R = S.post(URL, data=PARAMS_3)
    DATA = R.json()

    print(DATA)

def edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, URL="https://wiki.openstreetmap.org/w/api.php"):
    # Step 4: POST request to edit a page
    PARAMS_3 = {
        "action": "edit",
        "title": page_title,
        "token": obtain_csrf_token(S, URL),
        "format": "json",
        "text": page_text,
        "summary": edit_summary,
        "baserevid": rev_id,
        "basetimestamp": timestamp,
        "nocreate": "1",
    }

    R = S.post(URL, data=PARAMS_3)
    DATA = R.json()

    print(DATA)

def obtain_csrf_token(S, URL):
    # CSRF == Cross Site Request Forgery
    # AKA, additional complexity because some people are evil

    # GET request to fetch CSRF token
    PARAMS_2 = {
        "action": "query",
        "meta": "tokens",
        "format": "json"
    }

    R = S.get(url=URL, params=PARAMS_2)
    DATA = R.json()

    CSRF_TOKEN = DATA['query']['tokens']['csrftoken']
    return CSRF_TOKEN

def obtain_login_token(S, URL):
    # Retrieve login token first
    PARAMS_0 = {
        'action':"query",
        'meta':"tokens",
        'type':"login",
        'format':"json"
    }

    R = S.get(url=URL, params=PARAMS_0)
    DATA = R.json()

    LOGIN_TOKEN = DATA['query']['tokens']['logintoken']
    return LOGIN_TOKEN
