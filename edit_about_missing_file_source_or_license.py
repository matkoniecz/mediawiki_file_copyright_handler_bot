import mediawiki_api_query
import shared
import mediawiki_api_login_and_editing

import datetime
import random
import time

# TODO: scan recently uploaded
# TODO: scan all problematic from specific user
# https://wiki.openstreetmap.org/wiki/Special:Log/upload
# https://wiki.openstreetmap.org/w/api.php?action=query&list=logevents&letype=upload&lelimit=500
# https://wiki.openstreetmap.org/w/api.php?action=query&list=logevents&letype=upload&lelimit=500&leuser=Marek%20kleciak

def selftest():
    text = """{{unknown}}
{{openstreetmap trademark}}
[[category:plots and charts]]

[[category:statistics]]"""
    if skip_image_based_on_text_on_its_description("dummy", text) != False:
        raise Exception("wrong classification")
    text = "{{delete|unused duplicate of https://wiki.openstreetmap.org/wiki/File:Rotwein.png}}"
    if skip_image_based_on_text_on_its_description("dummy", text) != True:
        raise Exception("wrong classification")

def main():
    selftest()
    session = shared.create_login_session()

    # imagery source missing:
    # https://wiki.openstreetmap.org/wiki/File:2-Lane-Roundabout-Winston-Salem-NC-With-Numbers.png https://wiki.openstreetmap.org/wiki/User_talk:LeifRasmussen#Imagery_source
    # https://wiki.openstreetmap.org/wiki/File:Farmland_Tea1.JPG https://wiki.openstreetmap.org/wiki/File:CADToolsE3.jpg https://wiki.openstreetmap.org/wiki/File:CADToolsE1.jpg https://wiki.openstreetmap.org/wiki/File:CADToolsE3.jpg https://wiki.openstreetmap.org/wiki/File:CADToolsE4.jpg https://wiki.openstreetmap.org/wiki/File:CADToolsE5.jpg https://wiki.openstreetmap.org/wiki/File:CADToolsE6.jpg https://wiki.openstreetmap.org/wiki/File:CADToolsE7.jpg https://wiki.openstreetmap.org/wiki/File:Example_of_bad_mapping_Ilam.JPG https://wiki.openstreetmap.org/wiki/File:Scrub2.JPG https://wiki.openstreetmap.org/wiki/File:NepalSchoolTypicalAerialImage.JPG https://wiki.openstreetmap.org/wiki/File:Terraced_Farmland1.JPG

    # unlisted:
    # https://wiki.openstreetmap.org/wiki/File:MarekYjunction.jpg
    # https://wiki.openstreetmap.org/wiki/File:MarekdDoubleXjunction.jpg
    # https://wiki.openstreetmap.org/wiki/File:MarekOandTjunction.jpg
    # https://wiki.openstreetmap.org/wiki/File:MarekXjunction.jpg
    # https://wiki.openstreetmap.org/wiki/File:MarekdDoubleXjunctionWithGrassInTheMiddle.jpg
    # see more https://wiki.openstreetmap.org/w/index.php?title=Special:ListFiles&offset=20150817161600%7CMarekMockupHamburgBurgstrasse.jpg&user=Marek+kleciak

    skipped_users = shared.users_dropped_from_regular_processing()
    refresh_users = [
    "PanierAvide", "Segubi", # got link with their file listing, lets keep it updates
    ]

    screenshot_only_uploads_remaining = [
    ]
    for user in screenshot_only_uploads_remaining:
        mark_all_unmarked_files_by_user(session, user, "{{unknown}}\n[[Category:Screenshots]]")
    """
    mark_all_unmarked_files_by_user(session, "Berteun", "[[Category:Screenshots]]{{unknown}}")
    mark_all_unmarked_files_by_user(session, "R0uzic", "{{PD-shape}}")

    returned = make_page_listing_problematic_uploads_by_user(session, "Lalali") #PD-shape spam
    returned = returned['session']
    shared.show_latest_diff_on_page(returned['page_name'])

    complain_about_missing_file_source_or_license(files_to_find=77, extra_files_to_preview=88, files_for_processing=['File:Rotwein.png'], banned_users=skipped_users, source_description="single file")  
    """
    #shared.pause()
    
    sources = []
    sources.append({"description": "has {{unknown}}", "files": mediawiki_api_query.pages_from_category("Category:Media without a license - without subcategory")})
    sources.append({"description": "without any category", "files": uncategorized_images_skipping_some_initial_ones()})
    sources.append({"description": "by date, from 2009", "files": mediawiki_api_query.images_by_date("2009-01-01T18:05:46Z")})
    sources.append({"description": "by date, from start", "files": mediawiki_api_query.images_by_date("1900-01-01T18:05:46Z")})
    sources.append({"description": "by date, from 2015", "files": mediawiki_api_query.images_by_date("2015-01-01T18:05:46Z")})
    sources.append({
        "description": "by date, from 2022",
        "files": mediawiki_api_query.images_by_date("2022-01-01T00:00:00Z"),
        })
    random.shuffle(sources)
    for source in sources:
        print(source["description"])
        complain_about_missing_file_source_or_license(files_to_find=51, extra_files_to_preview=53, files_for_processing=source["files"], banned_users=skipped_users, source_description=source["description"])
    for user in skipped_users + refresh_users:
        returned = make_page_listing_problematic_uploads_by_user(session, user)
        session = returned['session']
    show_retaggable_images(session)

    mark_screenshots_as_also_needing_attention(session)

    # for 6+month old and marked as waiting for action for uploader
    # {{delete|unused image, no evidence of free licensing, unused so not qualifying for fair use}}

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

def mark_screenshots_as_also_needing_attention(session):
    for category in screeshot_categories():
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
            print(page_title)
            time.sleep(1)
            text = test_page['page_text'] + "\n" + "{{Unknown}}"
            shared.edit_page_and_show_diff(session, page_title, text, "what is the license here? (I have no idea what is the answer to that)", test_page['rev_id'], test_page['timestamp'])

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
    files_for_processing = mediawiki_api_query.uploads_by_username_generator(username)
    generated_data = detect_images_with_missing_licences(limit, files_for_processing, notify_uploaders_once=False, notify_recently_notified=True)
    page_name = "User:" + mediawiki_api_login_and_editing.password_data.username() + "/notify uploaders/" + username
    if len(generated_data) >= minimum:
        session = show_overview_page(session, generated_data, page_name, limit, username + " [[Drafts/Media file license chart]]")
    return {"page_name": page_name, "problematic_image_data": generated_data, 'session': session}

def show_overview_page(session, generated_data, show_page, break_after, hint):
    test_page = mediawiki_api_query.download_page_text_with_revision_data(show_page)
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

def complain_about_missing_file_source_or_license(files_to_find, extra_files_to_preview, files_for_processing, banned_users, source_description):
    session = shared.create_login_session()
    generated_data = detect_images_with_missing_licences(files_to_find + extra_files_to_preview, files_for_processing, banned_users, notify_uploaders_once=True)
    create_category_for_the_current_month_if_missing(session)

    session, generated_data = create_overview_pages_for_users_with_more_problematic_uploads(session, generated_data)
    show_page = "User:" + mediawiki_api_login_and_editing.password_data.username() + "/test"

    # datetime.datetime.strptime('2021-04-19T18:22:40Z', "%Y-%m-%dT%H:%M:%SZ")
    hint = "For help with dealing with unlicensed media, see https://wiki.openstreetmap.org/wiki/Category:Media_without_a_license <nowiki>{{JOSM screenshot without imagery}}   {{OSM Carto screenshot}}     {{OSM Carto screenshot||old_license}} {{CC-BY-SA-2.0 OpenStreetMap}} (uploaded before September 12, 2012)</nowiki>\n\nsource of files: " + source_description + "\n\n"
    session = show_overview_page(session, generated_data, show_page, files_to_find, hint)

    if len(generated_data) == 0:
        return

    shared.show_latest_diff_on_page(show_page)
    shared.pause()
    for data in generated_data[:files_to_find]:
        page_title = data['page_title']
        print("page title:", page_title)
        edit_summary = "please, specify missing information about file that would allow keeping it on OSM Wiki"
        session = mark_file_as_without_copyright_info_and_notify_user(session, data, edit_summary)
        
# use returned session, it could be renewed
def create_overview_pages_for_users_with_more_problematic_uploads(session, generated_data):
    for entry in generated_data:
        print("listing requested for", entry["uploader"])
        info = make_page_listing_problematic_uploads_by_user(session, entry["uploader"], limit=10000, minimum=2)
        session = info['session']
        if len(info["problematic_image_data"]) > 1:
            print("user", entry["uploader"], "has more problematic images")
        entry['more_problematic_images'] = info["problematic_image_data"]
    return session, generated_data

# use returned session, it could be renewed
def mark_file_as_without_copyright_info_and_notify_user(session, data_about_affected_page, edit_summary):
    data = data_about_affected_page
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

    user_talk_page_text = user_talk_page_text + notification_on_user_talk(page_title)

    if user_talk_data != None:
        shared.edit_page_and_show_diff(session, user_talk, user_talk_page_text, edit_summary, user_talk_data['rev_id'], user_talk_data['timestamp'])
    else:
        shared.create_page_and_show_diff(session, user_talk, user_talk_page_text, edit_summary)

def edit_talk_page_to_mark_uploader_as_notified(session, page_title, page_text, edit_summary, rev_id, timestamp):
    page_text = page_text.replace("{{unknown}}", "").replace("{{Unknown}}", "")
    page_text = page_text + "\n" + file_template_about_missing_license()
    shared.edit_page_and_show_diff(session, page_title, page_text, edit_summary, rev_id, timestamp)

def create_category_for_the_current_month_if_missing(session):
    category_name = category_for_given_month_name()
    category_text = category_for_given_month_page_text()
    data = mediawiki_api_query.download_page_text_with_revision_data(category_name)
    if data == None:
        shared.create_page_and_show_diff(session, category_name, category_text, "create category for holding files awaiting response")
    elif data['page_text'] != category_text:
        shared.edit_page_and_show_diff(session, category_name, category_text, "reset category for holding files awaiting response", test_page['rev_id'], data['timestamp'])

def file_template_about_missing_license():
    mydate = datetime.datetime.now()
    current_month = mydate.strftime("%B")
    current_year = mydate.strftime("%Y")
    return "{{Unknown|subcategory=uploader notified " + current_month + " " + current_year + "}}"

def category_for_given_month_name():
    mydate = datetime.datetime.now()
    current_month = mydate.strftime("%B")
    current_year = mydate.strftime("%Y")
    return "Category:Media without a license - uploader notified " + current_month + " " + current_year

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

def detect_images_with_missing_licences(files_to_find, files_for_processing, banned_users=[], notify_uploaders_once=True, notify_recently_notified=False):
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
            if is_uploader_eligible_for_new_complaints(returned['uploader']) == False:
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

def is_uploader_eligible_for_new_complaints(uploader):
    user_talk_data = mediawiki_api_query.download_page_text_with_revision_data("User talk:"+uploader)
    if user_talk_data != None:
        person_badgering = mediawiki_api_login_and_editing.password_data.username()
        if user_talk_data['page_text'].find(person_badgering) != -1:
            timestamp = mediawiki_api_query.parse_mediawiki_time_string(user_talk_data['timestamp'])
            now = datetime.datetime.now()
            days_since_last = (now - timestamp).days
            if days_since_last <= 60:
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
        if upload_history == None:
            return None # TODO: remove root cause of THAT
        uploader = mediawiki_api_query.get_uploader_from_file_history(upload_history)
        if uploader == None:
            print("Unable to establish uploader")
            print("https://wiki.openstreetmap.org/wiki/"+page_title.replace(" ", "_"))
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
    "{{unknown}}", # replacing it is implemented
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
    keywords = screeshot_categories() + ["SoTM", #"mapping", "OSM", "OpenStreetMap", "HOT",
    "OSM picture", "Rendered OSM data", "Category:Maps of places", "Map of",
    "taghistory", "chart", "graph", 
    "StreetComplete", # solve this!

    # https://wiki.openstreetmap.org/wiki/Category:Documents
    "Category:Documents",
    # https://wiki.openstreetmap.org/wiki/Category:Images_of_data_use_permissions,_rejections_or_requests
    "Category:Images of data use permissions, rejections or requests",
    # subcategories:
    # https://wiki.openstreetmap.org/wiki/Category:ES:Autorizaciones_para_usar_fuentes_de_datos_de_Espa%C3%B1a
    "Category:ES:Autorizaciones para usar fuentes de datos de España",
    "Letter of authorization", "Autorizzazione", "Authorization", # TODO: just use category from above
    "Photo for profile", "profile picture", "profile", "self photo", "taken by", 
    "selbst", "own work", "taken by me", "self made", "self-made", "I made", "by author", 
    "non-free", "image search", "copied from", "unfree",
    "CC-BY-SA", "public domain",
    "copyright",
    "Bus.meran.eu", # https://wiki.openstreetmap.org/wiki/File:Bus.meran.eu_real_time_bus_map.png
    "AEP - Captage eau.JPG", # asked on https://wiki.openstreetmap.org/wiki/User_talk:Penegal for now
    "licence", "license", "permission", "flickr", "source", "Openfietsmap", "OSM contributors",
    "slippy map",
    "commons", "wikipedia", "0px-", "px-",
    # commons, wikipedia, 0px- covers cases like
    # https://wiki.openstreetmap.org/wiki/File:120px-Zusatzzeichen_1020-12.svg.png https://commons.wikimedia.org/w/index.php?title=File:Zusatzzeichen_1020-12.svg&redirect=no
    # where bothering uploader is not needed and matches can be automatically found

    "Screenshot", # long backlog of weird cases
    "should be replaced with",
    "Asked for more info at", "github.com",
    '[[Category:User images]]',
    "[[Category:Logos]]", # likely {{trademarked}} is missing which would cause skip anyway
    "JOSM", # likely {{JOSM screenshot without imagery}} or one for with imagery

    # https://wiki.openstreetmap.org/wiki/Category:Images_of_published_materials_related_to_OpenStreetMap
    "Category:Images of published materials related to OpenStreetMap",
    "Artikel in", "article in", "article about", "News published in local paper", "News published", # fair use?

    "OSM Coverage",
    # https://wiki.openstreetmap.org/wiki/Talk:Drafts/Media_file_license_chart#More_likely_layers%3A_CyclOSM
    "mapquest", "osmarender", "Render cycle", "Render transport", "CyclOSM", "OpenCycleMap", # arghhhhhhhhhh, licensing of one more thingy https://wiki.openstreetmap.org/wiki/File:Render_cycle_leisure_playground_node.png https://wiki.openstreetmap.org/wiki/File:Render_transport_leisure_playground_area.png https://wiki.openstreetmap.org/wiki/File:Render_mapquest_leisure_playground_area.png 
    "Potlatch", # licensing of https://wiki.openstreetmap.org/wiki/File:Connected_Ways_in_Potlatch.png
    "http",
    "freemap", # https://github.com/FreemapSlovakia/freemap-mapnik/issues/237 https://wiki.openstreetmap.org/wiki/File:OSM-Bratislava-2014-08-18.png https://github.com/matkoniecz/mediawiki_file_copyright_handler_bot/commit/d2cf743317a6c7878c5f3c71141b47d28e19d035
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
    for template in valid_licencing_templates():
        if template.lower() in page_text.lower():
            return True
    return False

def notification_on_user_talk(image_name):
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

In case where it is a photo you (except relatively rare cases) author can make it available under a specific free license.

Would you be OK with CC0 (it allows use without attribution or any other requirement)?

Or do you prefer to require attribution and some other things using CC-BY-SA-4.0? 

If you are the author: Please add <nowiki>{{CC0-self}}</nowiki> to the file page to publish the image under CC0 license.

You can also use <nowiki>{{CC-BY-SA-4.0-self}}</nowiki> to publish under CC-BY-SA-4.0 license.

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

def valid_licencing_templates():
    return [
        "{{PD}}", # in far future it may be worth replacing
        "{{PD-self}}",
        "{{delete", # active deletion request waiting for processing means that page is processed for now
        "{{Superseded by Commons", # special deletion variant
        "{{PD-shape}}",
        "{{PD-text}}",
        "{{PD-textlogo}}",
        "{{CC0}}",
        "{{CC0-self}}",
        "{{CC-BY-2.0}}",
        "{{CC-BY-2.0-self}}",
        "{{CC-BY-2.5}}",
        "{{CC-BY-2.5-self}}",
        "{{CC-BY-3.0}}",
        "{{CC-BY-3.0-self}}",
        "{{CC-BY-4.0}}",
        "{{CC-BY-4.0-self}}",
        "{{CC-BY-SA-2.0}}",
        "{{CC-BY-SA-2.0-self}}",
        "{{CC-BY-SA-2.5}}",
        "{{CC-BY-SA-2.5-self}}",
        "{{CC-BY-SA-3.0}}",
        "{{CC-BY-SA-3.0-self}}",
        "{{CC-BY-SA-4.0}}",
        "{{CC-BY-SA-4.0-self}}",
        "{{CC-BY-SA-2.0 OpenStreetMap}}",
        "{{Geograph}}",
        "{{GFDL}}",
        "{{GPL}}",
        "{{ISC}}",
        "{{JOSM screenshot without imagery}}",
        "{{JOSM screenshot with imagery",
        "{{ODbL OpenStreetMap}}",
        "{{OSM Carto screenshot||old_license}}",
        "{{OSM Carto screenshot}}",
        "{{Tiles@Home screenshot}}",
        "{{PD-PRC-Road Traffic Signs}}",
        "{{WTFPL}}",
        "{{WTFPL-self}}",

        # This can be a crayon license :(
        "{{Attribution}}",

        # This templates should be eliminated
        "{{CC-BY-NC-ND-4.0}}",
        "{{CC-BY-NC-SA-3.0}}",

        # likely problematic, but at less well defined state
        "{{Bing image}}",

        # https://wiki.openstreetmap.org/wiki/Category:Media_license_templates
    ]

main()