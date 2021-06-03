Use a MIDI controller to change various settings in the OS, such as volume mixing and screen brightness.

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
