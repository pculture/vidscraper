# Copyright 2009 - Participatory Culture Foundation
# 
# This file is part of vidscraper.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import datetime
import time
from lxml import html as lxml_html
from lxml.etree import _ElementUnicodeResult

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
            elif isinstance(result, _ElementUnicodeResult):
                return unicode(result)
            else:
                return result


    return new_scraper_func

def returns_struct_time(scraper_func):
    def new_scraper_func(url, shortmem=None, *args, **kwargs):
        result = scraper_func(url, shortmem=shortmem, *args, **kwargs)
    
        if result is not None:
            return datetime.datetime.fromtimestamp(time.mktime(result))

    return new_scraper_func
