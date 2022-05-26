import mediawiki_api_query
import shared
import datetime
import mediawiki_api_login_and_editing
import mwparserfromhell
import time

def selftest():
    fixed = add_uploader_info("{{CC-BY-4.0-self}}", "uploader")
    if fixed != "{{CC-BY-4.0-self|1=uploader}}":
        print(fixed)
        raise

def main():
    selftest()
    session = shared.create_login_session('image_bot')

    banned_users = shared.users_dropped_from_regular_processing()
    categories = [
        "Category:Attribution not provided in CC license template which requires attribution",
        #"Category:CC BY files",
        #"Category:CC BY-SA files",
    ]
    for category in categories:
        for page_title in mediawiki_api_query.pages_from_category(category):
            uploader = shared.get_uploader_of_file_or_none_if_not_clear(page_title)
            if uploader == None:
                continue
            data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
            text = data['page_text']
            text = add_uploader_info(text, uploader)
            if text == data['page_text']:
                if "-self" not in data['page_text']:
                    continue
                print(page_title, "- no changes proposed")
                print(data['page_text'])
                continue
            print(text)
            print(data['page_text'])
            while True:
                try:
                    shared.edit_page_and_show_diff(session, page_title, text, "add attribution directly to the template", data['rev_id'], data['timestamp'])
                    break
                except mediawiki_api_login_and_editing.NoEditPermissionException:
                    # Recreate session, may be needed after long processing
                    session = shared.create_login_session()

def add_uploader_info(text, uploader):
    wikicode = mwparserfromhell.parse(text)
    templates = wikicode.filter_templates()
    for template in templates:
        if template.name.strip().upper().replace("-SELF", "-self") in expected_templates():
            if len(template.params) == 0:
                replaced = "{{" + str(template.name) + "}}"
                new = "{{" + template.name.strip().upper().replace("-SELF", "-self") + "|1=" + uploader + "}}"
                text = text.replace(replaced, new)
    return text

def expected_templates():
    returned = []
    for basic in ["CC-BY", "CC-BY-SA"]:
        for version in ["2.0", "3.0", "4.0"]:
            returned.append(basic + "-"  + version + "-self")
    return returned


main()
