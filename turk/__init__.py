import string

# D-BUS services and interfaces
TURK_BRIDGE_SERVICE = "org.turkinnovations.turk.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.turk.Bridge"
TURK_CONFIG_INTERFACE = "org.turkinnovations.turk.Configuration"
TURK_SPAWNER_SERVICE = "org.turkinnovations.turk.Spawner"
TURK_SPAWNER_INTERFACE = "org.turkinnovations.turk.Spawner"
TURK_DRIVER_ERROR = "org.turkinnovations.turk.DriverError"

# Driver REST API
TURK_CLOUD_DRIVER_INFO = string.Template('http://drivers.turkinnovations.com/drivers/${id}.xml')
TURK_CLOUD_DRIVER_STORAGE = string.Template('http://drivers.turkinnovations.com/files/drivers/${filename}')

# Driver/Worker -> App POST API
#TURK_CLOUD_APP_POST = string.Template('http://apps.turkinnovations.com/apps/${id}/')
TURK_CLOUD_APP_POST = string.Template('http://localhost:8000/apps/${id}/update/')

# XMPP Namespace
TURK_CONFIG_NAMESPACE = "http://turkinnovations.com/protocol/1.0/config"

# Default values for config (used when keys are left out)
DEFAULT = {
    'turkctl': {
        'pidfile': '/etc/turk/turk.pid',
        'daemon': False,
    },
    'bridge': {
        'server': 'macpro.local',
        'port': 5222,
        'username': 'platform@macpro.local',
        'password': 'password',
        'bus': 'SessionBus',
        'daemon': False,
        'debug': True,
    },
    'spawner': {
        'daemon': False,
        'debug': False,
        'autostart': [],
        'drivers': '/usr/share/turk/drivers',
        'bus': 'SessionBus',
    },
    'xbeed': {
        'name': 'xbee0',
        'bus': 'SessionBus',
        'port': '/dev/ttyUSB0',
        'baudrate': 9600,
        'escaping': True,
        'debug': True,
        'daemon': False,
    }
}

def get_config(conf, key):
    """
    Uses a dot-separated string to look up values from the configuration file.
    Falls back on the default values if not found.
    """
    value = conf
    try:
        for query in key.split('.'):
            value = value.__getitem__(query)
        return value
    except Exception, e:
        if conf is not DEFAULT:
            return get_config(DEFAULT, key)
        else:
            raise KeyError(query)

def get_configs(conf, keys, prefix=''):
    all = []
    for key in keys:
        all.append(get_config(conf, '.'.join([prefix, key])))
    return all



