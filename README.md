Use a MIDI controller to change various settings in the OS, such as volume mixing and screen brightness.

# Environment Setup
```
mamba create -n midi python=3 wxpython toml mido -c conda-forge -c roebel
conda activate midi
pip install pulsectl python-rtmidi

# On Ubuntu 20.04 I also needed to fix a 'missing' alsa library with a symlink:
cd /usr/lib/x86_64-linux-gnu/
sudo ln -s alsa-lib/libasound_module_conf_pulse.so libasound_module_conf_pulse.so
```

# Hardware

I am using a Worlde EasyControl9 midi controller, which seems to be a rebranded pmidip30.
This controller is misconfigured out of the box, and needs some tweaking to address overlapping control ID indices.
I also wanted the buttons on the bottom to be toggles rather than press-and-hold, so [this linked project was great for reconfiguring the device.](https://github.com/nettoyeurny/pmidipd30)

You may not need to deal with this if you have a different midi controller, but you will have to modify the config file to match the new device.
Since the midi standard doesn't support polling a device for the controls and their states, it isn't possible to automatically grab the device layout without vendor-specific midi extensions (sysex).

# Initial to-do:

- [x]	Test basic procedure for using midi device to change volume
- [x]   Switch proof-of-concept UI to wxPython
- [x]	Create layout file format / reader for assigning functions to mini ports
- [ ]	Create GUI that displays current config, allows for changing settings, and saves changes to the config file
- [ ]	Volume/mute actions
- [ ]	Screen brightness action
- [ ]	Screen warmth action
- [ ]	Media scrubber action
- [ ]	Document scroller action
- [ ]	Document/page zoomer action
- [ ]	Media keys mapping action

# Config File Format

Programs correspond to layouts of the entire midi device, and are toggled using the 'bank' button on the device, which changes the `channel` midi property of the inputs from 0-3.
There are then nested arrays of tables for sliders, dials, toggles, and buttons. 
The latter two are distinguished by the behavior when pressed - a toggle will change states when pressed and remain changed when released, while a button will change states when pressed and change back when released. 
With the exception of the silver dial, all input types are labeled as `control_change` midi events and have the following properties:

* `channel` - corresponding to the program bank currently activated
* `control` - the index uniquely identifying the specific input dial/button/toggle/slider
* `value` - the position of the specific input, from 0-127 for dials and sliders, and 0 or 127 for buttons and toggles.
* `time` - not currently used in this project
