import taginfo
import mediawiki_api_query
import shared

def main():
    session = shared.create_login_session('image_bot')
    key = "wiki:symbol"
    link_info = " - see https://taginfo.openstreetmap.org/keys/" + key + "#values"
    for taginfo_value_response in taginfo.query.values_of_key(key):
        #print(key, "=", value)
        tag_value = taginfo_value_response["value"]
        if is_invalid_value(tag_value):
            #print("skipping invalid value, not processing it further" + link_info)
            #print(value["value"])
            continue
        file = taginfo_value_response["value"]
        if "File:".lower() not in file.lower():
            file = "File:" + file
        history = mediawiki_api_query.file_upload_history(file)
        if history == None:
            handle_link_to_file_not_existing_at_osm_wiki(file, link_info)
        else:
            mark_file_as_used_in_wiki_symbol_tag(file, key, tag_value, session)

def is_invalid_value(value):
    if value in ["t.b.d.", "todo", "fixme"]:
        # https://forum.openstreetmap.org/viewtopic.php?id=75226
        return True
    if "wikimedia.org" in value:
        return True
    if value.strip() != value:
        return True
    return False

def handle_link_to_file_not_existing_at_osm_wiki(file, link_info):
    #print("handle_link_to_file_not_existing_at_osm_wiki - start")
    commons_history = mediawiki_api_query.file_upload_history(file, URL="https://commons.wikimedia.org/w/api.php")
    #print("handle_link_to_file_not_existing_at_osm_wiki - XXXXX marker")
    if commons_history == None:
        deletion_log = mediawiki_api_query.deletion_history(file)
        if deletion_log != None and len(deletion_log) > 0:
            print("* [[:" + file + "]]" + link_info + " - this file", shared.osm_wiki_page_link(file), "was on OSM Wiki but was deleted")
            print("handle_link_to_file_not_existing_at_osm_wiki - end")
            return
        deletion_log = mediawiki_api_query.deletion_history(file, URL="https://commons.wikimedia.org/w/api.php")
        if deletion_log != None and len(deletion_log) > 0:
            print("* [[:" + file + "]]" + link_info + " - this file was on Commons but was deleted")
            print("handle_link_to_file_not_existing_at_osm_wiki - end")
            return
    #print("handle_link_to_file_not_existing_at_osm_wiki - end")

def mark_file_as_used_in_wiki_symbol_tag(file, key, tag_value, session):
    test_page = mediawiki_api_query.download_page_text_with_revision_data(file)
    if test_page == None:
        commons_page = mediawiki_api_query.download_page_text_with_revision_data(file, URL="https://commons.wikimedia.org/w/api.php")
        if commons_page != None:
            return
    other_sufficient_forms = ["{{Used outside the Wiki|description=It is used as a value of {{Tag|wiki:symbol}} and this file is linked by some relations in the OSM database. See https://taginfo.openstreetmap.org/tags/?key=" + key.replace(":", "%3A") + "&value=" + tag_value.replace(" ", "%20") + "}}"

    ]
    added = "{{Used outside the Wiki|description=It is used as a value of {{Tag|wiki:symbol}} and this file is linked by some relations in the OSM database. See https://taginfo.openstreetmap.org/tags/?key=" + key + "&value=" + tag_value.replace(" ", "%20") + "}}"
    text = test_page['page_text']
    other_form_is_present = False
    for form in other_sufficient_forms:
        if form in text:
            other_form_is_present = True
    if added in text:
        if other_form_is_present:
            for form in other_sufficient_forms:
                text = text.replace(form, "")
                shared.edit_page(session, file, text, "remove old duplicated info", test_page['rev_id'], test_page['timestamp'], mark_as_bot_edit=True)
        return
    if other_form_is_present:
        return
    print(file)
    text = text + "\n" + added
    # use shared.edit_page_and_show_diff in testing
    shared.edit_page(session, file, text, "adding [[Template:Used outside the Wiki]]", test_page['rev_id'], test_page['timestamp'], mark_as_bot_edit=True)
    shared.make_delay_after_edit()

main()