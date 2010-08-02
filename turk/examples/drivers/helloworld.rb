#!/usr/bin/env ruby

require 'dbus'

device_id = ENV['DEVICE_ID']
if not device_id
    puts 'DEVICE_ID not found in env!'
    exit
end

path = "/Bridge/Drivers/#{device_id}"
iface = 'org.turkinnovations.turk.Bridge'
service = 'org.turkinnovations.turk.Bridge'

puts "helloworld.rb: listening for updates from #{path}"

bus = DBus::SessionBus.instance
bridge_s = bus.service(service)
bridge = bridge_s.object('/Bridge')
puts bridge.introspect

bridge[iface].RegisterDriver(device_id.to_i)

driver = bridge_s.object(path)
driver.introspect
driver.default_iface = iface

driver.on_signal("Update") do |driver_id, app_id, update|
    puts "update for #{driver_id} from #{app_id}: #{update}"
end

loop = DBus::Main.new
loop << bus
loop.run

