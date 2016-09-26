# Hue-Hacks

This project contains various scripts for controlling Hue lights
from a Raspberry Pi.

There are a number of testing scripts in the "experiments" directory,
but the primary project contains code for a Raspberry-Pi based
Hue Light controller.  It consists of 3 buttons and a knob.

We use the Raspberry Pi B+ as the central controller.  The GPIO
has the following pinout:
![Schematic](/images/Pi-Bplus-Pinout.png)

Here is the schematic for the controller:
![Schematic](/images/PiHueHat-Layout.png)

The prototype can be put together on a simple PiHat:
![Blank PiHat](/images/Perma-Proto.jpg)

Here is the front:
![Proto Front](/images/Proto-front.png)

And the Back:
![Proto Back](/images/Proto-back.png)

The 3 buttons are:
* a large square LED which serves as the main button
* a red button which is the "back" button
* a blue button which is the "forward" button

The primary functions of the button are triggered with a "short press"

These are:
* Square button: toggle lights on or off
* Red Button: Switch to the previous scene
* Blue Button: Switch to the next scene

A long press will trigger a secondary functinon.  The secondary functions are:
* Square button: Dump state to log
* Red Button: Delete the current scene
* Blue Button: Save the current scene

Additionally, a knob is used to dim the lights.
An led is used to indicate that the lights are in the "on" state.