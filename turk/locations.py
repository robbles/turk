import string

# D-BUS services and interfaces
TURK_BRIDGE_SERVICE = "org.turkinnovations.turk.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.turk.Bridge"
TURK_CONFIG_INTERFACE = "org.turkinnovations.turk.Configuration"
TURK_SPAWNER_SERVICE = "org.turkinnovations.turk.Spawner"
TURK_SPAWNER_INTERFACE = "org.turkinnovations.turk.Spawner"

# Driver REST API
TURK_CLOUD_DRIVER_INFO = string.Template('http://drivers.turkinnovations.com/drivers/${id}.xml')
TURK_CLOUD_DRIVER_STORAGE = string.Template('http://drivers.turkinnovations.com/files/drivers/${filename}')

# Driver/Worker -> App POST API
TURK_CLOUD_APP_POST = string.Template('http://apps.turkinnovations.com/apps/${id}/')

# XMPP Namespace
TURK_CONFIG_NAMESPACE = "http://turkinnovations.com/protocol/1.0/config"

