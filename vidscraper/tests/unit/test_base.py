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

import urllib

from vidscraper.suites import OEmbedMethod
from vidscraper.videos import Video
from vidscraper.tests.base import BaseTestCase


class OEmbedMethodTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.endpoint = "http://blip.tv/oembed/"
        self.method = OEmbedMethod(self.endpoint)
        self.base_url = "http://blip.tv/djangocon/lightning-talks-day-1-4167881"
        self.video = Video(self.base_url)

    def test_get_url(self):
        escaped_url = urllib.quote_plus(self.video.url)
        expected = "%s?url=%s" % (self.endpoint, escaped_url)
        result = self.method.get_url(self.video)
        self.assertEqual(result, expected)

    def test_process(self):
        expected_data = {
            'title': "Scaling the World's Largest Django Application",
            'embed_code': '<iframe src="http://blip.tv/play/AYH9xikC.html" '
                            'width="640" height="510" frameborder="0" '
                            'allowfullscreen></iframe><embed '
                            'type="application/x-shockwave-flash" '
                            'src="http://a.blip.tv/api.swf#AYH9xikC" '
                            'style="display:none"></embed>',
            'thumbnail_url': "http://a.images.blip.tv/Robertlofthouse-ScalingTheWorldsLargestDjangoApplication538.png",
            'user': 'djangocon',
            'user_url': 'http://blip.tv/djangocon',
        }
        oembed_file = self.get_data_file('oembed.json')
        response = self.get_response(oembed_file.read())
        data = self.method.process(response)
        self.assertEqual(set(data), set(self.method.fields))
        self.assertEqual(set(data), set(expected_data))
        for key in expected_data:
            self.assertEqual(data[key], expected_data[key])
