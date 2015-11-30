#!/bin/bash

# adjust the variables section below
#
# then: place this in /etc/init.d
# then: chmod +x /etc/init.d/sonos-ampmonitor
# then: update-rc.d sonos-ampmonitor defaults
#
# start daemon with /etc/init.d/sonos-monitor start
# stop it with /etc/init.d/sonos-monitor stop

### BEGIN INIT INFO
# Provides:          sonos-ampmonitor
# Required-Start:    lirc $network
# Required-Stop:     lirc $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start sonos-ampmonitor daemon
# Description:       Enable sonos-ampmonitor service.
### END INIT INFO

DAEMON=/usr/bin/python
ARGS=/usr/local/bin/sonos-ampmonitor.py
LOG=/var/log/sonos-ampmonitor.log
PIDFILE=/var/run/sonos-ampmonitor.pid
USER=pi
GROUP=pi

case "$1" in
  start)
    echo "Starting server"
    /sbin/start-stop-daemon --start --pidfile $PIDFILE \
        --user $USER --group $GROUP \
        -b --make-pidfile \
        --chuid $USER \
        --startas /bin/bash -- -c "exec $DAEMON $ARGS >>$LOG 2>&1"
    ;;
  stop)
    echo "Stopping server"
    /sbin/start-stop-daemon --stop --pidfile $PIDFILE --verbose
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac

exit 0
