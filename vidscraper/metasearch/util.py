def search_string_from_terms(include_terms, exclude_terms=None):
    marked_exclude_terms = ['-' + term for term in exclude_terms or []]
    search_term_list = list(include_terms) + marked_exclude_terms
    search_terms = ' '.join(search_term_list)
    return search_terms
