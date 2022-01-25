import requests
import shared
import json

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
    url = "https://wiki.openstreetmap.org/w/api.php?action=query&format=json&list=querypage&utf8=1&qppage=Uncategorizedimages&qplimit=" + str(group_count) + "&qpoffset=" + str(offset)
    response = requests.post(url)
    #print(json.dumps(response.json(), indent=4))
    file_list = response.json()['query']['querypage']['results']
    returned = []
    for file in file_list:
        returned.append(file["title"])
    return returned

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
    #print()
    #print("------------------------")
    #print(upload_history)
    #print(len(upload_history))
    #print("------------------------")
    #print()
    if(len(upload_history) > 1):
        print("multiple uploads, lets skip for now as complicated")
        return None
    return upload_history[0]['user']
