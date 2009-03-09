def scrape_suite(url, suite, fields=None):
    scraped_data = {}

    funcs_map = suite['funcs']
    fields = fields or funcs_map.keys()
    order = suite.get('order')
    if order:
        # remove items in the order that are not in the fields
        for field in set(order).difference(fields):
            order.pop(field)

        # add items that may have been missing from the order but
        # which are in the fields
        order.extend(set(fields).difference(order))
        fields = order

    shortmem = {}
    for field in fields:
        try:
            func = funcs_map[field]
            scraped_data[field] = func(url, shortmem=shortmem)
        except KeyError:
            # should probably only pass conditionally
            pass

    return scraped_data
