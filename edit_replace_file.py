import mediawiki_api_query
import shared
import mediawiki_api_login_and_editing

import datetime
import random
import time
import webbrowser
import re

def selftest():
    if extract_replacement_filename_from_templated_page("{{Superseded by Commons|File:Baghdad International Airport (October 2003).jpg}}", "test") != "File:Baghdad International Airport (October 2003).jpg":
        raise
    page = """This work is in the public domain in the United States because it is a work of the United States Federal Government under the terms of Title 17, Chapter 1, Section 105 of the US Code. See Copyright.

Note: This only applies to works of the Federal Government and not to the work of any individual U.S. state, territory, commonwealth, county, municipality, or any other subdivision.

[[Category:Outdoor OSM data Example]]
{{Superseded by Commons|File:Baghdad International Airport (October 2003).jpg}}
"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Baghdad International Airport (October 2003).jpg":
        raise

def main():
    selftest()

    migrate_file("File:Isolated Danger Buoy.png", "File:Buoy marking the wreck of HMS Natal - geograph.org.uk - 1280172.jpg", ["higher quality", "proper licensing info"])
    # https://wiki.openstreetmap.org/wiki/Category:Media_without_a_license_-_author_notified_October_2021

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

def extract_replacement_filename_from_templated_page(text, page_title):
    p = re.compile('\{\{Superseded by Commons\|([^\}]+)\}\}')
    m = p.search(text)
    if m == None:
        print("failed on", page_title)
        print(text)
    return m.group(1)

def try_to_migrate_as_superseded_by_commons_template_indicated(session, page_title):
    for used in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        print("IN USE!")
    test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    if test_page == None:
        print(page_title)
    if has_tricky_templating_situation(test_page['page_text']):
        return

    replacement = extract_replacement_filename_from_templated_page(test_page['page_text'], page_title)

    if file_used_and_only_on_pages_where_no_editing_allowed(page_title):
        print("used only on pages exempt from editing like talk pages")
        print()
        return

    webbrowser.open("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"), new=2)
    webbrowser.open("https://commons.wikimedia.org/wiki/"+replacement.replace(" ", "_"), new=2)
    shared.pause()
    migrate_file(page_title, replacement, [])


def run_hardcoded_file_migrations():
    migrate_file("File:800px-Luge Schlucht.jpg", "File:Luge Schlucht.jpg", ["higher quality", "proper licensing info"])
    migrate_file("File:120px-Zeichen 250.svg.png", "File:Zeichen 250 - Verbot für Fahrzeuge aller Art, StVO 1970.svg", ["higher quality", "proper licensing info"])

    migrate_file("File:Symbol E10.png", "File:Balken-gruen.png", [])
    migrate_file("File:Blue bar.png", "File:Balken-blau.png", []) # lowercasing MESS
    
def skip_editing_on_this_page(page_title):
    if "User:Mateusz Konieczny/" in page_title:
        return True
    if "talk" in page_title.lower():
        print("skipping", page_title, "as talk page")
        return True
    return False

def file_used_and_only_on_pages_where_no_editing_allowed(page_title):
    used = False
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        used = True
        if skip_editing_on_this_page(page_title):
            continue
        return False
    return used

def migrate_file(old_file, new_file, reasons_list):
    session = shared.create_login_session()
    edit_summary = "file replacement ( " + old_file + " -> " + new_file + " ). It is on Wikimedia commons"
    edit_summary = (", ").join([edit_summary] + reasons_list)
    edit_summary += "."
    print(edit_summary)
    old_file = old_file.replace("_", " ")
    new_file = new_file.replace("_", " ")

    if file_used_and_only_on_pages_where_no_editing_allowed(old_file):
        print("In use only on pages skipped from editing")
        return

    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        if skip_editing_on_this_page(page_title):
            continue
        print("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"))
        data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        text = data["page_text"]
        unsafe_changes = False
        for main_form in [old_file, old_file.replace(" ", "_")]:
            for form in valid_image_transforms(main_form, new_file):
                if form['from'] in text:
                    print("FOUND, as", form['description'], "-", form['from'])
                    text = text.replace(form['from'], form['to'])
                    if form['safe'] == False:
                        unsafe_changes = True
                from_form = form['from'].replace("File:", "Image:")
                description = "(in Image: variant)"
                if from_form in text:
                    print("FOUND " + description + ", as", form['description'], "-", from_form)
                    text = text.replace(from_form, form['to'])
                    if form['safe'] == False:
                        unsafe_changes = True
                        
        if text != data["page_text"]:
            shared.edit_page_and_show_diff(session, page_title, text, edit_summary, data['rev_id'], data['timestamp'])
            time.sleep(random.randrange(30, 60))
            if unsafe_changes:
                print("EDIT COULD BE UNSAFE, VERIFY PLS")
                shared.pause()
        else:
            print("Failed to find this file within " + page_title + " - length of page was", len(text))
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        shared.null_edit(session, page_title)

    still_used = False
    for page_title in mediawiki_api_query.pages_where_file_is_used_as_image(old_file):
        still_used = True
        break

    data = mediawiki_api_query.download_page_text_with_revision_data(old_file)
    text = data["page_text"]
    if "{{delete|" in text or still_used:
        webbrowser.open(shared.osm_wiki_page_link(old_file), new=2)
    else:
        if text.strip() != "":
            text += "\n"
        delete_request = "{{delete|uses replaced with Wikimedia commons alternative, this file is not needed anymore. And it has licensing issues.}}"
        text += delete_request
        edit_summary = delete_request
        shared.edit_page_and_show_diff(session, old_file, text, edit_summary, data['rev_id'], data['timestamp'])

def valid_image_transforms(main_form, new_file):
    returned = [
        {'from': "[[" + main_form + "|",
        'to': "[[" + new_file + "|",
        'description': 'basic form, safe replacement',
        'safe': True,
        },
    ]
    for pre in range(0, 10):
        for post in range(0, 3):
            # infoboxes with varying space count
            returned.append(
                {'from': main_form.replace("image" + (" " * pre) + "=" + (" " * post) + "File:", ""),
                'to': new_file.replace("image = File:", ""),
                'description': 'used in template (quite safe)',
                'safe': True,
                }
            )
    returned = returned + [
        {'from': main_form,
        'to': new_file,
        'description': 'basic form',
        'safe': False,
        },
        {'from': main_form.replace("File:", ""),
        'to': new_file.replace("File:", ""),
        'description': 'used in template or mentioned',
        'safe': False,
        },
    ]
    return returned

main()
