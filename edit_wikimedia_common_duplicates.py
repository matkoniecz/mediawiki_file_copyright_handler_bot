import json
import requests
import webbrowser

import shared
import mediawiki_api_query

def main():
    session = shared.create_login_session()

    # https://wiki.openstreetmap.org/wiki/File:Gasometer.jpg
    # Category:Image superseded by Wikimedia Commons
    # list pages where this files are present, attempt replace
    process_wikimedia_commons_duplicates(session, "Spätkauf_in_Skobbler_Berlin.png") # "" to start from scratch


def process_wikimedia_commons_duplicates(session, continue_index = ""):
    while True:
        url = "https://wiki.openstreetmap.org/w/api.php?action=query&format=json&prop=duplicatefiles&generator=allimages&dflimit=50&gaiprop=&gailimit=50&gaicontinue=" + shared.escape_parameter(continue_index)
        response = requests.post(url)
        data = response.json()
        pages = response.json()["query"]["pages"]
        keys = pages.keys()
        for key in keys:
            if "duplicatefiles" in pages[key]:
                process_file_with_duplicates(session, pages[key])

        print("continue_index:", continue_index)
        # {{Superseded by Commons|File:Cliffjumping.jpg}}
        # {{delete|exactly the same file is on Wikimedia Commons, there is no point in maintaining a local copy}}
        if "continue" in data:
            continue_index = data["continue"]["gaicontinue"]
        else:
            break # crawled through all

def process_file_with_duplicates(session, duplication_data):
    page_title = duplication_data["title"]

    data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
    page_text = data['page_text']
    if "{{Delete".lower() in page_text.lower():
        return

    if "{{Featured date".lower() in page_text.lower():
        return

    print(page_title)
    print()
    for duplicate in duplication_data["duplicatefiles"]:
        filename_of_duplicate = "File:" + duplicate["name"]
        print(filename_of_duplicate)
        if "shared" in duplicate:
            print("This file is on Commons")
            # download data about upload history
            osm_wiki_history = mediawiki_api_query.file_upload_history_without_broken_uploads(page_title)
            commons_history = mediawiki_api_query.file_upload_history_without_broken_uploads(filename_of_duplicate, URL="https://commons.wikimedia.org/w/api.php")
            print("osm_wiki_history")
            print(json.dumps(osm_wiki_history, indent=4))
            print("------------------------")
            print("commons_history")
            print(json.dumps(commons_history, indent=4))
            print("------------------------")
            print("osm_wiki_history - initial")
            print(json.dumps(osm_wiki_history[0]['timestamp'], indent=4))
            print("------------------------")
            print("commons_history - last")
            print(json.dumps(commons_history[-1]['timestamp'], indent=4))
            print("------------------------")
            may_be_copied_to_commons = commons_history[-1]['timestamp'] > osm_wiki_history[0]['timestamp']
            print(may_be_copied_to_commons, " - may_be_copied_to_commons")
            if may_be_copied_to_commons:
                print("https://wiki.openstreetmap.org/wiki/" + page_title.replace(" ", "_"))
                print("skipping as it could be copied to Commons from OSM Wiki")
                return

            if filename_of_duplicate.replace(" ", "_") == page_title.replace(" ", "_"):
                #webbrowser.open(shared.osm_wiki_page_link(page_title), new=2)
                with open('duplicates_for_safe_deletion.txt', 'a') as the_file:
                    the_file.write('* [[:' + page_title +']] [[:commons:' + filename_of_duplicate + ']]\n')
                #mark_file_for_deletion_as_commons_duplicate_under_the_same_name(session, page_title, filename_of_duplicate)
            elif mediawiki_api_query.is_file_used_as_image(page_title):
                print("https://wiki.openstreetmap.org/wiki/" + page_title.replace(" ", "_"))
                print("commons_duplicate_under_the_different_name_with_use")
                # TODO
                # tricky, not done as it is unclear whether it would even result in file deletions
                # process some known existing ones before dealing with more of them
                # though maybe marking them is useful?
                #process_commons_duplicate_under_the_different_name_with_use(session, page_title, filename_of_duplicate)
            else:
                print("https://wiki.openstreetmap.org/wiki/" + page_title.replace(" ", "_"))
                print("commons_duplicate_under_the_different_name_not_in_use")
                # TODO: handle this
                # tricky, not done as it is unclear whether it would even result in file deletions
                # process some known existing ones before dealing with more of them
                # though maybe marking them is useful?
                #process_commons_duplicate_under_the_different_name_not_in_use(session, page_title, filename_of_duplicate)

def mark_file_for_deletion_as_commons_duplicate_under_the_same_name(session, page_title, filename_of_duplicate):
    webbrowser.open(shared.osm_wiki_page_link(page_title), new=2)
    append = "{{delete|duplicate of Wikimedia Commons file under the same filename, can be safely deleted even if in use. See [[:commons:" + filename_of_duplicate + "]]. There is no good reason for keeping local duplicates of Wikimedia Commons images. This is a pointless duplication of effort and both Commons and OSM Wiki has huge backlogs in processing images.}}"
    print(append)
    shared.pause()
    shared.append_to_page(session, page_title, "\n" + append, append)

def process_commons_duplicate_under_the_different_name_not_in_use(session, page_title, filename_of_duplicate):
    webbrowser.open(shared.osm_wiki_page_link(page_title), new=2)
    append = "{{delete|duplicate of Wikimedia Commons file under the different filename, but is unused so can be safely deleted. See [[:commons:" + filename_of_duplicate + "]]. There is no good reason for keeping local duplicates of Wikimedia Commons images, this is a pointless duplication of effort and both Commons and OSM Wiki has huge backlogs in processing images.}}"
    print(append)
    shared.pause()
    shared.append_to_page(session, page_title, "\n" + append, append)

def process_commons_duplicate_under_the_different_name_with_use(session, page_title, filename_of_duplicate):
    return
    #potentialy_shadowing_file = mediawiki_api_query.download_page_text(filename_of_duplicate)
    #if potentialy_shadowing_file != None:
    # raise "shadowed"
    # TODO: what anout file pages without text on file page?
    #print("SHADOWING FILE:", shadowing_file)
    for use_page in mediawiki_api_query.pages_where_file_is_used_as_image(page_title):
        file_used_page_data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        file_used_page_text = file_used_page_data['page_text']
        if page_title in file_used_page_text:
            print("FOUND FILE IN", use_page)
            file_used_page_text = file_used_page_text.replace(page_title, filename_of_duplicate)
    if "{{Superseded by Commons|".lower() in page_text.lower():
        return

    webbrowser.open(shared.osm_wiki_page_link(page_title), new=2)
    print("File is in an active use, is on Commons under a different filename", page_title, "vs", filename_of_duplicate)
    append ="{{Superseded by Commons|" + filename_of_duplicate + "}}"
    print(append)
    shared.pause()
    shared.append_to_page(session, page_title, "\n" + append, append)

main()