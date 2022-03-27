import mediawiki_api_query
import shared

for page_title in mediawiki_api_query.pages_from_category("Category:Labelled for deletion"):
    if page_title.find("File:") != 0:
        continue
    if mediawiki_api_query.is_used_as_image_anywhere(page_title):
        print("* [[:" + page_title + "]]")