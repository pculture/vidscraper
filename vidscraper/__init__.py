from vidscraper import errors
from vidscraper.sites import (
    vimeo, google_video, youtube)

AUTOSCRAPE_SUITES = [
    vimeo.SUITE, google_video.SUITE, youtube.SUITE,
    blip.SUITE]


def scrape_suite(url, suite, fields=None):
    scraped_data = {}

    funcs_map = suite['funcs']
    fields = fields or funcs_map.keys()
    order = suite.get('order')
    if order:
        # remove items in the order that are not in the fields
        for field in set(order).difference(fields):
            order.pop(field)

        # add items that may have been missing from the order but
        # which are in the fields
        order.extend(set(fields).difference(order))
        fields = order

    shortmem = {}
    for field in fields:
        func = funcs_map[field]
        scraped_data[field] = func(url, shortmem=shortmem)

    return scraped_data


def auto_scrape(url, fields=None):
    for suite in AUTOSCRAPE_SUITES:
        if suite['regex'].match(url):
            return scrape_suite(url, suite, fields)

    # If we get here that means that none of the regexes matched, so
    # throw an error
    raise errors.CantIdentifyUrl(
        "No video scraping suite was found that can scrape that url")
