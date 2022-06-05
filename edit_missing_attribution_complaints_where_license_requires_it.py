import mediawiki_api_query
import shared
import datetime
import mediawiki_api_login_and_editing
import mwparserfromhell
import time
import webbrowser

def selftest():
    if is_marked_already("{{Proper attribution missing|template=CC-BY-4.0|subcategory=uploader notified 2022, May}}") != True:
        raise

def main():
    selftest()
    detect_files_where_attribution_complaint_is_present_and_unwanted()
    detect_files_where_attribution_complaint_is_missing_and_required()

def detect_files_where_attribution_complaint_is_present_and_unwanted():
    for page_title in mediawiki_api_query.pages_from_category("Category:Media without a proper attribution"):
        if page_title.find("Category:") == 0:
            continue
        data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        text = data['page_text']
        if is_marked_already(text):
            missing_attribution = list_templates_with_missing_attribution_for_this_text(text, page_title)
            if len(missing_attribution) == 0:
                webbrowser.open(shared.osm_wiki_page_link(page_title), new=2)

def detect_files_where_attribution_complaint_is_missing_and_required():
    session = shared.create_login_session('image_bot')
    watchlisting_session = shared.create_login_session()

    banned_users = shared.users_dropped_from_regular_processing()
    categories = [
        "Category:Attribution not provided in CC license template which requires attribution",
        "Category:CC BY files",
        "Category:CC BY-SA files",
    ]
    for category in categories:
        for page_title in mediawiki_api_query.pages_from_category(category):
            uploader = shared.get_uploader_of_file_or_none_if_not_clear(page_title)
            if uploader == None:
                continue
            if uploader in banned_users:
                continue
            banned_users.append(uploader) # will be now processed either way

            data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
            text = data['page_text']
            if is_marked_already(text):
                # extra download per user, will protect against processing hundreds of images
                # where for all relevant user was notified anyway 
                continue
            try:
                files = get_all_affected_uploads_by_user(uploader)
            except mediawiki_api_query.InvalidUsername as e:
                print("page_title:", page_title, "uploader:", uploader)
            if files == []:
                print(uploader, "is apparently fully notified, also for", page_title, "which triggered checks")
                continue # notified already

            likely_editable = False
            for file_data in files:
                file = file_data['filename']
                file_page = mediawiki_api_query.download_page_text_with_revision_data(file)
                text = file_page['page_text']
                for keyword in shared.description_keywords_that_may_indicate_that_author_is_specified():
                    if keyword.lower() in text.lower():
                        print()
                        print()
                        print("======================================")
                        print()
                        print()
                        print(shared.osm_wiki_page_link(file))
                        print(file_page['page_text'])
                        print()
                        likely_editable = True

            if likely_editable:
                print(uploader, "apparently has files which are marked, just not in the template")
                print("skipping them")
                print("===========================================")
                print("============>END===========================")
                print("===========================================")
                print()
                continue # notified already

            print(uploader)
            shared.pause()
            session = notify_user_on_their_talk_page(session, uploader, files)
            for file_data in files:
                session, watchlisting_session = mark_file_as_missing_clear_attribution(session, watchlisting_session, file_data)
            create_category_for_the_current_month_if_missing(session)

def mark_file_as_missing_clear_attribution(session, watchlisting_session, file_data):
    while True:
        file = file_data['filename']
        try:
            mediawiki_api_login_and_editing.watchlist_page(watchlisting_session, file)
        except mediawiki_api_login_and_editing.NoEditPermissionException:
            # Recreate session, may be needed after long processing
            watchlisting_session = shared.create_login_session()
        try:
            file_page = mediawiki_api_query.download_page_text_with_revision_data(file)
            template = file_data['templates_without_attribution'][0]
            template = str(template)
            text = file_page['page_text'] + "\n" + file_template_about_missing_attribution(template)
            text = text.replace("CC-by-sa", "CC-BY-SA") # to enable working -self suffix
            text = text.replace("Cc-by-sa", "CC-BY-SA") # to enable working -self suffix
            text = text.replace("cc-by-sa", "CC-BY-SA") # to enable working -self suffix
            text = text.replace("cc-by-", "CC-BY-") # to enable working -self suffix
            shared.edit_page_and_show_diff(session, file, text, "mark file as missing well specified attribution (in template itself)", file_page['rev_id'], file_page['timestamp'])
            return session, watchlisting_session
        except mediawiki_api_login_and_editing.NoEditPermissionException:
            # Recreate session, may be needed after long processing
            session = shared.create_login_session('image_bot')
    raise

def notify_user_on_their_talk_page(session, uploader, files):
    user_page_title = "User talk:" + uploader
    page = mediawiki_api_query.download_page_text_with_revision_data(user_page_title)
    message = get_message(files)
    edit_summary = "notify about missing well specified attribution in uploaded files"
    while True:
        try:
            if page == None:
                shared.create_page_and_show_diff(session, user_page_title, message, edit_summary)
            else:
                text = page['page_text'] + "\n" + message
                shared.edit_page_and_show_diff(session, user_page_title, text, edit_summary, page['rev_id'], page['timestamp'])
            return session
        except mediawiki_api_login_and_editing.NoEditPermissionException:
            # Recreate session, may be needed after long processing
            session = shared.create_login_session('image_bot')
    raise

def is_marked_already(page_text):
    if template_name().lower() in page_text.lower():
        return True
    text_considered_as_marking = [
       "{{Superseded by Commons",
       "{{Unknown",
       "{{Delete",
       "OpenStreetMap trademark", "OpenStreetMap logo", # TODO handle this mess and remove this
    ]
    for text in text_considered_as_marking:
        if text.lower() in page_text.lower():
            return True
    return False

def template_name():
    return "Proper attribution missing"

def selectable_category_name_part():
    mydate = datetime.datetime.now()
    current_month = mydate.strftime("%B")
    current_year = mydate.strftime("%Y")
    return "uploader notified " + current_year + ", " + current_month

def entire_category_name():
    return "Media without a proper attribution - " + selectable_category_name_part()

def create_category_for_the_current_month_if_missing(session):
    category_name = "Category:" + entire_category_name()
    category_text = category_for_given_month_page_text()
    data = mediawiki_api_query.download_page_text_with_revision_data(category_name)
    if data == None:
        shared.create_page_and_show_diff(session, category_name, category_text, "create category for holding files awaiting response")
    elif data['page_text'] != category_text:
        print("DIFFFFFFFFFFFFFFFFF!")
        print(data['page_text'])
        print(category_text)
        shared.edit_page_and_show_diff(session, category_name, category_text, "reset category for holding files awaiting response", data['rev_id'], data['timestamp'])

def category_for_given_month_page_text():
    return """Use <pre>""" + file_template_about_missing_attribution("template_name_used_for_file") + """</pre>to put file here.

Please, use solely only where someone who uploaded file was notified during this month.

[[Category:Media without a proper attribution]]"""

def file_template_about_missing_attribution(template):
    return "{{" + template_name() + "|template=" + template + "|subcategory=" + selectable_category_name_part() + "}}"

def get_message(list_of_file_infos):
    uploaded = "file"
    to_be = "is"
    description_form = "description"
    if len(list_of_file_infos) >= 2:
        uploaded = "files"
        to_be = "are"
        description_form = "descriptions"
    message = "== Attribution =="
    message += "\n\n"
    message += "Hello! And sorry for bothering you, but " + description_form + " of " + uploaded + " you uploaded need to be improved."
    message += "\n\n"
    message += "You have uploaded " + uploaded + " which " + to_be + " licensed as requiring attribution. But right now attribution is not specified properly."
    message += "\n\n"
    message += "Please, [https://wiki.openstreetmap.org/w/index.php?title=Talk:Wiki&action=edit&section=new ask for help] if something is confusing or unclear in this message."
    message += "\n\n"
    message += "Please, fix that problem with this uploads - note that images with unclear licensing situation may be deleted."
    message += "\n\n"
    message += "Attribution may be missing completely or just be specified in nonstandard way, in either case it needs to be improved. Note that using CC-BY files without specifying attribution is a copyright violation, which is often unethical and unwanted. So clearly specifying required attribution is needed if license which makes attribution mandatory was used."
    message += "\n\n"
    message += "If it is applying to your own work which not based on work by others - then you can select own user name or some other preferred attribution or even change license to for example {{T|CC0-self}}"
    message += "\n\n"
    message += "For your own work: ensure that it is clearly stated at file page that you created image/took the photo/etc"
    message += "\n\n"
    message += "For works by others - please ensure that there is link to the original source which confirms license and that you used proper attribution, or that source is clearly stated in some other way."
    message += "\n\n"
    message += "Especially for old OSM-baded maps, made from data before license change on 12 September 2012 you should use \"map data © OpenStreetMap contributors\" as at least part of attribution"
    message += "\n\n"
    message += "For old [[OSM Carto]] maps, which predate license change on 12 September 2012 you can use a special template <nowiki> {{OSM Carto screenshot||old_license}}</nowiki>"
    message += "\n\n"
    for file in list_of_file_infos:
        if len(file['templates_without_attribution']) != 1:
            raise
        template_name = str(file['templates_without_attribution'][0])
        message += "* [[:" + file['filename'] + "]]"
        message += "\n"
    return message

def expected_templates():
    returned = []
    for basic in ["CC-BY", "CC-BY-SA"]:
        for version in ["2.0", "3.0", "4.0"]:
            returned.append(basic + "-"  + version)
    return returned

def get_all_affected_uploads_by_user(uploader):
    returned = []
    for page_title in mediawiki_api_query.uploads_by_username_generator(uploader):
        #print("get_all_affected_uploads_by_user", uploader, page_title)
        data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        text = data['page_text']
        if is_marked_already(text):
            continue
        missing_attribution = list_templates_with_missing_attribution_for_this_text(text, page_title)
        if len(missing_attribution) > 1:
            print(page_title)
            print(missing_attribution)
            print("giving up")
            print()
        elif len(missing_attribution) == 1:
            returned.append({"filename": page_title, "templates_without_attribution": missing_attribution})
    return returned

def list_templates_with_missing_attribution_for_this_text(text, page_title):
    returned = []
    wikicode = mwparserfromhell.parse(text)
    templates = wikicode.filter_templates()
    for template in templates:
        if template.name.strip().upper() in expected_templates():
            if len(template.params) > 1:
                for param in template.params:
                    print(param)
                raise
            if len(template.params) == 1:
                # TODO: check is it ending at the correct location
                continue
            if len(template.params) == 0:
                if text.replace("{{" + str(template.name) + "}}", "").replace("== Licensing ==", "").strip() != "":
                    print()
                    print()
                    print()
                    print("attribution may be recoverable...")
                    print(shared.osm_wiki_page_link(page_title))
                    print(text)
                    print()
                returned.append(template.name)
            else:
                raise "impossible"
    return returned

main()
