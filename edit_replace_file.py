import mediawiki_api_query
import shared
import mediawiki_api_login_and_editing

import datetime
import random
import time
import webbrowser
import re
import mwparserfromhell

def selftest():
    match_found = False
    for form in valid_image_transforms("File:CalshotLF.png", "File:Roaring Middle light float - geograph.org.uk - 638833.jpg"):
        if form["from"] == "[[File:CalshotLF.png|":
            match_found = True
    if match_found == False:
        raise

    if extract_replacement_filename_from_templated_page("{{Superseded by Commons|File:Baghdad International Airport (October 2003).jpg}}", "test") != "File:Baghdad International Airport (October 2003).jpg":
        raise
    page = """This work is in the public domain in the United States because it is a work of the United States Federal Government under the terms of Title 17, Chapter 1, Section 105 of the US Code. See Copyright.

Note: This only applies to works of the Federal Government and not to the work of any individual U.S. state, territory, commonwealth, county, municipality, or any other subdivision.

[[Category:Outdoor OSM data Example]]
{{Superseded by Commons|File:Baghdad International Airport (October 2003).jpg}}
"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Baghdad International Airport (October 2003).jpg":
        raise
    page =  """{{Superseded image|File:Beverages-14.svg}}"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Beverages-14.svg":
        raise
    page =  """{{Superseded image|File:Beverages-14.svg|reason=jdjdjdsjsissjifijsf}}"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Beverages-14.svg":
        raise
    page =  """{{Superseded image|File:Beverages-14.svg|reason=jd jdjdsj sis sj if  ijsf}}"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Beverages-14.svg":
        raise
    page =  """{{Superseded image|File:Beverages-14.svg|reason=duplicate of [[:File:Beverages-14.svg]]. See also [https://wiki.openstreetmap.org/wiki/User_talk:Immaculate_Mwanja#Duplicate_icons]}}"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Beverages-14.svg":
        raise
    page =  """{{Superseded image|File:BoatSharingIcon.svg|SVG available}}"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:BoatSharingIcon.svg":
        raise
    page =  """{{Superseded image|Pharmacy nondispensing.png|Visually identical with higher resolution}}"""
    if extract_replacement_filename_from_templated_page(page, "test") != "File:Pharmacy nondispensing.png":
        raise Exception("failed to support missing File: prefix")
        

def main():
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
    for category in ["Category:Image superseded by another image", "Category:Image superseded by Wikimedia Commons"]:
        for page_title in mediawiki_api_query.pages_from_category(category):
            if page_title in ["Category:Image superseded by Wikimedia Commons",
                              "File:Pharmacyno20.png" # TODO https://wiki.openstreetmap.org/wiki/File%3APharmacyno20.png https://wiki.openstreetmap.org/wiki/User:DieterTD/Kosmos_Bunker - requires page blankings or fixing dead Kosmos rulesets
                              ]:
                continue
            extra_comment = ""
            if category == "Category:Image superseded by Wikimedia Commons":
                extra_comment = " It is on Wikimedia commons"
            index += 1
            print(page_title, index)
            while True:
                try:
                    replacement = try_to_migrate_as_superseded_template_indicated(session, page_title, only_safe, sleeping_after_edit=False, extra_comment=extra_comment)
                    break
                except mediawiki_api_login_and_editing.NoEditPermissionException:
                    # Recreate session, may be needed after long processing
                    session = shared.create_login_session()

def has_tricky_templating_situation(page_text):
    wikicode = mwparserfromhell.parse(page_text)
    templates = wikicode.filter_templates()
    for template in templates:
        if template.name.strip().lower() == "delete":
            print("deletion requested already with delete template")
            print()
            return True
    return False

def extract_replacement_filename_from_templated_page(text, page_title):
    p = re.compile('\{\{[sS]uperseded by Commons\|([^\}|]+)\}\}')
    m = p.search(text)

    p_superseded = re.compile('\{\{[sS]uperseded image\|([^\}|]+)(|\|(|reason\s*=)\s*.*)\}\}')
    m_superseded = p_superseded.search(text)

    found = None
    if m != None:
        found = m.group(1)
    elif m_superseded != None:
        found = m_superseded.group(1)
    if found != None:
        p = re.compile('(.*):')
        m = p.search(found)
        prefix = None
        if m != None:
            prefix = m.group(1)
        if prefix == "File":
            return found
        if prefix == "Image":
            return found.replace("Image:", "File:")
        if prefix == None:
            return "File:" + found
        raise Exception("unexpected prefix " + prefix + " in " + found)
    print()
    print()
    print("failed on", page_title)
    print()
    print("----------------")
    print(text)
    print("----------------")
    print()
    return None

def try_to_migrate_as_superseded_template_indicated(session, page_title, only_safe, sleeping_after_edit, extra_comment):
    for used in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        print("IN USE!")
    test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    if test_page == None:
        print(page_title)

    replacement = extract_replacement_filename_from_templated_page(test_page['page_text'], page_title)
    if replacement == None:
        print()
        print(page_title)
        print("something broken, no replacement specified")
        print()
        return None
    if has_tricky_templating_situation(test_page['page_text']):
        return replacement

    if file_used_and_only_on_pages_where_no_editing_allowed(page_title):
        print("used only on pages exempt from editing like talk pages")
        print()
        return replacement

    migrate_file(page_title, replacement, [], only_safe, sleeping_after_edit=sleeping_after_edit, extra_comment=extra_comment)
    return replacement


def run_hardcoded_file_migrations(only_safe):
    # first I need to tag used ones...
     
    #migrate_file("File:Surfergirl.jpg", "File:Eisbach Surfer2.JPG", ["removing file with 'all rights reserved' in the source"], only_safe, got_migration_permission=True)
    pass
    
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
    if is_replacement_from_commons(old_file, new_file):
        webbrowser.open("https://commons.wikimedia.org/wiki/"+new_file.replace(" ", "_"), new=2)
    else:
        webbrowser.open("https://wiki.openstreetmap.org/wiki/"+new_file.replace(" ", "_"), new=2)
    print("replace that image?")
    shared.pause()
    return True

def is_replacement_from_commons(old_file, new_file):
    if old_file == new_file:
        # in such case it makes sense only if local file will be deleted
        # though it will fail in some degenerate cases and assumes lack of garbage input
        return True
    if mediawiki_api_query.file_upload_history(new_file) == None:
        # again, existence of Wikimedia Commons file is not checked!
        return True
    return False

def migrate_file(old_file, new_file, reasons_list, only_safe, got_migration_permission=False, sleeping_after_edit=True, extra_comment=""):
    # https://commons.wikimedia.org/wiki/Commons:Deletion_requests/File:RU_road_sign_7.18.svg
    # this needs to be resolved
    if old_file == "File:7.18 (Road sing).gif":
        return
    session = shared.create_login_session()
    if extra_comment != "":
        extra_comment = " " + extra_comment
    edit_summary = "file replacement ( " + old_file + " -> " + new_file + " )" + extra_comment + "."
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
        for form in valid_image_transforms(old_file, new_file):
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
        target = ""
        if is_replacement_from_commons(old_file, new_file):
            target = "Wikimedia Commons"
        else:
            target = "local file"
        delete_request = "{{delete|uses replaced with " + target + " alternative ([[:" + new_file + "]]), this file is not needed anymore.}}"
        text += delete_request
        edit_summary = delete_request
        shared.edit_page_and_show_diff(session, old_file, text, edit_summary, data['rev_id'], data['timestamp'], sleep_time=0)

def valid_image_transforms(main_form, new_file):
    if main_form.find("File:") != 0:
        raise
    without_prefix = main_form.replace("File:", "")
    lowercase_first_letter = "File:" + without_prefix[0].lower() + without_prefix[1:]
    forms = [main_form, main_form.replace(" ", "_"), lowercase_first_letter, lowercase_first_letter.replace(" ", "_")]
    returned = []
    for form in forms:
        returned.append(
            {'from': "[[" + form + "|",
            'to': "[[" + new_file + "|",
            'description': 'basic form, safe replacement',
            'safe': True,
            },
        )
        
        for pre in range(0, 10):
            for post in range(0, 3):
                # infoboxes with varying space count
                returned.append(
                    {'from': "image" + (" " * pre) + "=" + (" " * post) + form,
                    'to': "image = " + new_file,
                    'description': 'used in template (quite safe)',
                    'safe': True,
                    }
                )

                # https://wiki.openstreetmap.org/w/index.php?title=IT:Aeroways&diff=2294021&oldid=2216766
                returned.append(
                    {'from': "image" + (" " * pre) + "=" + (" " * post) + form.replace("File:", ""),
                    'to': "image = " + new_file.replace("File:", ""),
                    'description': 'used in template (quite safe)',
                    'safe': True,
                    }
                )
                returned.append(
                    {'from': "image" + (" " * pre) + "=" + (" " * post) + form.replace("File:", ""),
                    'to': "image = " + new_file.replace("File:", ""),
                    'description': 'used in template (quite safe)',
                    'safe': True,
                    }
                )
        returned = returned + [
            {'from': form,
            'to': new_file,
            'description': 'basic form',
            'safe': False,
            },
            {'from': form.replace("File:", ""),
            'to': new_file.replace("File:", ""),
            'description': 'used in template or mentioned',
            'safe': False,
            },
        ]
    return returned

selftest()
main()
