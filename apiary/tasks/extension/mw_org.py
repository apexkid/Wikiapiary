"""Synchronize Rating to Mediawiki.org for extensions."""
# pylint: disable=C0301,R0201,R0904

from apiary.tasks import BaseApiaryTask
import logging
import requests
import ConfigParser
from xml.etree import ElementTree
import os
import mwparserfromhell

LOGGER = logging.getLogger()

class MwTask(BaseApiaryTask):
    """Update extension data on mediawiki.org"""

    def get_rating(self, extension_name):
        """Retrieve and calculate total rating for an extension"""

        rating_properties = ['Has ease of installation rating', 'Has usability rating', 'Has documentation quality rating']
        total_rating = 0
        for property in rating_properties:
            try:
                wiki_return = self.bumble_bee.call({
                    'action': 'ask',
                    'query': ''.join([
                        "[[Category:Reviews]]",
                        "[[Has item::%s]]" % extension_name,
                        "|?%s|format=average", % property
                        ])
                    })
                rating = ((wiki_return['query']['results']).values()[0])['printouts'][property]
                total_rating = total_rating + rating[0]
            except Exception, e:
                raise Exception("Error while querying for Rating for extension %s (%s)." % (extension_name, e))

        return (total_rating / len(rating_properties) )

    def get_mwpagetitle(self, extension_name):
        """Return the corresponding page for the extension on mw.o"""
        #To be modified to fetch by smw property

        return extension_name

    def parse(self, title, wiki):
        """Function to parse MW page using mwparserfromhell"""

        data = {"action": "query", "prop": "revisions", "rvlimit": 1,
                "rvprop": "content", "format": "json", "titles": title}
        wiki_return = wiki.call(data)
        text = wiki_return["query"]["pages"].values()[0]["revisions"][0]["*"]
        return mwparserfromhell.parse(text)

    def run(self, extension_name):
        """Get rating information for an extension and write to mediawiki"""

        rating = self.get_rating(extension_name)
        mwtitle = self.get_mwpagetitle(extension_name)

        data = self.parse(mwtitle, self.mwracer_bee)
        for template in data.filter_templates():
            if template.name.matches(" "):
            template.add("rating", rating)

        wiki_return = self.mwracer_bee.call({
            'action':'query',
            'prop':'info',
            'intoken':'edit',
            'titles':mwtitle,
            'assert':'user'
        })
        LOGGER.debug(wiki_return)
        if 'error' in wiki_return:
            raise Exception(wiki_return)

        pageid = ((wiki_return['query']['pages']).values()[0])['pageid']

        wiki_return = self.mwracer_bee.call({
            'action':'edit',
            'pageid':pageid,
            'text':data,
            'token':self.mwracer_bee_token
        })
        LOGGER.debug(wiki_return)
        if 'error' in wiki_return:
            raise Exception(wiki_return)

        return wiki_return
