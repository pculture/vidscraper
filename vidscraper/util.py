import re
import urllib

from lxml import etree
from lxml.html import clean

DESCRIPTION_CLEANER = clean.Cleaner(
    remove_tags=['img', 'table', 'tr', 'td', 'th'])


def lxml_inner_html(elt):
    return (elt.text or '') + ''.join(etree.tostring(child) for child in elt)

def clean_description_html(html):
    return DESCRIPTION_CLEANER.clean_html(html)


class LiarOpener(urllib.FancyURLopener):
    """
    Some APIs (*cough* vimeo *cough) don't allow urllib's user agent
    to access their site.

    (Why on earth would you ban Python's most common url fetching
    library from accessing an API??)
    """
    version = (
        'Mozilla/5.0 (X11; U; Linux x86_64; rv:1.8.1.6) Gecko/20070802 Firefox')


def open_url_while_lying_about_agent(url):
    opener = LiarOpener()
    return opener.open(url)
