from lxml import html as lxml_html

def provide_shortmem(scraper_func, parse_url=True):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        shortmem = shortmem or {}

        if parse_url and not shortmem.get('base_etree'):
            shortmem['base_etree'] = lxml_html.parse(url)

        return scraper_func(url, shortmem=shortmem, *args, **kwargs)

    return new_scraper_func
