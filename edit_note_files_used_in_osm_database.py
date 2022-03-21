import taginfo
import mediawiki_api_query

key = "wiki:symbol"
for value in taginfo.query.values_of_key(key):
    #print(key, "=", value)
    if value["value"] in ["t.b.d.", "todo", "fixme"]:
        continue
    if "wikimedia.org" in value["value"]:
        continue
    file = value["value"]
    if "File:".lower() not in file.lower():
        file = "File:" + file
    history = mediawiki_api_query.file_upload_history(file)
    if history == None:
        commons_history = mediawiki_api_query.file_upload_history(file, URL="https://commons.wikimedia.org/w/api.php")
        if commons_history == None:
            deletion_log = mediawiki_api_query.deletion_history(file)
            if deletion_log != None and len(deletion_log) > 0:
                print("* [[:" + file + "]]")
