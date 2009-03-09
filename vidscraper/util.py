from lxml import etree

def lxml_inner_html(elt):
    return (elt.text or '') + ''.join(etree.tostring(child) for child in elt)
