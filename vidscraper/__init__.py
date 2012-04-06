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

import sys
from optparse import OptionParser

from vidscraper.suites import registry
from vidscraper.videos import Video, VideoSearch, VideoFeed


__version__ = '0.6-a'


def handles_video_url(url):
    """
    Returns True if vidscraper can scrape this url, and False if
    it can't.

    """
    return any((suite.handles_video_url(url) for suite in registry.suites))


def handles_feed_url(url):
    """
    Returns True if vidscraper can treat this url as a feed, and False if
    it can't.

    """
    return any((suite.handles_feed_url(url) for suite in registry.suites))


def auto_scrape(url, fields=None, api_keys=None):
    """
    Calls the default registry's :meth:`~.SuiteRegistry.get_video` method with
    the given parameters, then loads and returns the :class:`.Video`.

    """
    video = registry.get_video(url, fields=fields, api_keys=api_keys)
    video.load()
    return video


auto_feed = registry.get_feed
auto_search = registry.get_searches


# fetchvideo -> auto_scrape(url, fields, api_keys)


class VidscraperCommandHandler(object):
    """Command line handler for vidscraper.

    This exposes functions in this module to the command line giving
    vidscraper command line utility.

    Subcommands are implemented in ``handle_SUBCOMMAND`` methods.  See
    ``handle_video`` and ``handle_help`` for examples.
    """

    usage = "%prog [command] [options]"

    def get_commands(self):
        """Returns a list of subcommands implemented."""
        return [mem.replace("handle_", "")
                for mem in dir(self)
                if mem.startswith("handle_")]

    def build_parser(self, usage):
        """Builds the parser with universal bits."""
        parser = OptionParser(usage=usage, version=__version__)
        return parser

    def handle_video(self):
        """Handler for auto_scrape."""
        parser = self.build_parser("%prog video [options] URL")
        parser.add_option("--fields", dest="fields",
                          help="comma-separated list of fields to retrieve. "
                          "e.g. --fields=a,b,c")
        parser.add_option("--apikeys", dest="api_keys",
                          help="api keys comma separated. "
                          "e.g. --apikeys=key:val,key2:val")
        (options, args) = parser.parse_args()

        if len(args) == 0:
            parser.error("URL needed.")

        if options.fields:
            fields = options.fields.split(",")
        else:
            fields = None

        if options.api_keys:
            api_keys = dict(mem.split(":", 1)
                            for mem in options.api_keys.split(","))
        else:
            api_keys = None

        for arg in args:
            print "Scraping %s" % arg
            video = auto_scrape(arg, fields=fields, api_keys=api_keys)
            print video.to_json(indent=2, sort_keys=True)

        return 0

    def handle_help(self, error=None):
        """Handles help."""
        parser = self.build_parser("%prog [command]")
        parser.print_help()
        if error:
            print ""
            print "Error: " + error
        print ""
        print "Commands:"
        for cmd in self.get_commands():
            print "    %s" % cmd
        return 0

    def main(self):
        if len(sys.argv) <= 1 or sys.argv[1] in ("-h", "--help"):
            return self.handle_help()

        try:
            cmd = sys.argv.pop(1)
            cmd = "".join(c for c in cmd if c.isalpha())
            handler = getattr(self, "handle_%s" % cmd)
        except AttributeError:
            return self.handle_help(error='%s is not a valid command.' % cmd)

        return handler()

if __name__ == "__main__":
    sys.exit(VidscraperCommandHandler().main())
