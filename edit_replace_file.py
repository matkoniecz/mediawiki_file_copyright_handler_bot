import mediawiki_api_query
import shared
import mediawiki_api_login_and_editing

import datetime
import random
import time
import webbrowser

def selftest():
    pass

def main():
    selftest()
    session = shared.create_login_session()
    # https://wiki.openstreetmap.org/wiki/File:Canopy-action.jpg is not working well...
    old_file = "File:Canopy-action.jpg"
    new_file = "File:Trolley in PandaPark.JPG"
    edit_summary = "replace file wih one that has more clear legal situation, is on Wikimedia commons and is of a better quality"
    old_file = old_file.replace("_", " ")
    new_file = new_file.replace("_", " ")
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        if "User:Mateusz Konieczny/" in page_title:
            continue
        print("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"))
        data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        text = data["page_text"]
        for main_form in [old_file, old_file.replace(" ", "_")]:
            for form in [
                {'from': main_form,
                'to': new_file,
                'description': 'basic form'
                },
                {'from': main_form.replace("File:", "Image:"),
                'to': new_file,
                'description': 'basic form (Image: prefixed, changed to standard)'
                },
                {'from': main_form.replace("File:", ""),
                'to': new_file.replace("File:", ""),
                'description': 'used in template or mentioned'
                },
            ]:
                if form['from'] in data["page_text"]:
                    print("FOUND, as", form['description'], "-", form['from'])
                    text = text.replace(form['from'], form['to'])
        if text != data["page_text"]:
            shared.edit_page_and_show_diff(session, page_title, text, edit_summary, data['rev_id'], data['timestamp'])
            time.sleep(random.randrange(30, 60))
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        shared.null_edit(session, page_title)

    webbrowser.open(shared.osm_wiki_page_link(old_file), new=2)
    print("{{delete|uses replaced with Wikimedia commons alternative, this file is not needed anymore. And it has severe licensing issues.}}")

main()