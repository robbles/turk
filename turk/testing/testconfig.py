import unittest
from turk.config import *
import tempfile

class TestFile():
    """ A named temporary file with initial data. Useful for testing code that
    uses filenames or open files interchangeably. """
    def __init__(self, data):
        temp = tempfile.NamedTemporaryFile()
        temp.file.write(data)
        temp.file.flush()
        temp.seek(0)
        self.data = data
        self.temp = temp

    @property
    def file(self):
        return self.temp.file

    @property
    def name(self):
        return self.temp.name


class TestConfig(unittest.TestCase):

    def setUp(self):
        ini_str = """
        [section]
        value1 = 11
        value2 = test
        """
        self.ini_file = TestFile(ini_str)

        yaml_str = """
        value1: 11

        section:
            value2: test
            subsection:
                value3: 22
        """
        self.yaml_file = TestFile(yaml_str)

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

