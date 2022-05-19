import unittest

from jobs.crawler import get_name


class TestSimple(unittest.TestCase):

    def test_get_name(self):
        self.assertEqual(get_name(), "library-data-feeds")


if __name__ == '__main__':
    unittest.main()
