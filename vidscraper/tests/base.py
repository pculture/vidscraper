import os

from requests.models import Response
import unittest2

import vidscraper


class BaseTestCase(unittest2.TestCase):
    def _data_file_path(self, data_file):
        root = os.path.abspath(os.path.dirname(vidscraper.__file__))
        return os.path.join(root, 'tests', 'data', data_file)

    def get_data_file(self, data_file):
        return open(self._data_file_path(data_file))

    def get_response(self, content, code=200):
        response = Response()
        response._content = content
        response.status_code = code
        return response

    def assertDictEqual(self, data, expected_data, msg=None):
        self.assertEqual(set(data), set(expected_data))
        for key in data:
            self.assertEqual(data[key], expected_data[key],
                             u'value for {key} not equal:\n'
                             u'{value} != {expected}'.format(
                                key=key, value=data[key],
                                expected=expected_data[key]))
