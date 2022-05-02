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

    only_safe = True
    run_hardcoded_file_migrations(only_safe)
    only_safe = False
    run_hardcoded_file_migrations(only_safe)

    #done!
    #migrate_file("File:Isolated Danger Buoy.png", "File:Buoy marking the wreck of HMS Natal - geograph.org.uk - 1280172.jpg", ["higher quality", "proper licensing info"])
    # https://wiki.openstreetmap.org/wiki/Category:Media_without_a_license_-_author_notified_October_2021

    only_safe = True
    session = shared.create_login_session()
    index = 0
    for page_title in mediawiki_api_query.pages_from_category("Category:Image superseded by Wikimedia Commons"):
        index += 1
        print(page_title, index)
        while True:
            try:
                replacement = try_to_migrate_as_superseded_by_commons_template_indicated(session, page_title, only_safe, sleeping_after_edit=False)
                break
            except mediawiki_api_login_and_editing.NoEditPermissionException:
                # Recreate session, may be needed after long processing
                session = shared.create_login_session()

def mark_file_as_migrated(session, page_title, replacement):
    used = False
    for used in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        used = True
        print("still used on", used)
    if used:
        return False
    else:
        print(page_title, "is not used")
        test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)

        if has_tricky_templating_situation(test_page['page_text']):
            return False

        message = "unused duplicate of Wikimedia Commons file [[:" + replacement  + "]]"
        text = test_page['page_text'] + "\n" + "{{delete|" + message + "}}"
        shared.edit_page_and_show_diff(session, page_title, text, "request deletion of duplicate", test_page['rev_id'], test_page['timestamp'])
        return True
    raise

def has_tricky_templating_situation(page_text):
    if page_text.find("{{delete|") != -1 or page_text.find("{{Delete|") != -1:
        print("deletion requested already")
        print()
        return True
    if page_text.count("{") != 2 or page_text.count("}") != 2:
        print("complex situation, skipping")
        print()
        return True
    if page_text.count("|") != 1:
        print("complex situation, skipping")
        print()
        return True
    return False

def extract_replacement_filename_from_templated_page(text, page_title):
    p = re.compile('\{\{[sS]uperseded by Commons\|([^\}]+)\}\}')
    m = p.search(text)
    if m == None:
        print()
        print()
        print("failed on", page_title)
        print()
        print("----------------")
        print(text)
        print("----------------")
        print()
        return None
    return m.group(1)

def try_to_migrate_as_superseded_by_commons_template_indicated(session, page_title, only_safe, sleeping_after_edit):
    for used in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        print("IN USE!")
    test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    if test_page == None:
        print(page_title)

    replacement = extract_replacement_filename_from_templated_page(test_page['page_text'], page_title)
    if replacement == None:
        print("something broken, no replacement specified")
        return None
    if has_tricky_templating_situation(test_page['page_text']):
        return replacement

    if file_used_and_only_on_pages_where_no_editing_allowed(page_title):
        print("used only on pages exempt from editing like talk pages")
        print()
        return replacement

    migrate_file(page_title, replacement, [], only_safe, sleeping_after_edit=sleeping_after_edit)
    return replacement


def run_hardcoded_file_migrations(only_safe):
    # first I need to tag used ones...
     
    migrate_file("File:Surfergirl.jpg", "File:Eisbach Surfer2.JPG", ["removing file with 'all rights reserved' in the source"], only_safe, got_migration_permission=True)
    
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

def check_is_replacement_ok(old_file, new_file):
    webbrowser.open(shared.osm_wiki_page_link(old_file), new=2)
    webbrowser.open("https://commons.wikimedia.org/wiki/"+new_file.replace(" ", "_"), new=2)
    print("replace that image?")
    shared.pause()
    return True

def migrate_file(old_file, new_file, reasons_list, only_safe, got_migration_permission=False, sleeping_after_edit=True):
    # https://commons.wikimedia.org/wiki/Commons:Deletion_requests/File:RU_road_sign_7.18.svg
    # this needs to be resolved
    if old_file == "File:7.18 (Road sing).gif":
        return
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
                if only_safe:
                    if form['safe'] == False:
                        continue
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
            if got_migration_permission == False:
                if check_is_replacement_ok(old_file, new_file) == False:
                    return
                got_migration_permission = True
            shared.edit_page_and_show_diff(session, page_title, text, edit_summary, data['rev_id'], data['timestamp'])
            if unsafe_changes:
                print("EDIT COULD BE UNSAFE, VERIFY PLS")
                shared.pause()
            if sleeping_after_edit:
                shared.make_delay_after_edit()
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
    if "{{delete|" in text and still_used:
        webbrowser.open(shared.osm_wiki_page_link(old_file), new=2)
        print(page_title, "has deletion requested but is in use")
        shared.pause()
    elif still_used:
        print("still used")
    elif "{{delete|" in text:
        pass
    else:
        if got_migration_permission == False:
            if check_is_replacement_ok(old_file, new_file) == False:
                return
            got_migration_permission = True
        if text.strip() != "":
            text += "\n"
        delete_request = "{{delete|uses replaced with Wikimedia commons alternative ([[:" + new_file + "]]), this file is not needed anymore. And it has licensing issues.}}"
        text += delete_request
        edit_summary = delete_request
        shared.edit_page_and_show_diff(session, old_file, text, edit_summary, data['rev_id'], data['timestamp'], sleep_time=0)

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
                {'from': "image" + (" " * pre) + "=" + (" " * post) + main_form,
                'to': "image = " + new_file,
                'description': 'used in template (quite safe)',
                'safe': True,
                }
            )

            # https://wiki.openstreetmap.org/w/index.php?title=IT:Aeroways&diff=2294021&oldid=2216766
            returned.append(
                {'from': "image" + (" " * pre) + "=" + (" " * post) + main_form.replace("File:", ""),
                'to': "image = " + new_file.replace("File:", ""),
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
