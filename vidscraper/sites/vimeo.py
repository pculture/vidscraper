import re
import urllib

from lxml import builder
from lxml import etree
from lxml.html import builder as E
from lxml.html import tostring
from lxml.html.clean import clean_html

from vidscraper.decorators import provide_shortmem, parse_url, returns_unicode
from vidscraper import errors
from vidscraper import util


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
            "id('header')/div/div[@class='title']")[0].text_content().strip()
    except IndexError:
        raise errors.FieldNotFound('Could not find the title field')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_description(url, shortmem=None):
    try:
        return util.clean_description_html(
            util.lxml_inner_html(
                shortmem['base_etree'].xpath(
                    'id("description")')[0]).strip())
    except IndexError:
        raise errors.FieldNotFound('Could not find the description field')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_file_url(url, shortmem=None):
    vimeo_match = VIMEO_REGEX.match(url)
    video_id = vimeo_match.group(2)
    video_data_url = (
        u"http://www.vimeo.com/moogaloop/load/clip:%s" % video_id)
    vimeo_data = etree.parse(video_data_url)
    req_sig = vimeo_data.find('request_signature').text
    req_sig_expires = vimeo_data.find('request_signature_expires').text
    file_url = "http://www.vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=sd" % (
        video_id, req_sig, req_sig_expires)
    shortmem['file_url'] = file_url
    return file_url


@provide_shortmem
@parse_url
@returns_unicode
def get_flash_enclosure_url(url, shortmem=None):
    vimeo_match = VIMEO_REGEX.match(url)
    video_id = vimeo_match.group(2)
    return 'http://vimeo.com/moogaloop.swf?clip_id=' + video_id


@provide_shortmem
@returns_unicode
def get_embed(url, shortmem=None, width=EMBED_WIDTH, height=EMBED_HEIGHT):
    get_dict = {'server': 'vimeo.com',
                'show_title': 1,
                'show_byline': 1,
                'show_portrait': 0,
                'color': '',
                'fullscreen': 1}

    get_dict['clip_id'] = VIMEO_REGEX.match(url).groupdict()['video_id']

    flash_url = 'http://vimeo.com/moogaloop.swf?' + urllib.urlencode(get_dict)

    object_children = (
        E.PARAM(name="allowfullscreen", value="true"),
        E.PARAM(name="allowscriptaccess", value="always"),
        E.PARAM(name="movie", value=flash_url),
        EMBED(src=flash_url,
              type="application/x-shockwave-flash",
              allowfullscreen="true",
              allowscriptaccess="always",
              width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT)))
    main_object = E.OBJECT(
        width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT), *object_children)

    return tostring(main_object)


VIMEO_REGEX = re.compile(r'https?://([^/]+\.)?vimeo.com/(?P<video_id>\d+)')
SUITE = {
    'regex': VIMEO_REGEX,
    'funcs': {
        'title': scrape_title,
        'description': scrape_description,
        'file_url': scrape_file_url,
        'flash_enclosure_url': get_flash_enclosure_url,
        'embed': get_embed},
    'order': ['title', 'description', 'file_url', 'embed']}
            
