import mediawiki_api_query
import shared
import datetime
import mediawiki_api_login_and_editing

def selftest():
    pass

def main():
    selftest()
    session = shared.create_login_session()

    for page_title in mediawiki_api_query.pages_from_category("Category:Disabled"):
        print(page_title)
        test_page = mediawiki_api_query.download_page_text_with_revision_data(page_title)
        text = test_page['page_text']
        shared.edit_page(session, page_title, text, "NULL EDIT", test_page['rev_id'], test_page['timestamp'])

main()