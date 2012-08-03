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

from vidscraper.suites.fora import Suite, ScrapeLoader
from vidscraper.tests.base import BaseTestCase


class ForaTestCase(BaseTestCase):
    def setUp(self):
        self.suite = Suite()


class ForaScrapeTestCase(ForaTestCase):
    def setUp(self):
        ForaTestCase.setUp(self)
        self.url = "http://fora.tv/2011/08/08/Cradle_of_Gold_Hiram_Bingham_and_Machu_Picchu"
        self.loader = ScrapeLoader(self.url)

    def test_valid_urls(self):
        self.assertEqual(self.loader.get_url(), self.url)

    def test_get_video_data(self):
        scrape_file = self.get_data_file('fora/scrape.html')
        response = self.get_response(scrape_file.read())
        data = self.loader.get_video_data(response)
        self.assertTrue(isinstance(data, dict))
        self.assertEqual(set(data), self.loader.fields)
        expected_data = {
            'description': u"Historian Christopher Heaney relates how 100 "
                            "years ago Hiram Bingham stepped into the "
                            "astounding ruins of Machu Picchu, the lost city "
                            "of the Incas.<br/>",
            'flash_enclosure_url': u'http://fora.tv/embedded_player?webhost=fora.tv&clipid=13996&cliptype=clip&ie=f',
            'title': u'Cradle of Gold: Hiram Bingham and Machu Picchu',
            'user_url': u'/partner/National_Geographic_Live',
            'thumbnail_url': u'http://fora.tv/media/thumbnails/13996_320_240.jpg',
            'link': u'http://fora.tv/2011/08/08/Cradle_of_Gold_Hiram_Bingham_and_Machu_Picchu',
            'user': u'National Geographic Live',
            'publish_date': datetime.datetime(2011, 8, 8)
        }
        self.assertDictEqual(data, expected_data)

    def test_process_description_html(self):
        scrape_file = self.get_data_file('fora/scrape2.html')
        response = self.get_response(scrape_file.read())
        data = self.loader.get_video_data(response)
        self.assertEqual(data['description'], "Join Cornel West, Leith "
            "Mullings, Stanley Aronowitz, and Gary Younge as they discuss "
            "Manning Marable's new biography, <i>Malcolm X: A Life of "
            "Reinvention</i>, and the many questions about Malcolm X's life "
            "and assassination that it raises. Manning Marable, who died days "
            "before his book was released, was professor of public affairs, "
            "political science, history and African-American studies and the "
            "founding director of the Institute for Research in "
            "African-American Studies and the Center for the Study of "
            "Contemporary Black History at Columbia University. He is "
            "recognized as one of the most forceful and outspoken scholars of "
            "African-American history and race relations in the United States.")
