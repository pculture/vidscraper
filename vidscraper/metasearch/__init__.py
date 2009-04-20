import copy

#from vidscraper import errors
from vidscraper.metasearch.sites import (youtube)

AUTOSEARCH_SUITES = [youtube.SUITE]


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


def friendlysort_results(results):
    """
    Intersperse the results of a suite search
    """
    new_sort = []

    pass
