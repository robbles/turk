import unittest
from turk.config import *
from turk.utils.testing import TestFile

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.ini_file = TestFile("""
        [section]
        value1 = 11
        value2 = test
        """)

        self.yaml_file = TestFile("""
        value1: 11

        section:
            value2: test
            subsection:
                value3: 22
        """)

    def testYamlConfig_filename(self):
        c = YamlConfig(self.yaml_file.name)

    def testYamlConfig_file(self):
        c = YamlConfig(self.yaml_file.file)

    def testYamlConfig_value(self):
        c = YamlConfig(self.yaml_file.file)
        self.assertEqual(c['value1'], 11)

    def testYamlConfig_subvalues(self):
        c = YamlConfig(self.yaml_file.file)
        self.assertEqual(c['section.value2'], 'test')
        self.assertEqual(c['section.subsection.value3'], 22)

if __name__ == '__main__':
    unittest.main()

