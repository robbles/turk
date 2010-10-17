import ConfigParser
import yaml

class IniConfig(ConfigParser.ConfigParser):
    """ A slightly nicer version of ConfigParser """
    def __init__(self, filename):
        super(IniConfig, self).__init__()
        self.read(filename)

class YamlConfig(object):
    """ 
    Loads a YAML configuration file and provides convenience
    methods for retrieving nested values.
    """
    def __init__(self, f):
        if isinstance(f, file):
            data = f.read()
        else:
            data = open(f, 'rU').read()

        self.data = yaml.load(data)

    def __getitem__(self, key):
        data = self.data
        try:
            for query in key.split('.'):
                data = data.__getitem__(query)
            return data
        except Exception, e:
            raise KeyError('Config option %s is missing!' % key)

    def get_configs(keys, conf=None):
        all = []
        for key in keys:
            all.append(get_config(key, conf))
        return tuple(all)


class TurkConfig(YamlConfig):
    """ 
    Loads the turk configuration file (turk.yaml) and provides methods for
    working with missing and default values.
    """
    pass

class SupervisorConfig(IniConfig):
    """
    Loads the default supervisord/supervisorctl configuration file and provides
    methods to add and replace values, and to save it back to a temporary file.
    """
    pass


