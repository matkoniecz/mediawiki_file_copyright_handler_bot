import requests
import shared
import json
import datetime

def file_upload_history(file, URL="https://wiki.openstreetmap.org/w/api.php"):
    call_url = URL + "?action=query&titles=" + shared.escape_parameter(file) + "&prop=imageinfo&iilimit=50&format=json"
    response = requests.post(call_url, headers={'Content-type': 'text'})
    key = list(response.json()['query']['pages'].keys())[0]
    upload_history = response.json()['query']['pages'][key]
    if "imageinfo" not in upload_history:
        print(call_url)
        print(json.dumps(response.json(), indent=4))
        print(json.dumps(upload_history, indent=4))
        if 'query' not in upload_history:
            return None # https://wiki.openstreetmap.org/wiki/Talk:Wiki#Ghost_file - what is going on?
            raise Exception("unexpected missing query in data")
        print(json.dumps(upload_history['query']['pages'], indent=4))
        print(list(upload_history['query']['pages'].keys())[0])
    return upload_history["imageinfo"]

def file_upload_history_without_broken_uploads(file, URL="https://wiki.openstreetmap.org/w/api.php"):
    data = file_upload_history(file, URL)
    returned = []
    for entry in data:
        if "filemissing" not in entry:
            returned.append(entry)
    return returned

def debug_api():
    files = ["File:20170907 172429.jpg", "File:Global Relative Share Pie Chart.png"]
    for file in files:
        file = file.replace(" ", "%20")
        # versions of file itself
        url = "https://wiki.openstreetmap.org/w/api.php?action=query&titles=" + shared.escape_parameter(file) + "&prop=imageinfo&iilimit=50&format=json"
        response = requests.post(url) # , data=data
        print(json.dumps(response.json(), indent=4))
        # versions of file page
        url = "https://wiki.openstreetmap.org/w/api.php?action=query&prop=revisions&titles=" + shared.escape_parameter(file) + "&rvlimit=5&rvprop=timestamp|user|comment&format=json"
        response = requests.post(url) # , data=data
        print(response)
        print(json.dumps(response.json(), indent=4))
        print()
        print("00000000000000000000000000")
        print()

def pages_from_category(category):
    # maybe will limit and not return all... to investigate...
    returned = []
    """
    category should be something like Category:name
    """
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&generator=categorymembers&gcmtitle=" + shared.escape_parameter(category) + "&prop=categories&cllimit=max&gcmlimit=max&format=json"
    response = requests.post(url)
    #print(json.dumps(response.json(), indent=4))
    #print(json.dumps(response.json()["query"]["pages"], indent=4))
    data = response.json()["query"]["pages"]
    keys = response.json()["query"]["pages"].keys()
    for key in keys:
        returned.append(data[key]["title"])
    #print(returned)
    return returned
    # https://stackoverflow.com/questions/28224312/mediawiki-api-how-do-i-list-all-pages-of-a-category-and-for-each-page-show-all

def uncategorized_images(offset, group_count):
    # example:
    # https://wiki.openstreetmap.org/w/api.php?action=query&format=json&list=querypage&utf8=1&qppage=Uncategorizedimages&qplimit=10&qpoffset=0
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&format=json&list=querypage&utf8=1&qppage=Uncategorizedimages&qplimit=" + str(group_count) + "&qpoffset=" + str(offset)
    response = requests.post(url)
    #print(json.dumps(response.json(), indent=4))
    file_list = response.json()['query']['querypage']['results']
    returned = []
    for file in file_list:
        returned.append(file["title"])
    return returned

def images_by_date(date_string):
    # https://www.mediawiki.org/wiki/API:Allimages#Example_2:_Get_images_by_date
    S = requests.Session()

    URL = "https://wiki.openstreetmap.org/w/api.php"

    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "allimages",
        "aisort": "timestamp",
        "aidir": "newer", # older
        "aistart": date_string,
        "ailimit": 500,
    }

    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()

    IMAGES = DATA["query"]["allimages"]

    returned = []
    for img in IMAGES:
        returned.append(img["title"])
    return returned

def uploads_by_username_generator(user):
    continue_code = None
    print("uploads_by_username_generator warning: deleted/moved images will be likely shown under original names")
    already_shown = []
    while True:
        user = user.replace(" ", "%20")
        url = "https://wiki.openstreetmap.org/w/api.php?action=query&list=logevents&letype=upload&lelimit=500&leuser=" + user + "&format=json"
        if continue_code != None:
            url += "&lecontinue=" + continue_code
        response = requests.post(url)
        #print(json.dumps(response.json(), indent=4))
        #print(url)
        file_list = response.json()['query']['logevents']
        returned = []
        for file in file_list:
            if file not in already_shown:
                already_shown.append(file) # user can upload multiple times to a single file
                yield file["title"]
        if "continue" in response.json():
            #print(response.json()["continue"])
            continue_code = response.json()["continue"]["lecontinue"]
        else:
            break

def download_page_text_with_revision_data(page_title):
    # https://wiki.openstreetmap.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=content|timestamp|ids&format=json&titles=Sandbox
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=content|timestamp|ids&format=json&titles=" + shared.escape_parameter(page_title)
    response = requests.post(url)
    key = list(response.json()['query']['pages'].keys())[0]
    versions = response.json()['query']['pages'][key]
    if "revisions" not in versions:
        #print([page_title, "does not exist"])
        return None
    page_text = versions['revisions'][0]['*']
    rev_id = versions['revisions'][0]['revid']
    parent_id = versions['revisions'][0]['parentid']
    timestamp = versions['revisions'][0]['timestamp']
    return {'page_title': page_title, 'page_text': page_text, 'rev_id': rev_id, 'parent_id': parent_id, 'timestamp': timestamp}

def download_page_text(page_title):
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&prop=revisions&rvlimit=1&rvprop=content&format=json&titles=" + shared.escape_parameter(page_title)
    response = requests.post(url)
    #print(json.dumps(response.json(), indent=4))
    key = list(response.json()['query']['pages'].keys())[0]
    versions = response.json()['query']['pages'][key]
    if "revisions" not in versions:
        print([page_title, "does not exist"])
        return None
    page_text = versions['revisions'][0]['*']
    #print(page_text)
    return page_text

def pages_where_file_is_used_as_image(page_title):
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&titles=" + shared.escape_parameter(page_title) + "&prop=fileusage&format=json"
    response = requests.post(url)
    #print(json.dumps(response.json(), indent=4))
    key = list(response.json()['query']['pages'].keys())[0]
    entry = response.json()['query']['pages'][key]
    if "fileusage" not in entry:
        return []
    else:
        returned = []
        for use in entry["fileusage"]:
            returned.append(use["title"])
        #print("-=--------------")
        #print(json.dumps(entry["fileusage"], indent=4))
        #print("-=--------------")
        return returned

def is_file_used_as_image(page_title):
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&titles=" + shared.escape_parameter(page_title) + "&prop=fileusage&format=json"
    response = requests.post(url)
    #print(json.dumps(response.json(), indent=4))
    key = list(response.json()['query']['pages'].keys())[0]
    #print("-=--------------")
    #print(json.dumps(response.json(), indent=4))
    #print("-=--------------")
    entry = response.json()['query']['pages'][key]
    return "fileusage" in entry

    # backlinks: https://wiki.openstreetmap.org/w/api.php?action=query&format=json&list=backlinks&bltitle=File:01.Picture.jpg

def get_uploader(page_title):
    """
    returns uploader username
    or returns None if different versions were uploaded by a different people
    """
    upload_history = file_upload_history(page_title)
    return get_uploader_from_file_history(upload_history)

def get_uploader_from_file_history(upload_history):
    #print()
    #print("------------------------")
    #print(upload_history)
    #print(len(upload_history))
    #print("------------------------")
    #print("----UPLOAD HISTORY------")
    #print("------------------------")
    #print()
    
    user = upload_history[0]['user']

    for entry in upload_history:
        if user != entry['user']:
            print("multiple uploads by different people, lets skip for now as complicated")
            return None
    return user

def get_upload_date_from_file_history(upload_history):
    if(len(upload_history) > 1):
        print("multiple uploads, lets skip obtaining upload date for now as complicated")
        return None
    upload_timestamp_string = upload_history[0]['timestamp']
    return parse_mediawiki_time_string(upload_timestamp_string)

def parse_mediawiki_time_string(time_string):
    return datetime.datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%SZ")
