# Purpose

This scripts were created to [handle files at OpenStreetMap Wiki that were without proper licensing or with a mising source](https://wiki.openstreetmap.org/wiki/User:Mateusz_Konieczny/notify_uploaders).

It should be relatively easy to adapt it to other Mediawiki sites, but it was not tested.

Pull requests making easier to configure it for use with wikis other that OSM Wiki are welcome, as long as code is not getting much worse and more complicated.

This Mediawiki script can 

* detect files not marked with license templates (to handle copyright violations) - [edit_about_missing_file_source_or_license.py](edit_about_missing_file_source_or_license.py)
* detect duplicates of Wikimedia Commons images - [edit_wikimedia_common_duplicates.py](edit_wikimedia_common_duplicates.py)
** writes to `duplicates_for_safe_deletion.txt` file files safe to delete, in addition has some output in stdout
# Setup
## Obtain code
Clone repository.

```
git clone https://github.com/matkoniecz/mediawiki_file_copyright_handler_bot.git
cd mediawiki_file_copyright_handler_bot
```

## Dependencies

`pip3 install -r requirements.txt`

## Create config file with passwords

`secret.json` with content like 
```
{
	"api_password": {
        "comment": "use https://wiki.openstreetmap.org/wiki/Special:BotPasswords - giving your standard username and password may work for now but can break at any time",
		"username": "User account@User account:_test",
		"password": "m3mfgy8j6bvwker29i2rsjk0r3y5060"
	}
}
```

use [https://wiki.openstreetmap.org/wiki/Special:BotPasswords](https://wiki.openstreetmap.org/wiki/Special:BotPasswords) to obtain password
## Adapt to Wiki

If not used at [OSM Wiki](https://wiki.openstreetmap.org/) you will need to add some configuration - pull requests are welcomed!

### Base API url
Likely base api url needs to be passed - right now it defaults to OSM Wiki.

After base api url is defined and passed around defaulting to OSM Wiki likely should be removed.

It is fine to rewrite script so it will require API as a parameter.

### Templates

Templates are likely to be different - so it would be necessary to also specify them somehow in config.

# Alternatives

* https://github.com/AntiCompositeNumber/AntiCompositeBot/blob/master/src/nolicense.py - sadly I was unable to figure out how to run it. Seems to require a direct server access to run SQL queries.
* see [Wikimedia Commons recent bot edits](https://commons.wikimedia.org/wiki/Special:RecentChanges?hidehumans=1&translations=filter&hidecategorization=1&hideWikibase=1&hidelog=1&namespace=3&limit=500&days=7&urlversion=2) - maybe you will find something better more fitting for you there
# Architecture

## Why not pywikibot?

Pywikibot has some weird, arcane architecture - and extra complexity on top of quite simple API is not actually useful.

Especially as I consider rewriting it in JS and making available as a web page.

Why pywikibot is bad? For example it requires creation of `user-config.py` file with some arcane config for start.

I admit that

```
family='osm'
mylang='en'
usernames['osm']['en'] = 'Actual username'
```

is not terribly complex once magic and poorly documented syntax is figured out. But having an extra poorly defined and unnecessary config file somewhere in location decided by library is just asking for problems and bugs.

Using `pywikibot` requires more learning about `pywikibot` internals than about Mediawiki API. This is not useful, especially as pywikibot in practice (in my experience) has much worse documentation and is less clear and harder to debug than direct API calls.

In this case it seems simpler to reinvent and document wheel using well documented component over trying to reconstruct pywikibot documentation from complex source code, stackoverflow questions and discussions scattered elsewhere.

Pywikibot also required passing some magic values (for example `6` for file namespace index)

# Thanks

Thanks to people from https://t.me/wmhack for pointing me in right direction! 

Especially to Bohdan Melnychuk.
