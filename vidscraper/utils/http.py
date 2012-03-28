# Miro - an RSS based video player application
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

import random
import time
import urllib

from lxml import etree
from lxml.html import clean

DESCRIPTION_CLEANER = clean.Cleaner(
    remove_tags=['img', 'table', 'tr', 'td', 'th'])


def lxml_inner_html(elt):
    try:
        return (elt.text or '') + ''.join(
            etree.tostring(child) for child in elt)
    except UnicodeError:
        return u''


# TODO: Rename this to sanitize? Should this really be done with an xml cleaner?
def clean_description_html(html):
    if not html:
        return html
    return DESCRIPTION_CLEANER.clean_html(html)


# TODO: Is this still required?
class LiarOpener(urllib.FancyURLopener):
    """
    Some APIs (*cough* vimeo *cough*) don't allow urllib's user agent
    to access their site.

    (Why on earth would you ban Python's most common url fetching
    library from accessing an API??)
    """
    version = (
        'Mozilla/5.0 (X11; U; Linux x86_64; rv:1.8.1.6) Gecko/20070802 Firefox')


def open_url_while_lying_about_agent(url):
    opener = LiarOpener()
    return opener.open(url)

def random_exponential_backoff(denominator):
    i = 1.0
    while True:
        sleep_range = (i ** 2) / denominator
        sleep_time = random.uniform(0, sleep_range)
        time.sleep(sleep_time)
        i += 1
        yield sleep_time
