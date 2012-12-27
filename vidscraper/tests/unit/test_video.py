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

import datetime
import json
import pickle

from vidscraper.tests.base import BaseTestCase
from vidscraper.tests.unit.test_youtube import CARAMELL_DANSEN_API_DATA
from vidscraper.videos import Video, OEmbedLoaderMixin, VideoFile


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

    def test_serialize(self):
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        # we load the video data this way to avoid depending on the network
        video_data = CARAMELL_DANSEN_API_DATA.copy()
        video_data['tags'] = list(video_data['tags'])
        video._apply(video_data)

        data = video.serialize()
        # verify that the data we expect is in the serialized version.
        self.assertEqual(data['url'], video.url)
        self.assertEqual(data['title'], video.title)
        self.assertEqual(data['publish_datetime'],
                         video.publish_datetime.isoformat())

        # Verify that the data can be deserialized as a video.
        new_video = Video.deserialize(data)
        self.assertEqual(video.url, new_video.url)
        self.assertEqual(dict(video.items()), dict(new_video.items()))

    def test_serialize__json(self):
        """
        Tests that serialized videos can be transformed to and from json.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        # we load the video data this way to avoid depending on the network
        video_data = CARAMELL_DANSEN_API_DATA.copy()
        video_data['tags'] = list(video_data['tags'])
        video._apply(video_data)
        data = video.serialize()
        new_data = json.loads(json.dumps(data))
        self.assertEqual(new_data, data)

    def test_serialize__pickle(self):
        """
        Tests that serialized videos can be pickled and unpickled.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        # we load the video data this way to avoid depending on the network
        video_data = CARAMELL_DANSEN_API_DATA.copy()
        video_data['tags'] = list(video_data['tags'])
        video._apply(video_data)
        data = video.serialize()
        new_data = pickle.loads(pickle.dumps(data, pickle.HIGHEST_PROTOCOL))
        self.assertEqual(new_data, data)

    def test_serialize__files(self):
        """
        Tests that a video with associated files can still be serialized and
        deserialized.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        now = datetime.datetime.now()
        video.files = [VideoFile(url='http://google.com',
                                 expires=now,
                                 length=100,
                                 width=50,
                                 height=50,
                                 mime_type="video/x-flv"),
                       VideoFile(url='http://xkcd.com',
                                 expires=now,
                                 length=75,
                                 width=80,
                                 height=80,
                                 mime_type="application/x-shockwave-flash"),]

        data = video.serialize()
        # verify that the data we expect is in the serialized version.
        self.assertEqual(data['files'][0]['url'], "http://google.com")
        self.assertEqual(data['files'][1]['mime_type'],
                         "application/x-shockwave-flash")
        self.assertEqual(data['files'][0]['expires'], now.isoformat())

        # Verify that the data can be deserialized as a video.
        new_video = Video.deserialize(data)
        self.assertEqual(dict(video.items()), dict(new_video.items()))

    def test_serialize__partial(self):
        """
        Tests that a video with only some fields can still be serialized and
        deserialized.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4",
                      fields=('title', 'embed_code'))
        # we load the video data this way to avoid depending on the network
        video_data = CARAMELL_DANSEN_API_DATA.copy()
        video._apply(video_data)
        data = video.serialize()

        # verify that the data we expect is in the serialized version.
        self.assertEqual(data['url'], video.url)
        self.assertEqual(data['title'], video.title)
        self.assertEqual(data['embed_code'], video.embed_code)

        # Verify that the data can be deserialized as a video.
        new_video = Video.deserialize(data)
        self.assertEqual(video.url, new_video.url)
        self.assertEqual(dict(video.items()), dict(new_video.items()))

    def test_get_file__open(self):
        """
        Tests that open video formats are preferred over proprietary.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        file1 = VideoFile(url='http://google.com',
                          mime_type="video/ogg")
        file2 = VideoFile(url='http://xkcd.com',
                          mime_type="application/x-shockwave-flash")
        file3 = VideoFile(url='http://example.com',
                          mime_type="video/mp4")
        video.files = [file1, file2, file3]
        self.assertEqual(video.get_file(), file1)
        video.files = [file3, file2, file1]
        self.assertEqual(video.get_file(), file1)

    def test_get_file__no_mimetypes(self):
        """
        If none of the videos have mime types, the first file should be
        returned.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        file1 = VideoFile(url='http://google.com')
        file2 = VideoFile(url='http://xkcd.com')
        file3 = VideoFile(url='http://example.com')
        video.files = [file1, file2, file3]
        self.assertEqual(video.get_file(), file1)
        video.files = [file3, file2, file1]
        self.assertEqual(video.get_file(), file3)

    def test_get_file__none(self):
        """
        If there are no files, get_file() should return None.

        """
        video = Video("http://www.youtube.com/watch?v=J_DV9b0x7v4")
        video.files = None
        self.assertTrue(video.get_file() is None)
        video.files = []
        self.assertTrue(video.get_file() is None)


class OEmbedLoaderMixinTestCase(BaseTestCase):
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
        loader = OEmbedLoaderMixin()
        data = loader.get_video_data(response)
        self.assertEqual(set(data), set(loader.fields))
        self.assertEqual(set(data), set(expected_data))
        for key in expected_data:
            self.assertEqual(data[key], expected_data[key])
