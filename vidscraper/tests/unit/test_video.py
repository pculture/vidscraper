# Copyright 2012 - Participatory Culture Foundation
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

import unittest

from nose.tools import eq_

from vidscraper import auto_scrape
from vidscraper.compat import json
from vidscraper.suites.base import Video


class VideoTestCase(unittest.TestCase):
    def test_items(self):
        video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")

        # Make sure items can be iterated over and that there's one
        # for every field.
        for i, item in enumerate(video.items()):
            eq_(item[0], Video._all_fields[i])

    def test_items_with_fields(self):
        fields = ['title', 'user']
        video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4",
                            fields)

        # Make sure items can be iterated over and that there's one
        # for every field.
        for i, item in enumerate(video.items()):
            eq_(item[0], fields[i])

    def test_to_json(self):
        video = auto_scrape("http://www.youtube.com/watch?v=J_DV9b0x7v4")

        data_json = video.to_json()
        # Verify that we can load the json back into Python.
        json.loads(data_json)
