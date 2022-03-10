import mediawiki_api_query
import shared
import mediawiki_api_login_and_editing

import datetime
import random
import time
import webbrowser
import re

def selftest():
    pass

def main():
    selftest()

    #migrate_file("File:SafeWaterBuoy.png", "File:The Fairway Buoy, Tremadog Bay - geograph.org.uk - 120195 - cropped to buoy.png", ["higher quality", "proper licensing info"])

    
    # https://wiki.openstreetmap.org/wiki/File:Canopy-action.jpg is not working well...

    session = shared.create_login_session()
    index = 0
    for page_title in mediawiki_api_query.pages_from_category("Category:Image superseded by Wikimedia Commons"):
        index += 1
        print(page_title, index)
        try_to_migrate_as_superseded_by_commons_template_indicated(session, page_title)
        mark_file_as_migrated(session, page_title)
    run_hardcoded_file_migrations()

def mark_file_as_migrated(session, page_title):
    not_used = True
    for used in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        not_used = False
        print("still used on", used)
        break
    if not_used:
        print(page_title, "is not used")
        test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)

        if has_tricky_templating_situation(test_page['page_text']):
            return

        text = test_page['page_text'] + "\n" + "{{delete|unused duplicate of Wikimedia Commons file}}"
        shared.edit_page_and_show_diff(session, page_title, text, "request deletion of duplicate", test_page['rev_id'], test_page['timestamp'])

def has_tricky_templating_situation(page_text):
    if page_text.count("{") != 2 or page_text.count("}") != 2:
        print("complex situation, skipping")
        return True
    if page_text.count("|") != 1:
        print("complex situation, skipping")
        return True
    return False

def try_to_migrate_as_superseded_by_commons_template_indicated(session, page_title):
    for used in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        print("IN USE!")
    test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)

    if has_tricky_templating_situation(test_page['page_text']):
        return

    p = re.compile('\{\{Superseded by Commons\|([^\}]+)\}\}')
    m = p.match(test_page['page_text'])
    replacement = m.group(1)

    webbrowser.open("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"), new=2)
    webbrowser.open("https://commons.wikimedia.org/wiki/"+replacement.replace(" ", "_"), new=2)
    shared.pause()
    migrate_file(page_title, replacement, [])


def run_hardcoded_file_migrations():
    migrate_file("File:800px-Luge Schlucht.jpg", "File:Luge Schlucht.jpg", ["higher quality", "proper licensing info"])
    migrate_file("File:120px-Zeichen 250.svg.png", "File:Zeichen 250 - Verbot für Fahrzeuge aller Art, StVO 1970.svg", ["higher quality", "proper licensing info"])

    migrate_file("File:Symbol E10.png", "File:Balken-gruen.png", [])
    migrate_file("File:Blue bar.png", "File:Balken-blau.png", []) # lowercasing MESS
    

def migrate_file(old_file, new_file, reasons_list):
    session = shared.create_login_session()
    edit_summary = "file replacement ( " + old_file + " -> " + new_file + " ). It is on Wikimedia commons"
    edit_summary = (", ").join([edit_summary] + reasons_list)
    edit_summary += "."
    print(edit_summary)
    old_file = old_file.replace("_", " ")
    new_file = new_file.replace("_", " ")
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        if "User:Mateusz Konieczny/" in page_title:
            continue
        if "talk" in page_title:
            print("skipping", page_title, "as talk page")
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
        else:
            print("Failed to find this file within " + page_title + " - length of page was", len(text))
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        shared.null_edit(session, page_title)

    webbrowser.open(shared.osm_wiki_page_link(old_file), new=2)
    print("{{delete|uses replaced with Wikimedia commons alternative, this file is not needed anymore. And it has severe licensing issues.}}")

main()