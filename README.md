sonos-ampmonitor
=============

Sends ON/OFF commands via IR to amplifier based on play status of a Sonos Connect.

What this does:

Start this as a daemon (sample init.d-script included). It connects to your Sonos Connect. Whenever the Sonos Connect starts playing music, radio or whatever, it turns on the amplifier using the configured IR On command.   If you pause or stop the Sonos, it will turn off the amplifier using the configured IR On command.

Before installing it as a daemon, try it out first: Adapt the settings in the script below. Then just run the script. It'll auto-discover your Sonos Connect. If that fails (e.g. because you have more than one Connect in your home or for other reasons), you can use the UID of your Sonos Connect as the first and only parameter of the script. The script will output all UIDs neatly for your comfort.

I am currently running this on a Rev B Raspberry Pi.  (HW IR config to be provided.)

Prerequisites:
- Install LIRC and configure for the IR command for your amplifier.
- Install python soco package.  E.g., sudo pip install soco

Todo:  Provide more detailed construction and installation instructions.
