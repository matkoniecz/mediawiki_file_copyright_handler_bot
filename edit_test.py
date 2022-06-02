import shared
import mediawiki_api_login_and_editing
import mediawiki_api_query

session = shared.create_login_session()
page_title = "User:" + mediawiki_api_login_and_editing.password_data.username() + "/test"
text = "test"
edit_summary = "test"
data = mediawiki_api_query.download_page_text_with_revision_data(page_title)
shared.edit_page_and_show_diff(session, page_title, text, edit_summary, data['rev_id'], data['timestamp'])
