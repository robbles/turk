import string
import logging
import os
import yaml
from os.path import join, abspath, dirname, basename

INSTALL_DIR = abspath(dirname(__file__))

# D-BUS services and interfaces
TURK_BRIDGE_SERVICE = "org.turkinnovations.turk.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.turk.Bridge"
TURK_DRIVER_INTERFACE = "org.turkinnovations.turk.Driver"
TURK_SPAWNER_SERVICE = "org.turkinnovations.turk.Spawner"
TURK_SPAWNER_INTERFACE = "org.turkinnovations.turk.Spawner"
TURK_DRIVER_ERROR = "org.turkinnovations.turk.DriverError"

# XMPP Namespace
TURK_XMPP_NAMESPACE = "http://turkinnovations.com/protocol"

# Default config file (used when keys are left out)
DEFAULT_CONF_FILE = join(INSTALL_DIR, 'skel', 'turk.yaml')

def load_config(config_file):
    """
    Loads the Turk configuration file. Project settings like "name" and "dir"
    are guessed if missing, and project and install directories are substituted
    in for %(here)s and %(install)s.
    """
    if not config_file:
        config_file = DEFAULT_CONF_FILE

    # Load just the text
    if isinstance(config_file, file):
        config_text = config_file.read()
        project_dir = dirname(config_file.name)
    else:
        config_text = open(config_file, 'rU').read()
        project_dir = dirname(config_file)

    # Do substitution on plain text
    config_text = config_text % {
        'here' : project_dir,
        'install' : INSTALL_DIR,
    }

    # Parse the configuration
    config = yaml.load(config_text)

    # Guess some default project values if empty or not set explicitly
    if not config.get('project'):
        config['project'] = {}

    if not config['project'].get('name'):
        config['project']['name'] = basename(project_dir)

    if not config['project'].get('dir'):
        config['project']['dir'] = project_dir
    
    return config


def get_config(key, conf=None, substitute=False):
    """
    Uses a dot-separated string to look up values from the configuration file.
    Falls back on the default values if not found. 
    """
    temp = conf if conf else DEFAULTS
    try:
        for query in key.split('.'):
            temp = temp.__getitem__(query)
        return temp
    except Exception, e:
        if conf != DEFAULTS:
            return get_config(key)
        else:
            # Should only happen if unknown option is requested or
            # DEFAULT_CONF_FILE is busted
            raise KeyError('Config option %s is missing!' % key)

def get_configs(keys, conf=None):
    all = []
    for key in keys:
        all.append(get_config(key, conf))
    return tuple(all)


def init_logging(module, conf=None):
    conf = conf if conf else DEFAULTS
    logfile, logformat, loglevel = get_configs(['log.file', 'log.format', 'log.level'], conf)

    # TODO: add log to file

    logging.basicConfig(format=logformat)
    log = logging.getLogger(module)
    log.setLevel(getattr(logging, loglevel))

    return log


# Load the default configuration as a fallback
DEFAULTS = load_config(DEFAULT_CONF_FILE)



