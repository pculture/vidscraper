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

def terms_from_search_string(search_string):
    """
    Returns a ``(include_terms, exclude_terms)`` tuple, where ``include_terms``
    and ``exclude_terms`` are sets of strings. Currently extremely naive;
    doesn't handle quoted terms.

    """
    terms = set(search_string.split())
    exclude_terms = set((term for term in terms if term.startswith('-')))
    include_terms = terms - exclude_terms
    stripped_exclude_terms = set([term.lstrip('-') for term in exclude_terms])
    return include_terms, stripped_exclude_terms


def search_string_from_terms(include_terms, exclude_terms):
    """
    
    """
    marked_exclude_terms = ['-' + term for term in exclude_terms or []]
    search_term_list = list(include_terms) + marked_exclude_terms
    search_string = ' '.join(search_term_list)
    return search_string


def intersperse_results(suite_dict, max_results):
    """
    Given a dictionary of suite results, returns an iterator which cycles
    through the suites, yielding one result per suite until either all suite
    results are exhausted or ``max_results`` results have been returned.

    """
    iterators = [iter(i) for i in suite_dict.values()]
    num_results = 0
    while len(iterators) > 0 and num_results < max_results:
        for iterator in iterators[:]:
            try:
                yield iterator.next()
            except StopIteration:
                iterators.remove(iterator)
            else:
                num_results += 1
