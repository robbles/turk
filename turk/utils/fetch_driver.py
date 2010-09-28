import urllib2
from xml.dom.minidom import parseString
import turk
import os
import logging

log = logging.getLogger(__file__)

def fetch_driver(self, url, driver_id):
    """ 
    Fetches a driver file from a web server, using driver_id to
    identify the location.
    Expects an XML response of the form:
        <driver file="{URL}"/>
    where URL is a valid path to a driver executable to download.
    """
    try:
        driver_info = parseString(urllib2.urlopen(url).read())
    except urllib2.HTTPError, err:
        log.debug("Couldn't fetch driver metadata - HTTP error %d" % err.getcode())
        return None

    driver = driver_info.getElementsByTagName('driver')[0]
    if not driver:
        log.debug('Driver %d not found' % driver_id)
        return None
    filename = driver.getAttribute('file')
    log.debug("fetching: " + turk.TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename))

    try:
        driverdata = urllib2.urlopen(turk.TURK_CLOUD_DRIVER_STORAGE.substitute(filename=filename))
    except urllib2.HTTPError, err:
        log.debug("Couldn't fetch driver files - HTTP error %d" % err.getcode())
        return None

    path = ''.join([self.driver_dir, '/', filename])

    if not os.path.exists(filename):
        driverfile = open(filename, 'wB')
        driverfile.write(driverdata.read())
        driverfile.close()
        os.chmod(filename, 0755)
        log.debug("saved driver data successfully")
    else:
        log.debug("Driver file already exists! Leaving original")
    return filename



