import re

from lxml import etree
from lxml.html.clean import clean_html

from vidscraper.decorators import provide_shortmem, parse_url
from vidscraper import errors
from vidscraper import util


@provide_shortmem
@parse_url
def scrape_title(url, shortmem=None):
    try:
        return shortmem['base_etree'].xpath(
            "id('header')/div/div[@class='title']/text()")[0]
    except IndexError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_url
def scrape_description(url, shortmem=None):
    try:
        return clean_html(
            util.lxml_inner_html(
                shortmem['base_etree'].xpath(
                    'id("description")')[0]).strip())
    except IndexError:
        raise errors.FieldNotFound('Could not find the description field')


@provide_shortmem
@parse_url
def scrape_file_url(url, shortmem=None):
    vimeo_match = VIMEO_REGEX.match(url)
    video_id = vimeo_match.group(2)
    video_data_url = (
        u"http://www.vimeo.com/moogaloop/load/clip:%s" % video_id)
    vimeo_data = etree.parse(video_data_url)
    req_sig = vimeo_data.find('request_signature').text
    req_sig_expires = vimeo_data.find('request_signature_expires').text
    return "http://www.vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=sd" % (
        video_id, req_sig, req_sig_expires)            


VIMEO_REGEX = re.compile(r'http://([^/]+\.)?vimeo.com/(\d+)')
SUITE = {
    'regex': VIMEO_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description,
        'file_url': scrape_file_url}}
            
