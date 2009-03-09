# base error for this library
class Error(Exception): pass
# Error if you can't even load the base url
class BaseUrlLoadFailure(Error): pass
# An error if parsing the document with lxml fails
class ParsingError(Error): pass
# An error if the specific field is not found
class FieldNotFound(Error): pass
# Can't identify the url
class CantIdentifyUrl(Error): pass
