import cgi
import re
import urlparse

from vidscraper.decorators import provide_shortmem, parse_url, returns_unicode
from vidscraper import errors
from vidscraper import util


@provide_shortmem
@parse_url
@returns_unicode
def scrape_title(url, shortmem=None):
    try:
        return shortmem['base_etree'].xpath(
            "//div[@class='titlebar-title']/text()")[0]
    except IndexError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_description(url, shortmem=None):
    try:
        details = shortmem['base_etree'].xpath("//p[@id='details-desc']")[0]
        long_details = details.find("span[@id='long-desc']")
        if long_details:
            return util.clean_description_html(
                util.lxml_inner_html(long_details))
        else:
            return util.clean_description_html(util.lxml_inner_html(details))
    except IndexError:
        raise errors.FieldNotFound('Could not find the description field')


# This isn't returning a working url any more :\
@provide_shortmem
@returns_unicode
def scrape_file_url(url, shortmem=None):
    components = urlparse.urlsplit(url)
    params = cgi.parse_qs(components[3])
    doc_id = params['docid'][0]
    return u"http://video.google.com/videofile/%s.flv?docid=%s&itag=5" % (
        doc_id, doc_id)



GOOGLE_VIDEO_REGEX = re.compile(
    r'^https?://video.google.com/videoplay')
SUITE = {
    'regex': GOOGLE_VIDEO_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description}}
