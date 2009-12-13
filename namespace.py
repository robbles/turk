import string

# D-BUS services and interfaces
TURK_BRIDGE_SERVICE = "org.turkinnovations.core.Bridge"
TURK_BRIDGE_INTERFACE = "org.turkinnovations.core.Bridge"
TURK_CONFIG_INTERFACE = "org.turkinnovations.core.Configuration"
TURK_SPAWNER_SERVICE = "org.turkinnovations.core.Spawner"
TURK_SPAWNER_INTERFACE = "org.turkinnovations.core.Spawner"

# Driver REST API
TURK_CLOUD_DRIVER_INFO = string.Template('http://drivers.turkinnovations.com/drivers/${id}.xml')
TURK_CLOUD_DRIVER_STORAGE = string.Template('http://drivers.turkinnovations.com/files/drivers/${filename}')
# XML Namespace
TURK_CONFIG_NAMESPACE = "http://turkinnovations.com/protocol/1.0/config"
