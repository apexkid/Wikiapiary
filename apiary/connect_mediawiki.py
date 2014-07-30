"""Connect to MediaWiki."""
# pylint: disable=C0301,C0103,W1201

import ConfigParser
from simplemediawiki import MediaWiki
import os
import logging


LOGGER = logging.getLogger()

# Set default connection details for localhost dev
API_URL = 'https://www.mediawiki.org/w/api.php'

MEDIAWIKI_CONFIG = os.environ.get("MEDIAWIKI_CONFIG", 'config/mediawiki.cfg')
if os.path.isfile(MEDIAWIKI_CONFIG):
    LOGGER.info("Detected configuration at %s" % MEDIAWIKI_CONFIG)
    config = ConfigParser.SafeConfigParser()
    config.read(MEDIAWIKI_CONFIG)
else:
    LOGGER.warn("No configuration file detected.")

def open_connection(bot_name, env_name):
    """Open a connection to MediaWiki for a bot."""

    LOGGER.info("Opening MediaWiki connection for %s at %s" % (bot_name, API_URL))
    mw_wiki = MediaWiki(API_URL)

    try:
        # Passwords may be defined in the environment or in the config file
        # We prefer the environment variable if it is present
        password = os.environ.get(env_name, None)
        if password is None:
            try:
                config.get('Passwords', bot_name)
            except Exception, e:
                LOGGER.warn('No configuration file detected.')
        LOGGER.info("Logging in as %s uSsing %s" % (bot_name, password))
        mw_wiki.login(bot_name, password)

        LOGGER.info("Getting edit token for %s" % bot_name)
        wiki_return = mw_wiki.call({
            'action': 'tokens',
            'type': 'edit'
        })
        edit_token = wiki_return['tokens']['edittoken']
        LOGGER.info("%s has been given edit token %s" % (bot_name, edit_token))

    except Exception, e:
        LOGGER.error("Unable to login as %s. Error: %s" % (bot_name, e))
        edit_token = None

    return (mw_wiki, edit_token)


LOGGER.info("Setting up MWRacer Bee")
mwracer_bee, mwracer_bee_token = open_connection("MWracer Bee", "MWRACERBEE")
