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
        shared.null_edit(session, page_title)

main()