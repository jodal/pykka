import unittest

import pykka

class VersionTest(unittest.TestCase):
    def test_version_with_two_components(self):
        pykka.VERSION = (1, 2)
        self.assertEqual('1.2', pykka.get_version())

    def test_version_with_three_components(self):
        pykka.VERSION = (1, 2, 3)
        self.assertEqual('1.2.3', pykka.get_version())
