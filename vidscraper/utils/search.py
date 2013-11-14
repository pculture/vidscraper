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


def intersperse_results(iterators, max_results):
    """
    Given a list of video iterators, returns an iterator which returns one
    result for each iterator until either all iterators are exhausted or
    ``max_results`` videos have been returned.

    """
    # Make a copy of the original list.
    iterators = list(iterators)
    num_results = 0
    while len(iterators) > 0 and num_results < max_results:
        for iterator in iterators[:]:
            try:
                yield iterator.next()
            except StopIteration:
                iterators.remove(iterator)
            else:
                num_results += 1
