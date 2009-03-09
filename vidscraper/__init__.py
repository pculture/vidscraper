import re
import urlparse

from lxml import etree
from lxml import html as lxml_html
from lxml.html.clean import clean_html


def lxml_inner_html(elt):
    return (elt.text or '') + ''.join(etree.tostring(child) for child in elt)


class VideoScraper(object):
    def __init__(self, website_url, file_url=None,
                 name=None, description=None, tags=None):
        self.website_url = website_url
        self.file_url = file_url
        self.name = name
        self.description = description
        self.tags = tags or []

    def autoset_from_scraped(self):
        if not self.file_url:
            self.file_url = self.scrape_file_url()
        if not self.name:
            self.name = self.scrape_name()
        if not self.description:
            self.description = self.scrape_description()
        if not self.tags:
            self.tags = self.scrape_tags()

    def scrape_file_url(self):
        return None

    def scrape_name(self):
        return None

    def scrape_description(self):
        return None

    def scrape_tags(self):
        return None
        

class YoutubeVideoScraper(VideoScraper):
    def scrape_name(self):
        try:
            return clean_html(
                self.etree.xpath("//div[@id='watch-vid-title']/h1")[0].text)
        except IndexError:
            # maybe add our own exception here
            return None

    def scrape_description(self):
        span_elts = self.etree.xpath(
            "id('watch-video-details-inner')/"
            "div[@class='expand-content']/"
            "div[position()=1]/span")
        return clean_html(
            '\n'.join([etree.tostring(span_elt) for span_elt in span_elts]))


class BlipTvVideoScraper(object):
    def scrape_name(self):
        try:
            return self.etree.xpath("id('EpisodeTitle')/text()")[0]
        except IndexError:
            return None

    def scrape_description(self):
        try:
            return '\n'.join(
                self.etree.xpath("id('EpisodeDescription')/text()")).strip()
        except IndexError:
            return None


VIMEO_SCRAPE_URL = re.compile(r'http://([^/]+\.)?vimeo.com/(\d+)')

class VimeoScraper(VideoScraper):
    def scrape_name(self):
        try:
            return self.etree.xpath(
                "id('header')/div/div[@class='title']/text()")[0]
        except IndexError:
            return None

    def scrape_description(self):
        try:
            return clean_html(
                lxml_inner_html(self.etree.xpath('id("description")')[0]))
        except IndexError:
            return None

    def scrape_url(self):
        vimeo_match = VIMEO_SCRAPE_URL.match(self.website_url)
        if not vimeo_match:
            # raise an exception here
            return None
        video_id = vimeo_match.group(2)
        video_data_url = (
            u"http://www.vimeo.com/moogaloop/load/clip:%s" % video_id)
        vimeo_data = etree.parse(video_data_url)
        req_sig = vimeo_data.find('request_signature').text
        req_sig_expires = vimeo_data.find('request_signature_expires').text
        return "http://www.vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=sd" % (
            video_id, req_sig, req_sig_expires)            


VIMEO_SCRAPE_URL = re.compile(r'http://([^/]+\.)?vimeo.com/(\d+)')

def scrape_vimeo_url(url):
    vimeo_match = VIMEO_SCRAPE_URL.match(url)
    if not vimeo_match:
        # raise an exception here
        return None
    video_id = vimeo_match.group(2)
    video_data_url = (
        u"http://www.vimeo.com/moogaloop/load/clip:%s" % video_id)
    vimeo_data = etree.parse(video_data_url)
    req_sig = vimeo_data.find('request_signature').text
    req_sig_expires = vimeo_data.find('request_signature_expires').text
    return "http://www.vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=sd" % (
        video_id, req_sig, req_sig_expires)            



class GoogleVideoScraper(VideoScraper):
    def scrape_name(self):
        try:
            return self.etree.xpath("//div[@class='titlebar-title']/text()")[0]
        except IndexError:
            return None

    def scrape_description(self):
        try:
            details = google_video_page.xpath("//p[@id='details-desc']")[0]
            long_details = details.find("span[@id='long-desc']")
            if long_details:
                return clean_html(lxml_inner_html(long_details))
            else:
                return clean_html(lxml_inner_html(details))
        except IndexError:
            return None




def scrape_url(url):
    return name, description, categories, website_url
