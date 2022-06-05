import mediawiki_api_query
import shared
import mediawiki_api_login_and_editing

import datetime
import random
import time
import mwparserfromhell

# TODO: scan recently uploaded
# TODO: scan all problematic from specific user
# https://wiki.openstreetmap.org/wiki/Special:Log/upload
# https://wiki.openstreetmap.org/w/api.php?action=query&list=logevents&letype=upload&lelimit=500
# https://wiki.openstreetmap.org/w/api.php?action=query&list=logevents&letype=upload&lelimit=500&leuser=Marek%20kleciak

def selftest():
    license_selfcheck()
    text = """{{unknown}}
[[category:Images]]
"""
    if skip_image_based_on_text_on_presence_of_keywords_in_description("dummy", text) != False:
        raise Exception("wrong classification")
    if skip_image_based_on_text_on_its_description("dummy", text) != False:
        raise Exception("wrong classification")
    text = "{{delete|unused duplicate of https://wiki.openstreetmap.org/wiki/File:Rotwein.png}}"
    if skip_image_based_on_text_on_its_description("dummy", text) != True:
        raise Exception("wrong classification")

def main():
    selftest()
    session = shared.create_login_session()

    skipped_users = shared.users_dropped_from_regular_processing()
    refresh_users = [
    "PanierAvide", "Segubi", "Reneman", "marek kleciak" # got link with their file listing, lets keep it updates
    ]
    mark_categories_as_also_needing_attention(session, screeshot_categories(), limit=300)
    mark_categories_as_also_needing_attention(session, map_categories(), limit=300)

    screenshot_only_uploads_remaining = [
    ]
    for user in screenshot_only_uploads_remaining:
        mark_all_unmarked_files_by_user(session, user, "{{unknown}}\n[[Category:Screenshots]]")
    maps_only_uploads_remaining = [
    ]
    for user in maps_only_uploads_remaining:
        mark_all_unmarked_files_by_user(session, user, "{{unknown}}\n[[Category:Maps]]")
    """
    mark_all_unmarked_files_by_user(session, "ThomasKlosa", "{{Unknown|subcategory=uploader notified March 2022}}")
    mark_all_unmarked_files_by_user(session, "Berteun", "[[Category:Screenshots]]\n{{unknown}}")
    mark_all_unmarked_files_by_user(session, "Davalv", "[[Category:Maps]]\n{{unknown}}")
    mark_all_unmarked_files_by_user(session, "R0uzic", "{{PD-shape}}")

    returned = make_page_listing_problematic_uploads_by_user(session, "Lalali") #PD-shape spam
    returned = returned['session']
    shared.show_latest_diff_on_page(returned['page_name'])

    days_of_inactive_talk_page = 40
    complain_about_missing_file_source_or_license(files_to_find=77, extra_files_to_preview=88, files_for_processing=['File:Rotwein.png'], banned_users=skipped_users, source_description="single file", days_of_inactive_talk_page=0)
    """
    #shared.pause()
    
    detect_images_to_complain_about(skipped_users)

    show_retaggable_images(session)

    mark_categories_as_also_needing_attention(session, screeshot_categories(), limit=90)
    mark_categories_as_also_needing_attention(session, map_categories(), limit=90)
    #for cat in all_subcategories(session, "Category:Maps of places by continent"):
    #    print("        \"" + cat + "\",")

    # for 6+month old and marked as waiting for action for uploader
    # {{delete|unused image, no evidence of free licensing, unused so not qualifying for fair use}}

def sources_of_images_for_checking():
    sources = []
    sources.append({"description": "has {{unknown}}", "files": mediawiki_api_query.pages_from_category("Category:Media without a license - without subcategory")})
    sources.append({"description": "without any category", "files": uncategorized_images_skipping_some_initial_ones()})
    sources.append({"description": "by date, from 2009", "files": mediawiki_api_query.images_by_date("2009-01-01T18:05:46Z")})
    sources.append({"description": "by date, from start", "files": mediawiki_api_query.images_by_date("1900-01-01T18:05:46Z")})
    sources.append({"description": "by date, from 2016", "files": mediawiki_api_query.images_by_date("2016-01-01T18:05:46Z")})
    sources.append({
        "description": "by date, from 2022",
        "files": mediawiki_api_query.images_by_date("2022-01-01T00:00:00Z"),
        "days_of_inactive_talk_page": 0,
        })
    random.shuffle(sources)
    return sources

def detect_images_to_complain_about(skipped_users):
    session = shared.create_login_session()
    sources = sources_of_images_for_checking()
    for source in sources:
        print(source["description"])
        days_of_inactive_talk_page = 20
        if 'days_of_inactive_talk_page' in source:
            days_of_inactive_talk_page = source['days_of_inactive_talk_page']
        complain_about_missing_file_source_or_license(files_to_find=21, extra_files_to_preview=23, files_for_processing=source["files"], banned_users=skipped_users, source_description=source["description"], days_of_inactive_talk_page=days_of_inactive_talk_page)
    for user in skipped_users + refresh_users:
        returned = make_page_listing_problematic_uploads_by_user(session, user)
        session = returned['session']

def license_selfcheck():
    missing_licences = False
    category_with_license_templates = "Category:Media license templates"
    licenses_on_wiki_list = list(mediawiki_api_query.pages_from_category(category_with_license_templates))

    for page_title in licenses_on_wiki_list:
        name = page_title.replace("Template:", "")
        if name in ["Self-made-image", "Panoramafreiheit", "Personality rights",
                    "OpenStreetMap trademark", "Trademarked", "Free media",
                    "Free screenshot"]:
            # building blocks, not actual license
            continue
        if name in ["Bing image portions"]:
            # insufficient by itself
            continue
        if name in ["Unknown"]:
            # warns about lack of license
            continue
        if name in ["Wiki:Media file license chart"]:
            # likely should not be there, as well...
            continue
        if "File:" in name:
            print(name)
            print("FILE in category with licensing TEMPLATES - something went wrong")
            continue
        if name not in valid_licencing_template_names():
            print(name)
            missing_licences = True
    if missing_licences:
        raise Exception("there are entries in " + category_with_license_templates + " but not listed as licences in this script")
    for licence in valid_licencing_template_names():
        if licence in ["delete", "Superseded by Commons"]:
            # warns about terminal lack of license
            continue
        if licence in ["PD-text", "PD-textlogo", "Apache"]:
            # redirect
            continue
        template_page = "Template:" + licence
        template_doc_page = template_page + "/doc"
        if template_page not in licenses_on_wiki_list:
            session = shared.create_login_session()
            shared.null_edit(session, template_doc_page)
            shared.null_edit(session, template_page)
            licenses_on_wiki_list = list(mediawiki_api_query.pages_from_category(category_with_license_templates))
            if template_page not in licenses_on_wiki_list:
                raise Exception(licence + " is missing on wiki in its category (usually making null edits on template and /doc subpage fixes problem, but it was tried already here)")

def screeshot_categories():
    return [
        "Category:Screenshots",
        "Category:Images of Osmand",
        "Category:GPSMapEdit screenshots",
        "Category:GPSMapEdit screenshots",
        "Category:Images of ID",
        "Category:Images of Osmand",
        "Category:Images of OSMTracker (Android)",
        "Category:Images of Vespucci",
        "Category:Ito OSM Mapper screenshots",
        "Category:Images of Java Applet",
        "Category:Mapillary screenshots",
        "Category:MapSource screenshots",
        "Category:Images of Potlatch2",
        "Category:Images of OSM Garmin maps",
        #"Category:Images of JOSM", # Many are {{JOSM screenshot without imagery}} - TODO: recheck
        "Category:Screenshots of notification mails",
    ]

def map_categories():
    return [
        "Category:Maps of places by continent",
        "Category:Maps of places in Africa",
        "Category:Maps of places in Antarctica",
        "Category:Maps of places in Asia",
        "Category:Maps of places in Europe",
        "Category:Maps of places in North America",
        "Category:Maps of places in Oceania",
        "Category:Maps of places in South America",
        "Category:Maps of places in the United States",
        "Category:Maps of places in Austria",
        "Category:Maps of places in Belgium",
        "Category:Maps of places in Bulgaria",
        "Category:Maps of places in Denmark",
        "Category:Maps of places in Finland",
        "Category:Maps of places in France",
        "Category:Maps of places in Germany",
        "Category:Maps of places in Iceland",
        "Category:Maps of places in Italy",
        "Category:Maps of places in the Netherlands",
        "Category:Maps of places in Norway",
        "Category:Maps of places in Poland",
        "Category:Maps of places in Portugal",
        "Category:Maps of places in Sweden",
        "Category:Maps of places in Switzerland",
        "Category:Maps of places in Turkey",
        "Category:Maps of places in the United Kingdom",
        "Category:Maps of places in Baden-Württemberg",
        "Category:Maps of places in Bayern",
        "Category:Maps of places in Berlin",
        "Category:Maps of places in Nordrhein-Westfalen",
        "Category:Maps of places in Sachsen",
        "Category:Maps of places in Sachsen-Anhalt",
        "Category:Maps of Turku",
        "Category:Map exports of Turku",
        "Category:Map sources of Turku",
        "Category:Maps of Brussels Capital Region",
        "Category:Maps of Flanders",
        "Category:Maps of Wallonia",
        "Category:Maps of places in Brussels Capital Region",
        "Category:Maps of places in Flanders",
        "Category:Maps of places in Wallonia",
        "Category:Maps of Brabant wallon",
        "Category:Maps of Hainaut",
        "Category:Maps of Province de Liège",
        "Category:Maps of Province de Luxembourg",
        "Category:Maps of Province de Namur",
        "Category:Maps of places in Brabant wallon",
        "Category:Maps of places in Hainaut",
        "Category:Maps of places in Province de Liège",
        "Category:Maps of places in Province de Luxembourg",
        "Category:Maps of places in Province de Namur",
        "Category:Maps of Provincie Antwerpen",
        "Category:Maps of Limburg (België)",
        "Category:Maps of Oost-Vlaanderen",
        "Category:Maps of Vlaams-Brabant",
        "Category:Maps of West-Vlaanderen",
        "Category:Maps of places in Provincie Antwerpen",
        "Category:Maps of places in Limburg (België)",
        "Category:Maps of places in Oost-Vlaanderen",
        "Category:Maps of places in Vlaams-Brabant",
        "Category:Maps of places in West-Vlaanderen",
        "Category:Maps of places in Lebanon",
        "Category:Maps of places in Pakistan",
    ]

def all_subcategories(session, root_category, found=None):
    found = [root_category]
    remaining = [root_category]
    while len(remaining) > 0:
        category = remaining.pop()
        for page_title in mediawiki_api_query.pages_from_category(category):
            if "Category:" in page_title:
                if page_title not in found:
                    found.append(page_title)
                    remaining.append(page_title)
    return found

def mark_categories_as_also_needing_attention(session, processed_categories, limit=10):
    for category in processed_categories:
        for page_title in mediawiki_api_query.pages_from_category(category):
            if page_title in screeshot_categories():
                continue
            if "Category:" in page_title:
                print("Skipping", page_title, "as category")
                print("        \"" + page_title + "\",")
                # TODO: run on subcategories?
                continue
            if "File:" not in page_title:
                print("Skipping", page_title, "as without File: in the title")
                continue
            test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
            if "{{unknown" in test_page['page_text'].lower():
                continue
            if "{" in test_page['page_text']:
                if is_marked_with_template_declaring_licensing_status(test_page['page_text']):
                    continue
                else:
                    print("has template, without declaring licensing status!")
            print(page_title)
            text = test_page['page_text'] + "\n" + "{{Unknown}}"
            shared.edit_page_and_show_diff(session, page_title, text, "what is the license here? (please fill it if you know it or you are author and can license it! [[Wiki:Media file license chart]] may be helpful)", test_page['rev_id'], test_page['timestamp'])
            limit -= 1
            print("remaining limit:", limit)
            if limit <= 0:
                return
            shared.make_delay_after_edit()

def uncategorized_images_skipping_some_initial_ones():
    skip = random.randrange(0, 10000)
    print("skipping", skip)
    skipped = []
    for file in uncategorized_images():
        if len(skipped) < skip:
            skipped.append(file)
        else:
            yield file
    for file in skipped:
        yield file

def mark_all_unmarked_files_by_user(session, username, marker):
    files_for_processing = mediawiki_api_query.uploads_by_username_generator(username)
    limit = 1000
    generated_data = detect_images_with_missing_licences(limit, files_for_processing, notify_uploaders_once=False, notify_recently_notified=True)
    for entry in generated_data:
        page_title = entry['page_title']
        test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        edit_summary = "marking as " + marker
        if test_page == None:
            shared.create_page_and_show_diff(session, page_title, marker, edit_summary)
        else:
            text = test_page['page_text'] + "\n" + marker
            shared.edit_page_and_show_diff(session, page_title, text, edit_summary, test_page['rev_id'], test_page['timestamp'])

def make_page_listing_problematic_uploads_by_user(session, username, limit=10000, minimum=2):
    if session == None:
        raise Exception("session cannot be None")
    files_for_processing = mediawiki_api_query.uploads_by_username_generator(username)
    generated_data = detect_images_with_missing_licences(limit, files_for_processing, notify_uploaders_once=False, notify_recently_notified=True)
    page_name = "User:" + mediawiki_api_login_and_editing.password_data.username() + "/notify uploaders/" + username
    session = show_overview_page(session, generated_data, page_name, limit, username + " [[Drafts/Media file license chart]]", minimum_for_new_page=2)
    if session == None:
        raise Exception("session cannot be None")
    return {"page_name": page_name, "problematic_image_data": generated_data, 'session': session}

def show_overview_page(session, generated_data, show_page, break_after, hint, minimum_for_new_page):
    if session == None:
        raise Exception("session cannot be None")
    test_page = mediawiki_api_query.download_page_text_with_revision_data(show_page)
    if test_page == None:
        if len(generated_data) < minimum_for_new_page:
            return session
    table_for_confirmation = shared.generate_table_showing_image_data_for_review(generated_data, break_after=break_after)
    text = hint + "\n" + table_for_confirmation
    edit_summary = "copyright review"
    while True:
        try:
            if test_page == None:
                shared.create_page(session, show_page, text, edit_summary)
                return session
            elif test_page['page_text'] != text:
                shared.edit_page(session, show_page, text, edit_summary, test_page['rev_id'], test_page['timestamp'])
                return session
        except mediawiki_api_login_and_editing.NoEditPermissionException:
            # Recreate session, may be needed after long processing
            session = shared.create_login_session()
    raise "unexpected"

def complain_about_missing_file_source_or_license(files_to_find, extra_files_to_preview, files_for_processing, banned_users, source_description, days_of_inactive_talk_page):
    session = shared.create_login_session()
    if session == None:
        raise Exception("session cannot be None")
    generated_data = detect_images_with_missing_licences(files_to_find + extra_files_to_preview, files_for_processing, banned_users, notify_uploaders_once=True, days_of_inactive_talk_page=days_of_inactive_talk_page)
    create_category_for_the_current_month_if_missing(session)

    session, generated_data = create_overview_pages_for_users_with_more_problematic_uploads(session, generated_data)
    show_page = "User:" + mediawiki_api_login_and_editing.password_data.username() + "/test"

    # datetime.datetime.strptime('2021-04-19T18:22:40Z', "%Y-%m-%dT%H:%M:%SZ")
    hint = """For help with dealing with unlicensed media, see https://wiki.openstreetmap.org/wiki/Category:Media_without_a_license and [[Drafts/Media file license chart]]
<br>
<nowiki>{{JOSM screenshot without imagery}}</nowiki>
<br>
<nowiki>{{JOSM screenshot with imagery|}}</nowiki>
<br>
<nowiki>{{OSM Carto screenshot}}</nowiki>
<br>
<nowiki>
{{OSM Carto screenshot||old_license}}</nowiki>
<br>
<nowiki>
{{OpenStreetMap trademark}}</nowiki>
<br>
<nowiki>
{{CC-BY-SA-2.0 OpenStreetMap}} (uploaded before September 12, 2012)
</nowiki>\n\nsource of files: """ + source_description + "\n\n"
    session = show_overview_page(session, generated_data, show_page, files_to_find, hint, minimum_for_new_page=0)

    if len(generated_data) == 0:
        return

    shared.show_latest_diff_on_page(show_page)
    print("Launch marking of files, as presented on", show_page, "?")
    shared.pause()
    for data in generated_data[:files_to_find]:
        page_title = data['page_title']
        print("page title:", page_title)
        edit_summary = "please, specify missing information about file that would allow keeping it on OSM Wiki"
        session = mark_file_as_without_copyright_info_and_notify_user(session, data, edit_summary)

# use returned session, it could be renewed
def create_overview_pages_for_users_with_more_problematic_uploads(session, generated_data):
    if session == None:
        raise Exception("session cannot be None")
    for entry in generated_data:
        print("listing requested for", entry["uploader"])
        info = make_page_listing_problematic_uploads_by_user(session, entry["uploader"], limit=10000, minimum=2)
        session = info['session']
        if len(info["problematic_image_data"]) > 1:
            print("user", entry["uploader"], "has more problematic images")
        entry['more_problematic_images'] = info["problematic_image_data"]
        print("listing completed for", entry["uploader"])
    if session == None:
        raise Exception("session cannot be None")
    return session, generated_data

# use returned session, it could be renewed
def mark_file_as_without_copyright_info_and_notify_user(session, data_about_affected_page, edit_summary):
    data = data_about_affected_page
    current_data = mediawiki_api_query.download_page_text_with_revision_data(data['page_title'])
    if data['page_text'] != current_data['page_text']:
        print(data['page_title'], "contents were changed in meantime, skipping")
        return session
    try:
        notify_user_about_missing_copyright_data(session, data['uploader'], data['page_title'], edit_summary)
    except mediawiki_api_login_and_editing.NoEditPermissionException:
        # Recreate session, may be needed after long processing
        session = shared.create_login_session()
        notify_user_about_missing_copyright_data(session, data['uploader'], data['page_title'], edit_summary)

    try:
        edit_talk_page_to_mark_uploader_as_notified(session, data['page_title'], data['page_text'], edit_summary, data['rev_id'], data['timestamp'])
    except mediawiki_api_login_and_editing.NoEditPermissionException:
        # Recreate session, may be needed after long processing
        session = shared.create_login_session()
        edit_talk_page_to_mark_uploader_as_notified(session, data['page_title'], data['page_text'], edit_summary, data['rev_id'], data['timestamp'])
    return session

def notify_user_about_missing_copyright_data(session, uploader_name, page_title, edit_summary):
    user_talk = "User talk:" + uploader_name

    user_talk_data = mediawiki_api_query.download_page_text_with_revision_data(user_talk)
    user_talk_page_text = ""
    if user_talk_data != None:
        user_talk_page_text = user_talk_data['page_text']

    user_talk_page_text = user_talk_page_text + notification_on_user_talk(page_title, uploader_name)

    if user_talk_data != None:
        shared.edit_page_and_show_diff(session, user_talk, user_talk_page_text, edit_summary, user_talk_data['rev_id'], user_talk_data['timestamp'])
    else:
        shared.create_page_and_show_diff(session, user_talk, user_talk_page_text, edit_summary)

def edit_talk_page_to_mark_uploader_as_notified(session, page_title, page_text, edit_summary, rev_id, timestamp):
    page_text = page_text.replace("{{unknown}}", "").replace("{{Unknown}}", "")
    page_text = page_text + "\n" + file_template_about_missing_license()
    shared.edit_page_and_show_diff(session, page_title, page_text, edit_summary, rev_id, timestamp)

def create_category_for_the_current_month_if_missing(session):
    category_name = entire_category_name()
    category_text = category_for_given_month_page_text()
    data = mediawiki_api_query.download_page_text_with_revision_data(category_name)
    if data == None:
        shared.create_page_and_show_diff(session, category_name, category_text, "create category for holding files awaiting response")
    elif data['page_text'] != category_text:
        shared.edit_page_and_show_diff(session, category_name, category_text, "reset category for holding files awaiting response", test_page['rev_id'], data['timestamp'])

def subcategory_selectable_name_part():
    mydate = datetime.datetime.now()
    current_month = mydate.strftime("%B")
    current_year = mydate.strftime("%Y")
    return "uploader notified " + current_year + ", " + current_month

def file_template_about_missing_license():
    return "{{Unknown|subcategory=" + subcategory_selectable_name_part() + "}}"

def entire_category_name():
    return "Category:Media without a license - " + subcategory_selectable_name_part()

def category_for_given_month_page_text():
    return """Use <pre>""" + file_template_about_missing_license() + """</pre>to put file here.

Please, use solely only where someone who uploaded file was notified during this month.

[[Category:Media without a license]]"""

def show_retaggable_images(session):
    print("https://wiki.openstreetmap.org/wiki/Category:Alpha-Numeric_Trail_markings - apply {{PD-textlogo}}")
    file_data = []
    category_content = mediawiki_api_query.pages_from_category("Category:Alpha-Numeric_Trail_markings")
    for page_title in category_content:
        if "Spessart" not in page_title and "Foto " not in page_title and page_title != "File:RT3.jpg":
            page_text = mediawiki_api_query.download_page_text(page_title)
            if "PD-text" not in page_text:
                file_data.append({'page_title': page_title, 'page_text': page_text})
    if len(file_data) == 0:
        print(":) nothing to process")
    else:
        print("file data:", file_data)
        print("------------")
        table_for_confimation = shared.generate_table_showing_image_data_for_review(file_data)
        print(table_for_confimation)
        shared.pause()

def detect_images_with_missing_licences(files_to_find, files_for_processing, banned_users=[], notify_uploaders_once=True, notify_recently_notified=False, days_of_inactive_talk_page=40):
    generated_data = []

    reported_remaining_count = files_to_find
    processed_images = []
    # https://www.mediawiki.org/wiki/API:Allimages
    for page_title in files_for_processing:
        if page_title in processed_images:
            continue
        processed_images.append(page_title)
        returned = detect_images_with_missing_licences_process_page(page_title, banned_users)
        if returned == None:
            continue
        if notify_recently_notified == False:
            if is_uploader_eligible_for_new_complaints(returned['uploader'], days_of_inactive_talk_page) == False:
                print("Skip", returned['uploader'], "as they are ineligible for new complaints")
                banned_users.append(returned['uploader'])
                continue
        generated_data.append(returned)
        if notify_uploaders_once:
            banned_users.append(returned['uploader'])
        reported_remaining_count -= 1
        if reported_remaining_count <= 0:
            break
    return generated_data

def is_uploader_eligible_for_new_complaints(uploader, days_of_inactive_talk_page):
    user_talk_data = mediawiki_api_query.download_page_text_with_revision_data("User talk:"+uploader)
    if user_talk_data != None:
        person_badgering = mediawiki_api_login_and_editing.password_data.username()
        if user_talk_data['page_text'].find(person_badgering) != -1:
            timestamp = mediawiki_api_query.parse_mediawiki_time_string(user_talk_data['timestamp'])
            now = datetime.datetime.now()
            days_since_last = (now - timestamp).days
            if days_since_last < days_of_inactive_talk_page:
                print("------------------")
                print("uploader (" + uploader + ") received comments, from " + person_badgering + " - and their talk page was edited within last", days_since_last, "days")
                # prefer broad range of notifications in initial stage
                return False
    return True


def detect_images_with_missing_licences_process_page(page_title, banned_users):
        unused = True
        if is_skipped_file_type(page_title):
            return None

        # this filtering turned out to not be viable - too many are used   
        #if(mediawiki_api_query.is_file_used_as_image(page_title)):
        #    print("       ", page_title, "is used, will be skipped")
        #    return None

        # TODO: return also metadata here (po oddaniu)
        page_data = mediawiki_api_query.download_page_text_with_revision_data(page_title)

        if page_data == None:
            print("none? here? For page_data?")
            print(page_title)
            return None

        page_text = page_data['page_text']

        if page_text == None:
            print("none? here? For page_text?")
            print(page_title)
            return None

        if skip_image_based_on_text_on_its_description(page_title, page_text):
            return None

        upload_history = mediawiki_api_query.file_upload_history(page_title)
        uploader = shared.get_uploader_from_upload_history_or_none_if_not_clear(upload_history, page_title, log_when_returned_none_due_to_multiple_uploaders=True)
        if uploader == None:
            return None
        if uploader in banned_users:
            return None
        #print("-----------file upload history-------------")
        #print("-------------------------------------------")
        returned = {'page_title': page_title,
                'page_text': page_text,
                'uploader': uploader,
                'rev_id': page_data['rev_id'],
                'parent_id': page_data['parent_id'],
                'timestamp': page_data['timestamp']
                }
        upload_time = mediawiki_api_query.get_upload_date_from_file_history(upload_history)
        if upload_time != None:
            returned['upload_time'] = upload_time
        else:
            print("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"))
        return returned

def nonlicensing_wikicode():
    return ["[[Category:Software design images]]",
    "[[category:plots and charts]]",
    "{{Tag|", "{{Key|", "{{Tagvalue|", # link tags
    "{{itas|", # pointless templates to link external sites
    "{{Information|", # does not link by itself
    "== License ==\n{{Unknown}}", # replacing {{unknown}} is implemented
    "{{unknown}}", # replacing {{unknown}} is implemented
    # "{{Trademarked}}" - requires fair use policy
    "{{bing image portions}}", # not a license by itself I think
    "{{featured date", "{{featured_date",
    "{{openstreetmap trademark}}",
    "http://wiki.openstreetmap.org/wiki/Category:Life_Long_Learning_Mapping_Project",
    "== License ==", "== Licence ==", # often used above "unknown" template
    ]

def skip_image_based_on_text_on_its_description(page_title, page_text):
    if is_marked_with_template_declaring_licensing_status(page_text):
        return True
    if page_text.find("#REDIRECT[[") == 0:
        return True # it is redirect, not an actual file
    cleaned_text = page_text.lower()
    cleaned_text = cleaned_text.replace("{{template:", "{{") # overly verbose by valid method of template use
    for remove in nonlicensing_wikicode():
        cleaned_text = cleaned_text.replace(remove.lower(), "")
    if "{" in cleaned_text.strip() != "":
        #TODO stop skipping here
        return True
    return skip_image_based_on_text_on_presence_of_keywords_in_description(page_title, page_text)

def skip_image_based_on_text_on_presence_of_keywords_in_description(page_title, cleaned_text):
    keywords = screeshot_categories() + [
    # unlikely to be photos
    "SoTM", #"mapping", "OSM", "OpenStreetMap", "HOT",
    "{{OpenStreetMap trademark}}", "trademark", "logo", # unlikely to be photos
    "[[Category:Logos]]", # likely {{trademarked}} is missing which would cause skip anyway
    "JOSM", # likely {{JOSM screenshot without imagery}} or one for with imagery
    "OSM picture", "Rendered OSM data", "Category:Maps of places", "Map of", "OSM-Daten",
    "taghistory", "chart", "graph", "Category:Statistics",
    "slippy map", "map", "mapping party",

    # partially explains the source
    ] + shared.description_keywords_that_may_indicate_that_author_is_specified() + [
    "http",
    "non-free", "image search", "copied from", "unfree",
    "CC-BY-SA", "public domain",
    "copyright",
    "Photo by", "image by", 
    "licence", "license", "permission", "flickr", "Openfietsmap",
    # commons, wikipedia, 0px- covers cases like
    # https://wiki.openstreetmap.org/wiki/File:120px-Zusatzzeichen_1020-12.svg.png https://commons.wikimedia.org/w/index.php?title=File:Zusatzzeichen_1020-12.svg&redirect=no
    # where bothering uploader is not needed and matches can be automatically found

    # unlikely to be photos and complex
    "StreetComplete", # solve this!
    "Screenshot", # long backlog of weird cases

    # https://wiki.openstreetmap.org/wiki/Category:Documents
    "Category:Documents",
    # https://wiki.openstreetmap.org/wiki/Category:Images_of_data_use_permissions,_rejections_or_requests
    "Category:Images of data use permissions, rejections or requests",
    # subcategories:
    # https://wiki.openstreetmap.org/wiki/Category:ES:Autorizaciones_para_usar_fuentes_de_datos_de_Espa%C3%B1a
    "Category:ES:Autorizaciones para usar fuentes de datos de España",
    "Letter of authorization", "Autorizzazione", "Authorization", # TODO: just use category from above
    "Photo for profile", "profile picture", "profile", "self photo", "taken by", '[[Category:User images]]',
    "Bus.meran.eu", # https://wiki.openstreetmap.org/wiki/File:Bus.meran.eu_real_time_bus_map.png
    "AEP - Captage eau.JPG", # asked on https://wiki.openstreetmap.org/wiki/User_talk:Penegal for now
    "Asked for more info at", "github.com",
    # https://wiki.openstreetmap.org/wiki/Category:Images_of_published_materials_related_to_OpenStreetMap
    "Category:Images of published materials related to OpenStreetMap",
    "Artikel in", "article in", "article about", "News published in local paper", "News published", # fair use?
    "OSM Coverage",

    # https://wiki.openstreetmap.org/wiki/Talk:Drafts/Media_file_license_chart#More_likely_layers%3A_CyclOSM
    "mapquest", "osmarender", "Render cycle", "Render transport", "CyclOSM", "OpenCycleMap", "ÖPNVkarte", # arghhhhhhhhhh, licensing of one more thingy https://wiki.openstreetmap.org/wiki/File:Render_cycle_leisure_playground_node.png https://wiki.openstreetmap.org/wiki/File:Render_transport_leisure_playground_area.png https://wiki.openstreetmap.org/wiki/File:Render_mapquest_leisure_playground_area.png 
    "Potlatch", # licensing of https://wiki.openstreetmap.org/wiki/File:Connected_Ways_in_Potlatch.png
    "freemap", # https://github.com/FreemapSlovakia/freemap-mapnik/issues/237 https://wiki.openstreetmap.org/wiki/File:OSM-Bratislava-2014-08-18.png https://github.com/matkoniecz/mediawiki_file_copyright_handler_bot/commit/d2cf743317a6c7878c5f3c71141b47d28e19d035
    "collage", "Comparing", "based on", # handle in the second wave after other images are processed TODO
    "osmfr", "openstreetmap.fr", "french-style", "french style", # https://github.com/cquest/osmfr-cartocss https://wiki.openstreetmap.org/wiki/File:Mont-Blanc-french-style.png https://wiki.openstreetmap.org/wiki/Drafts/Media_file_license_chart
    "tiles@home", "OSM Carto", "Carto",
    "[[Category:Yahoo! Aerial Imagery]]",

    # sheduled for deletion anyway
    "should be replaced with",
    ]

    for keyword in keywords:
        if keyword.lower() in page_title.lower() or keyword.lower() in cleaned_text.lower():
            # TODO drop exception
            print("skipping as likely of historic interest or at least on topic (", keyword, ")", "https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"))
            return True
    return False

def uncategorized_images():
    # many are categorized but still without licences
    group = 0
    while True:
        images = mediawiki_api_query.uncategorized_images(group * 500, 500)
        if len(images) == 0:
            return
        for image in images:
            yield image
        group += 1

    titles = pages_from_category("Category:Media without a license - without subcategory")
    for title in titles:
        yield title
 
def is_skipped_file_type(page_title):
    if ".doc" in page_title.lower():
        return True # TODO, enable
    if ".ods" in page_title.lower():
        return True # TODO, enable
    if ".odt" in page_title.lower():
        return True # TODO, enable
    if ".pdf" in page_title.lower():
        return True # TODO, enable
    if ".svg" in page_title.lower():
        # skipped as many as are actually below TOO
        return True # TODO, enable
    return False

def is_marked_with_template_declaring_licensing_status(page_text):
    wikicode = mwparserfromhell.parse(page_text)
    templates = wikicode.filter_templates()
    for template in templates:
        for valid in valid_licencing_template_names():
            if template.name.strip().lower() == valid.lower():
                return True
    return False

def notification_on_user_talk(image_name, uploader_name):
    # https://wiki.openstreetmap.org/wiki/Category:Media_without_a_license#Writing_to_an_uploader
    # NOTE! one layer of nopwiki should be removed!
    # NOTE! line
    # Once you add missing data - please remove <nowiki>""" + file_template_about_missing_license() + """</nowiki> from the file page.
    # is added only here as exact template can be dynamically generated
    return """
== Missing file information ==
Hello! And thanks for your upload - but some extra info is necessary.

Sorry for bothering you about this, but it is important to know source of the uploaded files.

Are you the creator of image [[:""" + image_name + """]] ?

Or is it copied from some other place (which one?)?

Please, add this info to the file page - something like "I took this photo" or "downloaded from -website link-" or "I took this screeshot of program XYZ" or "this is map generated from OpenStreetMap data and SRTM data" or "map generated from OSM data and only OSM data" or "This is my work based on file -link-to-page-with-that-file-and-its-licensing-info-" or "used file downloaded from internet to create it, no idea which one".

Doing this would be already very useful.

=== Licensing - photos ===
In case that you are the author of the image: Would you agree to open licensing of this image, allowing its use by anyone (similarly to your OSM edits)?

In case where it is a photo you have taken then you can make it available under a specific free license (except some cases, like photos of modern sculptures in coutries without freedom of panorama or taking photo of copyrighted artwork).

Would you be OK with CC0 (it allows use without attribution or any other requirement)?

Or do you prefer to require attribution and some other things using CC-BY-SA-4.0? 

If you are the author: Please add <nowiki>{{CC0-self}}</nowiki> to the file page to publish the image under CC0 license.

You can also use <nowiki>{{CC-BY-SA-4.0-self|""" + uploader_name + """}}</nowiki> to publish under CC-BY-SA-4.0 license.

Once you add missing data - please remove <nowiki>""" + file_template_about_missing_license() + """</nowiki> from the file page.

=== Licensing - other images ===

If it is not a photo situation gets a bit more complicated.

See [[Drafts/Media file license chart]] that may help.

note: if you took screenshot of program made by someone else, screenshot of OSM editor with aerial imagery: then licensing of that elements also matter and you are not a sole author.

note: If you downloaded image made by someone else then you are NOT the author.

Note that in cases where photo is a screenshot of some software interface: usually it is needed to handle also copyright of software itself.

Note that in cases where aerial imagery is present: also licensing of an aerial imagery matter.

=== Help ===

Feel free to ask for help if you need it - you can do it for example by asking on [[Talk:Wiki]]: [https://wiki.openstreetmap.org/w/index.php?title=Talk:Wiki&action=edit&section=new new topic].

Please ask there if you are not sure what is the proper next step. Especially when you are uploading files that are not your own work or are derivative work (screenshots, composition of images, using aerial imagery etc).

If you are interested in wider discussion about handling licencing at OSM Wiki, see [https://wiki.openstreetmap.org/wiki/Talk:Wiki#Designing_policy_for_handling_files_without_clear_license this thread].

(sorry if I missed something that already states license and source: I am looking through over 20 000 files and fixing obvious cases on my own, in other I ask people who upladed files, but it is possible that I missed something - in such case also please answer)

--~~~~

"""

def valid_licencing_template_names():
    return [
        # not strictly licenses, but as long as these are present license processing is not needed
        "delete", # active deletion request waiting for processing means that page is processed for now
        "Superseded by Commons", # special deletion variant

        "PD", # in far future it may be worth replacing
        "PD-self",
        "PD-creator",
        "PD-shape",
        "PD-text",
        "PD-textlogo",
        "CC0",
        "OSM Carto icon", # CC0 with extra info about source
        "OpenCampingMapIcons", # CC0 with extra info about source
        "CC0-self",
        "CC-SA-1.0",
        "CC-BY-2.0",
        "CC-BY-2.0-self",
        "CC-BY-2.5",
        "CC-BY-2.5-self",
        "CC-BY-3.0",
        "CC-BY-3.0-self",
        "CC-BY-4.0",
        "CC-BY-4.0-self",
        "CC-BY-SA-2.0",
        "CC-BY-SA-2.0-self",
        "CC-BY-SA-2.5",
        "CC-BY-SA-2.5-self",
        "CC-BY-SA-3.0",
        "CC-BY-SA-3.0-self",
        "CC-BY-SA-4.0",
        "CC-BY-SA-4.0-self",
        "CC-BY-SA-2.0 OpenStreetMap",
        "Geograph",
        "GFDL",
        "GPL",
        "ISC",
        "ID screenshot", # typically formatted "iD screenshot"
        #"ID screenshot without imagery", not existing maybe it should TODO
        "Bing image",
        "JOSM Icon license",
        "JOSM screenshot without imagery",
        "JOSM screenshot with imagery",
        "ODbL OpenStreetMap",
        "OSM Carto screenshot",
        "OSM Humanitarian screenshot",
        "ODbL",
        "Tiles@Home screenshot",
        "PD-PRC-Road Traffic Signs",
        "WTFPL",
        "WTFPL-self",
        "Licence Ouverte 2",
        "Mapbox image credit",
        "Maxar image",
        "Esri image",
        "Apache",
        "Apache license 2.0",
        "AGPL",
        "LGPL",
        "MIT",
        "MPL",
        "Open Government Licence 2.0 Canada",
        "PD-B-road-sign", # try to get rid of it by migration
        "PD-CAGov",
        "PD-old",
        "PD-RU-exempt",
        "PD-USGov",
        "OpenSeaMap symbol", # TODO: recheck its state https://wiki.openstreetmap.org/w/index.php?title=Template:OpenSeaMap_symbol&action=history

        # This can be a crayon license :(
        # TODO: investigate!
        "Attribution",

        # This templates should be eliminated (TODO HACK)
        "CC-BY-NC-ND-2.0",
        "CC-BY-NC-ND-4.0",
        "CC-BY-NC-SA-3.0",

        # likely problematic, but at less well defined state
        "Bing image",

        "Mapof", # misleading nowadays: TODO: eliminate it from wiki or retitle or something
        "OSM Carto example", # badly named one... TODO: rename

        # https://wiki.openstreetmap.org/wiki/Category:Media_license_templates
    ]

main()