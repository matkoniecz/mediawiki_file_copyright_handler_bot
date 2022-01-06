import json

def api_login_data():
    with open('secret.json') as f:
        data = json.load(f)
        username = data['api_password']['username']
        password = data['api_password']['password']
        return {'user': username, 'password': password}
    # https://wiki.openstreetmap.org/wiki/Special:BotPasswords

def username():
    # https://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(technical_restrictions)#Restrictions_on_usernames
    with open('secret.json') as f:
        data = json.load(f)
        username = data['api_password']['username']
        if "@" in username:
            return username.split("@")[0]
        else:
            return username
