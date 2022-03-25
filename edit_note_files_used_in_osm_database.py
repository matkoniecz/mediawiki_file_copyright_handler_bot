import taginfo
import mediawiki_api_query
import shared

def is_invalid_value(value):
    if value in ["t.b.d.", "todo", "fixme"]:
        # https://forum.openstreetmap.org/viewtopic.php?id=75226
        return True
    if "wikimedia.org" in value:
        return True
    if value.strip() != value:
        return True
    return False

session = shared.create_login_session('image_bot')
key = "wiki:symbol"
for value in taginfo.query.values_of_key(key):
    #print(key, "=", value)
    if is_invalid_value(value["value"]):
        print("skipping")
        print(value["value"])
        continue
    file = value["value"]
    if "File:".lower() not in file.lower():
        file = "File:" + file
    history = mediawiki_api_query.file_upload_history(file)
    if history == None:
        commons_history = mediawiki_api_query.file_upload_history(file, URL="https://commons.wikimedia.org/w/api.php")
        if commons_history == None:
            deletion_log = mediawiki_api_query.deletion_history(file)
            if deletion_log != None and len(deletion_log) > 0:
                print("* [[:" + file + "]]")
    else:
        test_page = mediawiki_api_query.download_page_text_with_revision_data(file)
        added = "{{Used outside the Wiki|description=It is used as a value of {{Tag|wiki:symbol}} and this file is linked by some relations in the OSM database. See https://taginfo.openstreetmap.org/tags/?key=wiki%3Asymbol&value=" + value["value"] + "}}"
        text = test_page['page_text']
        if added in text:
            continue
        print(file)
        text = text + "\n" + added
        shared.edit_page_and_show_diff(session, file, text, "adding [[Template:Used outside the Wiki]]", test_page['rev_id'], test_page['timestamp'])
        shared.make_delay_after_edit()
