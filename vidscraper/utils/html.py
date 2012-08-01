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

import re

from bs4.dammit import EntitySubstitution


HTML_ENTITY_TO_CHARACTER = EntitySubstitution.HTML_ENTITY_TO_CHARACTER
HTML_ENTITY_TO_CHARACTER_RE = re.compile("|".join(("&{entity};"
                                                   "".format(entity=entity)
                                                   for entity in
                                                   HTML_ENTITY_TO_CHARACTER)))


def _substitute_character(matchobj):
    character = HTML_ENTITY_TO_CHARACTER.get(matchobj.group(0)[1:-1])
    return character


def convert_entities(text):
    """
    Converts HTML entities from the given code to the appropriate characters.
    """
    return unicode(HTML_ENTITY_TO_CHARACTER_RE.sub(_substitute_character,
                                                   text))


def make_embed_code(video_url, flash_qs, width=400, height=264):
    """Generates embed code from a flash enclosure."""
    return u"""<object width="{width}" height="{height}">
    <param name="flashvars" value="{flashvars}">
    <param name="movie" value="{url}">
    <param name="allowFullScreen" value="true">
    <param name="allowscriptaccess" value="always">
    <embed src="{url}" flashvars="{flashvars}" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="{width}" height="{height}">
</object>""".format(width=width, height=height,
                    flashvars=flash_qs, url=video_url)
