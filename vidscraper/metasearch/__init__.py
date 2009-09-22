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

import copy

#from vidscraper import errors
from vidscraper.metasearch.sites import (youtube, blip, vimeo)

AUTOSEARCH_SUITES = [youtube.SUITE, blip.SUITE, vimeo.SUITE]


def auto_search(include_terms, exclude_terms=None,
                order_by='relevant', **kwargs):
    suite_results = []

    for suite in AUTOSEARCH_SUITES:
        if order_by in suite['order_bys']:
            suite_results.append(
                (suite,
                 suite['func'](
                        include_terms=include_terms,
                        exclude_terms=exclude_terms or [],
                        order_by=order_by, **kwargs)))

    return suite_results


def unfriendlysort_results(results, add_suite=True):
    """
    Just slop the results together.
    """
    new_results = []

    video_id = 0
    for suite, this_results in results:
        for result in this_results:
            if add_suite:
                result['suite'] = suite
            result['id'] = video_id
            video_id += 1

        new_results.extend(this_results)

    return new_results


def intersperse_results(results, add_suite=True):
    """
    Intersperse the results of a suite search
    """
    new_results = []

    len_biggest_list = max([len(r[1]) for r in results])

    video_id = 0
    for i in range(len_biggest_list):
        for suite, this_results in results:
            if video_id < len(this_results):
                result = this_results[i]
                if add_suite:
                    result['suite'] = suite
                result['id'] = video_id
                video_id += 1
                new_results.append(result)

    return new_results
