import tempfile
import atexit
import subprocess
import os

class TestFile():
    """ A named temporary file with initial data. Useful for testing code that
    uses filenames or open files interchangeably. """
    def __init__(self, data):
        temp = tempfile.NamedTemporaryFile()
        temp.file.write(data)
        temp.file.flush()
        temp.seek(0)
        self.original = data
        self.temp = temp

    @property
    def file(self):
        return self.temp.file

    @property
    def name(self):
        return self.temp.name

    @property
    def data(self):
        return self.original


class EnvVar:
    """ Context manager for temporarily setting an environment variable """
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __enter__(self):
        self.original = os.environ[self.name]
        os.putenv(self.name, self.value)
        return self.value

    def __exit__(self, type, value, traceback):
        os.environ[self.name] = self.original



DBUS_UNIX_ADDR = "unix:path=%s"
DBUS_DEFAULT_CONFIG = """
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
    <type>session</type>
    <keep_umask/>
    <listen>%s</listen>

    <policy context="default">
        <allow send_destination="*" eavesdrop="true"/>
        <allow eavesdrop="true"/>
        <allow own="*"/>
    </policy>
</busconfig>
"""

def start_test_bus():
    """
    Starts a D-Bus session bus daemon that will be automatically terminated at exit. 
    A unix socket in a temporary directory is used as the bus address.
    """
    tempdir = tempfile.mkdtemp()
    sock = os.path.join(tempdir, 'dbus.sock')
    address = DBUS_UNIX_ADDR % sock.replace('+', '%2B')
    config = TestFile(DBUS_DEFAULT_CONFIG % address)

    dbus_daemon = subprocess.Popen(['dbus-daemon', '--config-file', config.name], close_fds=True)
    os.environ['DBUS_SESSION_BUS_ADDRESS'] = address

    def cleanup(dbus_daemon, config):
        try:
            dbus_daemon.terminate()
            config.file.close()
            os.unlink(sock)
            os.unlink(tempdir)
        except:
            pass

    # Stop daemon and remove files/directories at exit
    atexit.register(cleanup, dbus_daemon, config)

    return dbus_daemon


