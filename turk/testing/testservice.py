import unittest
import os
from turk.service import *
from turk.utils.testing import TestFile, EnvVar, start_test_bus
from turk.config import TurkConfig
from signal import signal, alarm, SIGALRM


class TestService(unittest.TestCase):

    def setUp(self):
        # Test config file
        self.config_file = TestFile("""
            
        """)

        self.service = Service(self.config_file.name)

    def tearDown(self):
        self.config_file.file.close()

    def testInit(self):
        """ Check to see if initializing a Service succeeds """
        s = Service(self.config_file.name)

    def testRun(self):
        """ Check to see if temporarily running a Service succeeds """
        def interrupt(sig, frame):
            raise KeyboardInterrupt
        signal(SIGALRM, interrupt)
        alarm(1)
        try:
            self.service.run()
        except KeyboardInterrupt:
            pass

    def testGetBusConnection(self):
        """ Test if get_bus_connection returns a valid reference to SessionBus """
        bus = self.service.get_bus_connection()
        self.assertTrue(isinstance(bus, dbus.SessionBus))
        self.assertTrue(bus.get_is_connected())
        


if __name__ == '__main__':
    # We need to start a D-Bus daemon in the background to test this.
    # Should probably be done in setUp, but this is easier.
    dbus_daemon = start_test_bus()

    unittest.main()



