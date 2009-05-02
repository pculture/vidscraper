import cgi
import re
import urlparse

from lxml import builder
from lxml import etree
from lxml.html import builder as E
from lxml.html import tostring
from lxml.html.clean import clean_html

from vidscraper.decorators import provide_shortmem, parse_url, returns_unicode
from vidscraper import errors, util


EMaker = builder.ElementMaker()
EMBED = EMaker.embed

EMBED_WIDTH = 425
EMBED_HEIGHT = 344


@provide_shortmem
@parse_url
@returns_unicode
def scrape_title(url, shortmem=None):
    try:
        return shortmem['base_etree'].xpath(
            "//div[@id='watch-vid-title']/h1")[0].text
    except IndexError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_description(url, shortmem=None):
    span_elts = shortmem['base_etree'].xpath(
        "id('watch-video-details-inner')/"
        "div[@class='expand-content']/"
        "div[position()=1]/span")
    return util.clean_description_html(
        '\n'.join([etree.tostring(span_elt) for span_elt in span_elts])).strip()


@provide_shortmem
@returns_unicode
def get_embed(url, shortmem=None, width=EMBED_WIDTH, height=EMBED_HEIGHT):
    video_id = cgi.parse_qs(urlparse.urlsplit(url)[3])['v'][0]

    flash_url = 'http://www.youtube.com/v/%s&hl=en&fs=1' % video_id

    object_children = (
        E.PARAM(name="movie", value=flash_url),
        E.PARAM(name="allowFullScreen", value="true"),
        E.PARAM(name="allowscriptaccess", value="always"),
        EMBED(src=flash_url,
              type="application/x-shockwave-flash",
              allowfullscreen="true",
              allowscriptaccess="always",
              width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT)))
    main_object = E.OBJECT(
        width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT), *object_children)

    return tostring(main_object)


@provide_shortmem
@returns_unicode
def get_thumbnail_url(url, shortmem=None):
    video_id = cgi.parse_qs(urlparse.urlsplit(url)[3])['v'][0]
    return 'http://img.youtube.com/vi/%s/default.jpg' % video_id


YOUTUBE_REGEX = re.compile(r'http://([^/]+\.)?youtube.com/(?:watch)?\?v=')
SUITE = {
    'regex': YOUTUBE_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description,
        'embed': get_embed,
        'thumbnail_url': get_thumbnail_url}}
