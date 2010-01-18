import datetime
from lxml import builder
from lxml import etree
from lxml.html import builder as E
import re

from vidscraper.decorators import provide_shortmem, parse_url, returns_unicode


EMaker = builder.ElementMaker()
EMBED = EMaker.embed

@provide_shortmem
@parse_url
@returns_unicode
def scrape_link(url, shortmem=None):
    return 'http://fora.tv%s' % (
        shortmem['base_etree'].xpath(
        "//link[@rel='canonical']/@href")[0],)

@provide_shortmem
@parse_url
@returns_unicode
def scrape_title(url, shortmem=None):
    return shortmem['base_etree'].xpath(
        "//h2[@class='program_title']/text()")[0]

@provide_shortmem
@parse_url
@returns_unicode
def scrape_description(url, shortmem=None):
    return shortmem['base_etree'].xpath(
        "//meta[@name='description']/@content")[0]


@provide_shortmem
@parse_url
@returns_unicode
def scrape_thumbnail_url(url, shortmem=None):
    return shortmem['base_etree'].xpath(
        "//link[@rel='image_src']/@href")[0]

@provide_shortmem
@parse_url
@returns_unicode
def scrape_flash_enclosure_url(url, shortmem=None):
    return shortmem['base_etree'].xpath(
        "//link[@rel='video_src']/@href")[0]

@provide_shortmem
@parse_url
@returns_unicode
def get_embed(url, shortmem=None, EMBED_WIDTH=400, EMBED_HEIGHT=264):
    enclosure_url = scrape_flash_enclosure_url(url, shortmem)
    split_index = enclosure_url.find('?')
    flash_url = enclosure_url[:split_index]
    flashvars = enclosure_url[split_index+1:].replace(
        'cliptype=clip', 'cliptype=full')

    object_children = (
        E.PARAM(name="flashvars", value=flashvars),
        E.PARAM(name='movie', value=flash_url),
        E.PARAM(name="allowFullScreen", value="true"),
        E.PARAM(name="allowscriptaccess", value="always"),
        EMBED(src=flash_url,
              flashvars=flashvars,
              type="application/x-shockwave-flash",
              allowfullscreen="true",
              allowscriptaccess="always",
              width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT)))
    main_object = E.OBJECT(
        width=str(EMBED_WIDTH), height=str(EMBED_HEIGHT), *object_children)

    return etree.tostring(main_object)


@provide_shortmem
@parse_url
def scrape_publish_date(url, shortmem=None):
    return datetime.datetime.strptime(
        shortmem['base_etree'].xpath(
            "//div[@id='programinfo_content']"
            "//dl/dt[3]/following-sibling::dd/text()")[0],
        '%m.%d.%y')


@provide_shortmem
@parse_url
@returns_unicode
def scrape_user(url, shortmem=None):
    return shortmem['base_etree'].xpath(
        "//a[@class='partner_header']/text()")[0]


@provide_shortmem
@parse_url
@returns_unicode
def scrape_user_url(url, shortmem=None):
    return 'http://fora.tv%s' % (shortmem['base_etree'].xpath(
            "//a[@class='partner_header']/@href")[0],)


FORA_REGEX = re.compile('https?://(www\.)?fora\.tv/\d+/\d+/\d+/.+')
SUITE = {
    'regex': FORA_REGEX,
    'funcs': {
        'link': scrape_link,
        'title': scrape_title,
        'description': scrape_description,
        'flash_enclosure_url': scrape_flash_enclosure_url,
        'embed': get_embed,
        'thumbnail_url': scrape_thumbnail_url,
        'publish_date': scrape_publish_date,
        'user': scrape_user,
        'user_url': scrape_user_url
}
}
