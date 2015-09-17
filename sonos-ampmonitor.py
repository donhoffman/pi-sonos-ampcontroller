#!/usr/bin/python
# -*- coding: utf-8 -*-

# What this does:
#
# Start this as a daemon. It connects to your Sonos Connect and 
# whenever the Sonos Connect starts playing music, radio or whatever,
# it turns on the Receiver, switches to the appropriate input, sets the volume
# and changes to the Sound Program you want to (e.g. "5ch Stereo").
#
# If you set the standby time of the Receiver to 20 minutes, you'll have a
# decent instant-on solution for your Sonos Connect - it behaves just like
# one of Sonos' other players.
#
# Optimized for minimum use of resources. I leave this running on a Raspberry
# Pi at my place.
#
# Before installing it as a daemon, try it out first: Adapt the settings in the
# script below. Then just run the script. It'll auto-discover your Sonos
# Connect. If that fails (e.g. because you have more than one Connect in your
# home or for other reasons), you can use the UID of your Sonos Connect as the
# first and only parameter of the script. The script will output all UIDs
# neatly for your comfort.
#
# Software prerequisites:
# - sudo pip install soco



import os
import sys
import time
import re
import urllib, urllib2
import telnetlib
import soco
import Queue
import signal
from datetime import datetime
from subprocess import call

__version__     = '0.3'



# --- Please adapt these settings ---------------------------------------------
OFF_WAIT_TIME = 60 * 5
IR_DEVICE = "onkyo"
IR_OFF_COMMAND = 'power'
IR_ON_COMMAND = 'power'



# basic in/out with the receiver
def send_once(device_id, command):
    call(['irsend', 'SEND_ONCE', device_id, command])
    
def send_off():
    print u"Sending IR OFF.".encode('utf-8')
    send_once(IR_DEVICE, IR_OFF_COMMAND)

def send_on():
    print u"Sending IR ON.".encode('utf-8')
    send_once(IR_DEVICE, IR_ON_COMMAND)

def auto_flush_stdout():
    unbuffered = os.fdopen(sys.stdout.fileno(), 'w', 0)
    sys.stdout.close()
    sys.stdout = unbuffered

def handle_sigterm(*args):
    global break_loop
    print u"SIGTERM caught. Exiting gracefully.".encode('utf-8')
    break_loop = True



# --- Discover SONOS zones ----------------------------------------------------

if len(sys.argv) == 2:
    connect_uid = sys.argv[1]
else:
    connect_uid = None

print u"Discovering Sonos zones".encode('utf-8')

match_ips   = []
for zone in soco.discover():
    print u"   {} (UID: {})".format(zone.player_name, zone.uid).encode('utf-8')

    if connect_uid:
        if zone.uid.lower() == connect_uid.lower():
            match_ips.append(zone.ip_address)
    else:
        # we recognize Sonos Connect and ZP90 by their hardware revision number
        print zone.get_speaker_info().get('hardware_version')
        print
        if zone.get_speaker_info().get('hardware_version')[:4] == '1.17':
            match_ips.append(zone.ip_address)
            print u"   => possible match".encode('utf-8')
print

if len(match_ips) != 1:
    print u"The number of Sonos Connect devices found was not exactly 1.".encode('utf-8')
    print u"Please specify which Sonos Connect device should be used by".encode('utf-8')
    print u"using its UID as the first parameter.".encode('utf-8')
    sys.exit(1)

sonos_device    = soco.SoCo(match_ips[0])
subscription    = None
renewal_time    = 120




# --- Main loop ---------------------------------------------------------------

break_loop      = False
last_status     = None
start_time      = 0
elapsed         = 0
device_on       = False

# catch SIGTERM gracefully
signal.signal(signal.SIGTERM, handle_sigterm)

# non-buffered STDOUT so we can use it for logging
auto_flush_stdout()

while True:
    # if not subscribed to SONOS connect for any reason (first start or disconnect while monitoring), (re-)subscribe
    if not subscription or not subscription.is_subscribed or subscription.time_left <= 5:
        # The time_left should normally not fall below 0.85*renewal_time - or something is wrong (connection lost).
        # Unfortunately, the soco module handles the renewal in a separate thread that just barfs  on renewal
        # failure and doesn't set is_subscribed to False. So we check ourselves.
        # After testing, this is so robust, it survives a reboot of the SONOS. At maximum, it needs 2 minutes
        # (renewal_time) for recovery.

        if subscription:
            print u"{} *** Unsubscribing from SONOS device events".format(datetime.now()).encode('utf-8')
            try:
                subscription.unsubscribe()
                soco.events.event_listener.stop()
            except Exception as e:
                print u"{} *** Unsubscribe failed: {}".format(datetime.now(), e).encode('utf-8')

        print u"{} *** Subscribing to SONOS device events".format(datetime.now()).encode('utf-8')
        try:
            subscription = sonos_device.avTransport.subscribe(requested_timeout=renewal_time, auto_renew=True)
        except Exception as e:
            print u"{} *** Subscribe failed: {}".format(datetime.now(), e).encode('utf-8')
            # subscription failed (e.g. sonos is disconnected for a longer period of time): wait 10 seconds
            # and retry
            time.sleep(10)
            continue

    try:
        event   = subscription.events.get(timeout=10)
        status  = event.variables.get('transport_state')

        if not status:
            print u"{} Invalid SONOS status: {}".format(datetime.now(), event.variables).encode('utf-8')

        if last_status != status:
            print u"{} SONOS play status: {}".format(datetime.now(), status).encode('utf-8')
            if status == 'PLAYING':
                if not device_on:
                    send_on()
                    device_on = True
                start_time = 0
            elif (status == 'PAUSED_PLAYBACK' or status == 'STOPPED') and device_on:
                print u"Starting wait timer.".encode('utf-8')
                start_time = time.time()
                print "start_time =", start_time

        last_status = status
    except Queue.Empty:
        if start_time > 0:
            elapsed = time.time() - start_time
            print "elapsed =", elapsed
            if elapsed > OFF_WAIT_TIME:
                if device_on:
                    send_off()
                    device_on = False
                start_time = 0
    except KeyboardInterrupt:
        handle_sigterm()

    if break_loop:
        subscription.unsubscribe()
        soco.events.event_listener.stop()
        break
