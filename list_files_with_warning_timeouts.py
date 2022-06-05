import mediawiki_api_query
import mediawiki_api_login_and_editing
import shared
import mwparserfromhell
import datetime

print("TODO: check for https://wiki.openstreetmap.org/wiki/Template:User_username on user page")


def main():
    split_into_rows = []
    for page_title in files_eligible_for_deletion():
        if page_title.find("File:") != 0:
            print(page_title, "is not a file")
            continue
        file_in_use = mediawiki_api_query.is_used_as_image_anywhere(page_title)
        page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        page_text = page['page_text']

        waiting_for_deletion = False
        has_commons_replacement = False
        wikicode = mwparserfromhell.parse(page_text)
        templates = wikicode.filter_templates()
        for template in templates:
            if template.name.strip().lower() == "delete".lower():
                waiting_for_deletion = True
            if template.name.strip().lower() == "Superseded by Commons".lower():
                has_commons_replacement = True

        problem = False
        comments = []
        if not waiting_for_deletion:
            comments.append("not marked for deletion")
            problem = True

        if file_in_use:
            comments.append("still in use")
            problem = True
        
        if has_commons_replacement:
            comments.append("replaceable by Commons file")

        comment = ", ".join(comments)
        if problem:
            comment = "{{Yellow|" + comment + "}}"

        if waiting_for_deletion and not file_in_use:
            continue
        
        upload_history = mediawiki_api_query.file_upload_history(page_title)
        uploader = shared.get_uploader_from_upload_history_or_none_if_not_clear(upload_history, page_title, log_when_returned_none_due_to_multiple_uploaders=True)

        if uploader == None:
            uploader = "multiple"
        else:
            uploader = "[[User:" + uploader + "|" + uploader + "]] [https://www.openstreetmap.org/user/" + uploader.replace(" ", "%20") + " potential OSM user matching wiki account name]"

        split_into_rows.append(["[[:" + page_title + "]]" + "|"+comment, uploader])
        print("* [[:" + page_title + "]]")
    
    for page_title in files_soon_eligible_for_deletion():
        file_in_use = mediawiki_api_query.is_used_as_image_anywhere(page_title)
        if not file_in_use:
            continue

        comments = []
        if file_in_use:
            comments.append("still in use")

        comment = ""
        if comments != []:
            comment = "{{Green|" + ", ".join(comments) + "}}"

        upload_history = mediawiki_api_query.file_upload_history(page_title)
        uploader = shared.get_uploader_from_upload_history_or_none_if_not_clear(upload_history, page_title, log_when_returned_none_due_to_multiple_uploaders=True)

        if uploader == None:
            uploader = "multiple"
        else:
            uploader = "[[User:" + uploader + "|" + uploader + "]] [https://www.openstreetmap.org/user/" + uploader.replace(" ", "%20") + " potential OSM user matching wiki account name]"

        split_into_rows.append(["[[:" + page_title + "]]" + "|"+comment, uploader])

    array = shared.generate_array_wikicode(split_into_rows)
    print(array)

    text = array
    session = shared.create_login_session()
    show_page = "User:" + mediawiki_api_login_and_editing.password_data.username() + "/cleanup"
    test_page = mediawiki_api_query.download_page_text_with_revision_data(show_page)
    edit_summary = "listing files where action is needed"
    if test_page == None:
        shared.create_page_and_show_diff(session, show_page, text, edit_summary)
    else:
        shared.edit_page_and_show_diff(session, show_page, text, edit_summary, test_page['rev_id'], test_page['timestamp'])

def files_eligible_for_deletion():
    # currently oldest category is 
    # Category:Media without a license - author notified October 2021

    # check
    # https://wiki.openstreetmap.org/wiki/Category:Media_without_a_license
    # https://wiki.openstreetmap.org/wiki/Category:Media_without_a_proper_attribution
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    max_month_offset = 2021 * 12 + 10 - ( year * 12 + month )

    # when things are eligible for deletion?
    # lets take "uploader notified 2022, May"
    # it can include files from last day of May
    # so one month lapses at last day of 2022-06
    # so two month lapses at last day of 2022-07
    # so six month lapses at last day of 2022-11
    # so on 2022-12-01 one may start deleting photos from 2022-05
    min_month_offset = -7

    return files_where_uploaders_were_notified(range(max_month_offset, min_month_offset + 1))

def files_soon_eligible_for_deletion():
    return files_where_uploaders_were_notified(range(-6, -4))


def files_where_uploaders_were_notified(month_offset_range):
    returned = []
    for offset in month_offset_range:
        print(offset)
        now = datetime.datetime.now()
        year = now.year
        month = now.month + offset
        while month <= 0:
            month += 12
            year -= 1
        checked_date = datetime.date(year, month, 1)
        checked_month_name = checked_date.strftime("%B")
        # generate plausible category names
        # Category:Media without a license - author notified October 2021
        # Category:Media without a license - uploader notified 2022, May
        # Category:Media without a proper attribution - uploader notified 2022, May
        categories = [
            "Category:Media without a license - author notified " + checked_month_name + " " + str(year),
            "Category:Media without a license - uploader notified " + checked_month_name + " " + str(year),
            "Category:Media without a license - uploader notified " + str(year) + ", " + checked_month_name,
            "Category:Media without a proper attribution - uploader notified " + str(year) + ", " + checked_month_name,
        ]
        for category in categories:
            for page_title in mediawiki_api_query.pages_from_category(category):
                returned.append(page_title)
        month -= 1
    return returned

main()
