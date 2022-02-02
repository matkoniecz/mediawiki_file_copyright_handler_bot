import mediawiki_api_login_and_editing
import mediawiki_api_query
import urllib.parse
import webbrowser

import password_data

def create_login_session():
    login_data = password_data.api_login_data()
    password = login_data['password']
    username = login_data['user']
    session = mediawiki_api_login_and_editing.login_and_create_session(username, password)
    return session

def show_latest_diff_on_page(page_title):
    data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    difflink = osm_wiki_diff_link(data['parent_id'], data['rev_id'])
    webbrowser.open(difflink, new=2)

def edit_page_and_show_diff(S, page_title, page_text, edit_summary, rev_id, timestamp):
    returned = edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp)
    show_latest_diff_on_page(page_title)
    return returned

def edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp):
     return mediawiki_api_login_and_editing.edit_page(S, page_title, page_text, edit_summary, rev_id, timestamp)

def create_page(S, page_title, page_text, edit_summary):
    return mediawiki_api_login_and_editing.create_page(S, page_title, page_text, edit_summary)

def create_page_and_show_diff(S, page_title, page_text, edit_summary):
    returned = mediawiki_api_login_and_editing.create_page(S, page_title, page_text, edit_summary)
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
    while index < len(generated_summary_parts):
        output += "|-\n"
        output += "| "
        row_data = ""
        for i in range(columns):
            if row_data != "":
                row_data += " || "
            if index == break_after:
                row_data += "BREAK requested after " + str(break_after) + " images"
            else:
                if index < len(generated_summary_parts):
                    row_data += generated_summary_parts[index]
            index += 1 
        output += row_data
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


def pause():
    print("press enter (any key?) to continue")
    input()

