import datetime
import time
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


def returns_unicode(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        result = scraper_func(url, shortmem=shortmem, *args, **kwargs)
    
        if result is not None:
            if not isinstance(result, unicode):
                if shortmem and shortmem.has_key('base_etree'):
                    encoding = shortmem['base_etree'].docinfo.encoding
                else:
                    encoding = 'utf8'
                return result.decode(encoding)
            else:
                return result

    return new_scraper_func

def returns_struct_time(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        result = scraper_func(url, shortmem=shortmem, *args, **kwargs)
    
        if result is not None:
            return datetime.datetime.fromtimestamp(time.mktime(result))

    return new_scraper_func
