import mediawiki_api_login_and_editing
import mediawiki_api_query
import urllib.parse
import webbrowser
import password_data
import time
import random

def users_dropped_from_regular_processing():
    return [
    "Malcolmh", # many PD-shape images and basically only that - see https://wiki.openstreetmap.org/wiki/User:Mateusz_Konieczny/notify_uploaders/Malcolmh
    "Hoream telenav", # received PM from them
    "!i!", "Bwurst", # many PD-shape/Carto/possibly PD-shape images
    "Marek kleciak", # lost computer access
    "VIPINDAS K", # problematic: copyvios related to OSM
    "Dmgroom", # handle https://wiki.openstreetmap.org/wiki/File:Baghdad-210207.png first
    "Emmanuel BAMA", # handle PD-text like from https://wiki.openstreetmap.org/wiki/User:Mateusz_Konieczny/notify_uploaders/Emmanuel_BAMA
    "Michael Montani", "SimonPoole", # many charts: https://commons.wikimedia.org/wiki/Commons:Village_pump/Copyright#Is_chart_qualifying_for_PD-shape?
    "Bk", "Nordpfeil", "Mateusz Konieczny", # has chart (search fir chart below)
    "Skippern", #PD-shape spam, some more complex (posted on the talk page 2022-01-30)
    "Gkai", # https://wiki.openstreetmap.org/wiki/User:Mateusz_Konieczny/notify_uploaders/Gkai OSM Carto icons ("should be replaced with")
    "Fkv", # mark their image for deletion on or after 2022-09-08 https://wiki.openstreetmap.org/w/index.php?title=File:Kremszwickel_signpost.jpg&oldid=prev&diff=2279417 https://wiki.openstreetmap.org/w/index.php?title=User_talk:Fkv&curid=112308&diff=2279452&oldid=2279273 https://wiki.openstreetmap.org/w/index.php?title=User_talk:Fkv&diff=2279476&oldid=2279452 https://wiki.openstreetmap.org/w/index.php?title=File:Kremszwickel_signpost.jpg&diff=prev&oldid=2279473
    "Ulfm", "Abunai", # murdered - https://wiki.openstreetmap.org/w/index.php?title=User_talk%3AMateusz_Konieczny&type=revision&diff=2282967&oldid=2282571
    "Malenki", # dead - https://wiki.openstreetmap.org/wiki/User_talk:Malenki
    "Bmwiedemann", # tricky https://wiki.openstreetmap.org/wiki/File:Luftbild-2-originalprojektion-unscaled.png
    "Reneman", # most of files are not actually theirs - see descriptions of files, see also https://wiki.openstreetmap.org/wiki/User:Mateusz_Konieczny/notify_uploaders/Reneman
    ]

def create_login_session(index = 'api_password'):
    login_data = password_data.api_login_data(index)
    password = login_data['password']
    username = login_data['user']
    session = mediawiki_api_login_and_editing.login_and_create_session(username, password)
    return session

def show_latest_diff_on_page(page_title):
    if page_title == None:
        raise Exception("None passed as a title")
    data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    difflink = osm_wiki_diff_link(data['parent_id'], data['rev_id'])
    webbrowser.open(difflink, new=2)

def edit_page_and_show_diff(S, page_title, page_text, edit_summary, rev_id, timestamp, sleep_time = None, mark_as_bot_edit=False):
    if sleep_time != None:
        returned = edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, sleep_time, mark_as_bot_edit=mark_as_bot_edit)
    returned = edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, mark_as_bot_edit=mark_as_bot_edit)
    show_latest_diff_on_page(page_title)
    return returned

def edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, sleep_time = None, mark_as_bot_edit=False):
    if S == None:
        raise "Session must not be None"
    if sleep_time != None:
        return mediawiki_api_login_and_editing.edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, sleep_time=sleep_time, mark_as_bot_edit=mark_as_bot_edit)
    return mediawiki_api_login_and_editing.edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp, mark_as_bot_edit=mark_as_bot_edit)

def create_page(S, page_title, page_text, edit_summary, sleep_time = None, mark_as_bot_edit=False):
    if sleep_time != None:
        return mediawiki_api_login_and_editing.create_page(S, page_title, page_text, edit_summary, sleep_time=sleep_time, mark_as_bot_edit=mark_as_bot_edit)
    return mediawiki_api_login_and_editing.create_page(S, page_title, page_text, edit_summary, mark_as_bot_edit=mark_as_bot_edit)

def create_page_and_show_diff(S, page_title, page_text, edit_summary, sleep_time = None, mark_as_bot_edit=False):
    returned = None
    if sleep_time != None:
        returned = mediawiki_api_login_and_editing.create_page(S, page_title, page_text, edit_summary, sleep_time=sleep_time, mark_as_bot_edit=mark_as_bot_edit)
    else:
        returned = mediawiki_api_login_and_editing.create_page(S, page_title, page_text, edit_summary, mark_as_bot_edit=mark_as_bot_edit)
    show_latest_diff_on_page(page_title)
    return returned

def append_to_page(S, page_title, appended, edit_summary):
    data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    page_text = data['page_text'] + appended
    returned = edit_page_and_show_diff(S, page_title, page_text, edit_summary, data['rev_id'], data['timestamp'])
    return returned

def escape_parameter(parameter):
    return urllib.parse.quote(parameter.encode('utf8'))

def make_test_edit(session):
    sandbox = "Sandbox"
    data = mediawiki_api_query.download_page_text_with_revision_data(sandbox)
    edit_page_and_show_diff(session, sandbox, data['page_text'] + "\ntetteteteetteetett", "edit summary", data['rev_id'], data['timestamp'])

def generate_table_showing_image_data_for_review(data, break_after=None):
    """
    data - iterable with dictionaries containing following fields:
    page_title
    page_text
    """
    generated_summary_parts = []
    for entry in data:
        page_title = entry['page_title']
        page_text = entry['page_text']
        upload_timestamp = "unknown upload time"
        if 'upload_time' in entry:
            upload_timestamp = str(entry['upload_time'])
        generated_summary_parts.append("[[" + page_title + "|thumb| ["+ osm_wiki_page_edit_link(page_title) + " (EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT EEEEEEEEEEEEEEEEEEEEEEEDIIIIIIIIIIIIIIIIIIIIIIIIIIIIIT)] [[:" + page_title + "]] text on page: <<nowiki>" + page_text + "</nowiki>> upload timestamp: " + upload_timestamp + "]]\n")
    columns = 3
    output = '{| class="wikitable"\n'
    index = 0
    table_index = 0
    row_data = ""
    while index < len(generated_summary_parts):
        if (table_index % columns) == 0:
            output += row_data
            output += "|-\n"
            output += "| "
            row_data = ""
        if row_data != "":
            row_data += " || "
        if index == break_after and index == table_index:
            row_data += "BREAK requested after " + str(break_after) + " images\n"
            table_index += 1
        else:
            if index < len(generated_summary_parts):
                row_data += generated_summary_parts[index]
            index += 1
            table_index += 1
    if row_data != "":
        output += row_data
        row_data = ""
    output += "\n|}\n"
    return output

def osm_wiki_diff_link(old_page_id, current_page_id):
    url = "https://wiki.openstreetmap.org/wiki/?diff=" + str(current_page_id) + "&oldid=" + str(old_page_id)
    return url

def osm_wiki_page_link(page_name):
    url = "https://wiki.openstreetmap.org/wiki/" + escape_parameter(page_name)
    url = url.replace(" ", "_")
    return url

def osm_wiki_page_edit_link(page_name):
    url = "https://wiki.openstreetmap.org/wiki?title=" + escape_parameter(page_name) + "&action=edit"
    url = url.replace(" ", "_")
    return url

def null_edit(session, page_title):
    test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    text = test_page['page_text']
    edit_page(session, page_title, text, "NULL EDIT", test_page['rev_id'], test_page['timestamp'])

def pause():
    # wait
    print("press enter (any key?) to continue")
    input()

def make_delay_after_edit():
    sleep_time = 0.5
    if random.randrange(1, 100) > 90:
        sleep_time += random.randrange(400, 600) 
    print("make_delay_after_edit (", sleep_time ,") <-start")
    time.sleep(sleep_time)
    print("make_delay_after_edit end->")

def get_uploader_of_file_or_none_if_not_clear(page_title, log_when_returned_none_due_to_multiple_uploaders=True):
    upload_history = mediawiki_api_query.file_upload_history(page_title)
    return get_uploader_from_upload_history_or_none_if_not_clear(upload_history, page_title, log_when_returned_none_due_to_multiple_uploaders)

def get_uploader_from_upload_history_or_none_if_not_clear(upload_history, page_title, log_when_returned_none_due_to_multiple_uploaders):
    if upload_history == None:
        return None # TODO: remove root cause of THAT
    uploader = mediawiki_api_query.get_uploader_from_file_history(upload_history)
    if uploader == None and log_when_returned_none_due_to_multiple_uploaders:
        print("Unable to establish uploader")
        print("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"))
        return None
    return uploader

