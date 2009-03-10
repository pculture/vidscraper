import re

from lxml import etree
from lxml.html.clean import clean_html

from vidscraper.decorators import provide_shortmem, parse_url
from vidscraper import errors


@provide_shortmem
@parse_url
def scrape_title(url, shortmem=None):
    try:
        return shortmem['base_etree'].xpath(
            "//div[@id='watch-vid-title']/h1")[0].text
    except IndexError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_url
def scrape_description(url, shortmem=None):
    span_elts = shortmem['base_etree'].xpath(
        "id('watch-video-details-inner')/"
        "div[@class='expand-content']/"
        "div[position()=1]/span")
    return clean_html(
        '\n'.join([etree.tostring(span_elt) for span_elt in span_elts])).strip()


YOUTUBE_REGEX = re.compile(
    r'http://([^/]+\.)?youtube.com/(?!get_video(\.php)?)')
SUITE = {
    'regex': YOUTUBE_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description}}
