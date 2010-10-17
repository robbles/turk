import unittest
import os
from turk.manager import *
from turk.utils.testing import TestFile, start_test_bus
from turk.config import TurkConfig
from signal import signal, alarm, SIGALRM


class TestProcessManager(unittest.TestCase):

    def setUp(self):
        # Test config file
        self.config_file = TestFile("""

        manager:
            drivers: ./
            autostart: [
                {'path':'/bin/cat', 'args':[], 'env':{}},
                {'path':'/bin/cat', 'args':[], 'env':{}}
            ]
            
        """)

        self.manager = ProcessManager(self.config_file.name)

    def tearDown(self):
        self.config_file.file.close()
        self.manager.remove_from_connection()

    def testInitialize(self):
        """ Test ProcessManager.initialize() """
        self.manager.initialize()

        # Check for initialized fields
        self.assertTrue(isinstance(self.manager.managed_processes, dict))
        self.assertTrue(isinstance(self.manager.driver_dir, str))
        self.assertTrue(isinstance(self.manager.autostart, list))

    def testCreateId(self):
        """ Test uniqueness of ProcessManager.create_id() """
        id1 = self.manager.create_id()
        id2 = self.manager.create_id()
        self.assertFalse(id1 == id2)



if __name__ == '__main__':
    # We need to start a D-Bus daemon in the background to test this.
    # Should probably be done in setUp, but this is easier.
    dbus_daemon = start_test_bus()

    unittest.main()



