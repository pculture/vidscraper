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

from BeautifulSoup import BeautifulStoneSoup

def convert_entities(text):
    """
    Uses :mod:`BeautifulSoup` to convert the HTML entities in some text into
    the appropriate characters.
    """
    return unicode(
        BeautifulStoneSoup(text,
                           convertEntities=BeautifulStoneSoup.HTML_ENTITIES))

def make_embed_code(video_url, flash_qs, width=400, height=264):
    """Generates embed code from a flash enclosure."""
    return u"""<object width="%(width)s" height="%(height)s">
    <param name="flashvars" value="%(flashvars)s">
    <param name="movie" value="%(url)s">
    <param name="allowFullScreen" value="true">
    <param name="allowscriptaccess" value="always">
    <embed src="%(url)s" flashvars="%(flashvars)s" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="%(width)s" height="%(height)s>
</object>""" % {
        'width': width,
        'height': height,
        'flashvars': flash_qs,
        'url': video_url
    }
