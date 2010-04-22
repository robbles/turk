#!/usr/bin/env ruby

require 'dbus'

# Get environment variables
device_id = ENV['DEVICE_ID']
device_address = ENV['DEVICE_ADDRESS'].hex
if not device_id
    puts 'DEVICE_ID not found in env!'
    exit
end

if not device_address
    puts 'DEVICE_ADDRESS not found in env!'
    exit
end

# D-Bus services, interfaces, and paths
path = "/Bridge/Drivers/#{device_id}"
iface = 'org.turkinnovations.turk.Bridge'
service = 'org.turkinnovations.turk.Bridge'

puts "helloworld.rb: listening for updates from #{path}"

# Get Bridge service
bus = DBus::SessionBus.instance
bridge_s = bus.service(service)

# Get Bridge object (the main daemon)
bridge = bridge_s.object('/Bridge')
bridge.introspect

# Register this driver so that the bridge keeps track of updates
bridge[iface].RegisterDriver(device_id.to_i)

# Get a proxy for the new driver object
driver = bridge_s.object(path)
driver.introspect
driver.default_iface = iface

# Get a proxy for the XBee daemon
xbee_path = "/XBeeInterfaces/xbee0"
xbeed = bus.service("org.turkinnovations.xbeed")
xbee = xbeed.object(xbee_path)
xbee.introspect
xbee.default_iface = "org.turkinnovations.xbeed.XBeeInterface"

# Signal handler for new updates
driver.on_signal("Update") do |driver_id, app_id, update|
    puts "update for #{driver_id} from #{app_id}: #{update}"
    data = "Hello, world!".split(//).map {|c| c.to_i}
    xbee.SendData(data, device_address, 1)
end

# Start the loop!
loop = DBus::Main.new
loop << bus
loop.run

