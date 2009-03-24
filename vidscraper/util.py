from lxml import etree
from lxml.html import clean

DESCRIPTION_CLEANER = clean.Cleaner(
    remove_tags=['img', 'table', 'tr', 'td', 'th'])


def lxml_inner_html(elt):
    return (elt.text or '') + ''.join(etree.tostring(child) for child in elt)

def clean_description_html(html):
    return DESCRIPTION_CLEANER.clean_html(html)
