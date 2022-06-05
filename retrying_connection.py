import requests
import time

def get(url, params={}, headers=None, session=None):
    try:
        if headers != None:
            if session == None:
                return requests.get(url=url, params=params, headers=headers, timeout=120)
            else:
                return session.get(url=url, params=params, headers=headers, timeout=120)
        else:
            if session == None:
                return requests.get(url=url, params=params, timeout=120)
            else:
                return session.get(url=url, params=params, timeout=120)
    except requests.exceptions.ConnectionError as e:
        print("requests.exceptions.ConnectionError")
        print(e)
        print(session)
        print(url)
        print(params)
        print(headers)
        print("sleeping and retrying, WTF")
        time.sleep(60)
        return get(url, params, headers, session)
    except requests.exceptions.ReadTimeout as e:
        print(requests.exceptions.ReadTimeout)
        time.sleep(60)
        return get(url, params, headers, session)

def post(url, params={}, headers=None, session=None):
    try:
        if headers != None:
            if session == None:
                return requests.post(url=url, data=params, headers=headers, timeout=120)
            else:
                return session.post(url=url, data=params, headers=headers, timeout=120)
        else:
            if session == None:
                return requests.post(url=url, data=params, timeout=120)
            else:
                return session.post(url=url, data=params, timeout=120)
    except requests.exceptions.ConnectionError as e:
        print("requests.exceptions.ConnectionError")
        print(e)
        print(session)
        print(url)
        print(params)
        print(headers)
        print("sleeping and retrying, WTF")
        time.sleep(60)
        return post(url, params, headers, session)
    except requests.exceptions.ReadTimeout as e:
        print(requests.exceptions.ReadTimeout)
        time.sleep(60)
        return post(url, params, headers, session)

