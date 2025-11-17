import unittest
from urllib.parse import urlparse, parse_qs
from webscraper.webscraper import extract_no


class TestWebScraperFunctions(unittest.TestCase):

    def test_extract_no(self):
        url = 'http://example.com?no=5'
        self.assertEqual(extract_no(url), '5')

        url = 'http://example.com'
        self.assertIsNone(extract_no(url))

        url = 'http://example.com?another_param=xyz&no=10'
        self.assertEqual(extract_no(url), '10')


if __name__ == '__main__':
    unittest.main()
    