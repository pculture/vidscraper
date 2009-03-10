from lxml import html as lxml_html

def provide_shortmem(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        if shortmem is None:
            shortmem = {}

        return scraper_func(url, shortmem=shortmem, *args, **kwargs)

    return new_scraper_func


def parse_url(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        if not shortmem.get('base_etree'):
            shortmem['base_etree'] = lxml_html.parse(url)

        return scraper_func(url, shortmem=shortmem, *args, **kwargs)

    return new_scraper_func
