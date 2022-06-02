#!/usr/bin/python3

import password_data
import requests
import simplejson

import time

class NoEditPermissionException(Exception):
   # likely logged out
   pass

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
    if is_error_here(DATA):
        raise
    return S

def is_rate_limit_error_here(DATA):
    #{'error': {'code': 'ratelimited', 'info': 'As an anti-abuse measure, you are limited from performing this action too many times in a short space of time, and you have exceeded this limit. Please try again in a few minutes.', '*': 'See https://wiki.openstreetmap.org/w/api.php for API usage. Subscribe to the mediawiki-api-announce mailing list at &lt;https://lists.wikimedia.org/mailman/listinfo/mediawiki-api-announce&gt; for notice of API deprecations and breaking changes.'}}
    if 'error' in DATA:
        if DATA['error']['code'] == 'ratelimited':
            return True
    return False

def is_logged_out_error_here(DATA):
    #{'error': {'code': 'permissiondenied', 'info': 'The action you have requested is limited to users in the group: [[Wiki:Users|Users]].' ...
    # triggered by attempting to edit
    #
    # notloggedin is triggered when attempting to watchlist
    if 'error' in DATA:
        if DATA['error']['code'] in ['notloggedin', 'permissiondenied']:
            return True
    return False

def is_error_here(DATA):
    if 'error' in DATA:
        return True
    return False


def create_page(S, page_title, page_text, edit_summary, URL="https://wiki.openstreetmap.org/w/api.php", sleep_time=0.4, mark_as_bot_edit=False):
    # Step 4: POST request to edit a page
    params = {
        "action": "edit",
        "title": page_title,
        "token": obtain_csrf_token(S, URL),
        "format": "json",
        "text": page_text,
        "summary": edit_summary,
        "createonly": "1",
    }
    if mark_as_bot_edit:
        params["bot"] = "yes"

    R = S.post(URL, data=params)
    DATA = R.json()

    print(DATA)
    if is_logged_out_error_here(DATA):
        raise NoEditPermissionException("likely automatically logged out")
    if is_rate_limit_error_here(DATA):
        print("rate limit error, will retry after sleeeping")
        time.sleep(60)
        print("rate limit error, sleep finished, will retry")
        create_page(S, page_title, page_text, edit_summary, URL)
    if is_error_here(DATA):
        raise
    time.sleep(sleep_time)

def edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, URL="https://wiki.openstreetmap.org/w/api.php", sleep_time=0.4, mark_as_bot_edit=False):
    # https://www.mediawiki.org/wiki/API:Edit
    # Step 4: POST request to edit a page
    params = {
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
    if mark_as_bot_edit:
        params["bot"] = "yes"

    try:
        R = S.post(URL, data=params)
    except requests.exceptions.ConnectionError as e:
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print("requests.exceptions.ConnectionError")
        print(e)
        print(S)
        print(page_title)
        print(page_text)
        print(edit_summary)
        print(rev_id)
        print(timestamp)
        print(URL)
        print(sleep_time)
        print(mark_as_bot_edit)
        print("sleeping and retrying, WTF")
        time.sleep(60)
        return edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, URL, sleep_time, mark_as_bot_edit)
    DATA = R.json()

    print(DATA)
    if is_logged_out_error_here(DATA):
        raise NoEditPermissionException("likely automatically logged out")
    if is_rate_limit_error_here(DATA):
        print("rate limit error, will retry after sleeeping")
        time.sleep(60)
        print("rate limit error, sleep finished, will retry")
        edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, URL)
    if is_error_here(DATA):
        raise
    time.sleep(sleep_time)

def watchlist_page(S, page_title, URL="https://wiki.openstreetmap.org/w/api.php"):
    # https://www.mediawiki.org/wiki/API:Watch

    PARAMS_FOR_TOKEN = {
        "action": "query",
        "meta": "tokens",
        "type": "watch",
        "format": "json"
    }
    R = S.get(url=URL, params=PARAMS_FOR_TOKEN)
    DATA = R.json()
    CSRF_TOKEN = DATA["query"]["tokens"]["watchtoken"]

    PARAMS = {
        "action": "watch",
        "titles": page_title,
        "format": "json",
        "token": CSRF_TOKEN,
    }

    R = S.post(URL, data=PARAMS)
    DATA = R.json()
    if is_logged_out_error_here(DATA):
        raise NoEditPermissionException("likely automatically logged out")
    elif is_error_here(DATA):
        print(R)
        print(R.status_code)
        print(R.content)
        print(R.text)
        raise
    if is_error_here(DATA):
        raise

def obtain_csrf_token(S, URL):
    try:
        # CSRF == Cross Site Request Forgery
        # AKA, additional complexity because some people are evil

        # GET request to fetch CSRF token
        PARAMS_2 = {
            "action": "query",
            "meta": "tokens",
            "format": "json"
        }

        R = S.get(url=URL, params=PARAMS_2)
        try:
            DATA = R.json()
            if is_error_here(DATA):
                raise
            CSRF_TOKEN = DATA['query']['tokens']['csrftoken']
            return CSRF_TOKEN
        except simplejson.errors.JSONDecodeError:
            print(R)
            print(R.status_code)
            print(R.content)
            print(R.text)
            raise
    except requests.exceptions.ConnectionError as e:
        print("ERROR HAPPENED")
        print(e)
        time.sleep(120)
        return obtain_csrf_token(S, URL)

def obtain_login_token(S, URL):
    # Retrieve login token first
    PARAMS_0 = {
        'action':"query",
        'meta':"tokens",
        'type':"login",
        'format':"json"
    }

    R = S.get(url=URL, params=PARAMS_0)
    try:
        DATA = R.json()
        if is_error_here(DATA):
            raise
        LOGIN_TOKEN = DATA['query']['tokens']['logintoken']
        return LOGIN_TOKEN
    except simplejson.errors.JSONDecodeError:
        print(R)
        print(R.status_code)
        print(R.content)
        print(R.text)
        raise Exception("JSON decoding failed while obtaining login token")
        
