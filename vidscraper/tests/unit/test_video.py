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
import json

from vidscraper.tests.base import BaseTestCase
from vidscraper.tests.unit.test_youtube import CARAMELL_DANSEN_API_DATA
from vidscraper.videos import Video, OEmbedMixin


class VideoTestCase(BaseTestCase):
    def test_items(self):
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")

        # Make sure items can be iterated over and that there's one
        # for every field.
        for i, item in enumerate(video.items()):
            self.assertEqual(item[0], Video._all_fields[i])

    def test_items_with_fields(self):
        fields = ['title', 'user']
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4",
                            fields=fields)

        # Make sure items can be iterated over and that there's one
        # for every field.
        for i, item in enumerate(video.items()):
            self.assertEqual(item[0], fields[i])

    def test_json(self):
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        # we load the video data this way to avoid depending on the network
        video_data = CARAMELL_DANSEN_API_DATA.copy()
        video_data['tags'] = list(video_data['tags'])
        video._apply(video_data)

        data_json = video.to_json()
        # verify that the data we expect is in the JSON output
        self.assertTrue(video.url in data_json)
        self.assertTrue(video.title in data_json)
        self.assertTrue(video.publish_datetime.isoformat() in data_json)

        # Verify that we can also load that data as a video.
        new_video = Video.from_json(data_json)
        self.assertEqual(video.url, new_video.url)
        self.assertEqual(dict(video.items()), dict(new_video.items()))


class OEmbedMixinTestCase(BaseTestCase):
    def test_get_video_data(self):
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
        loader = OEmbedMixin()
        data = loader.get_video_data(response)
        self.assertEqual(set(data), set(loader.fields))
        self.assertEqual(set(data), set(expected_data))
        for key in expected_data:
            self.assertEqual(data[key], expected_data[key])
