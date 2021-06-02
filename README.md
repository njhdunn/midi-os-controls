Use a MIDI controller to change various settings in the OS, such as volume mixing and screen brightness.

# Initial to-do:

[y]	Test basic procedure for using midi device to change volume
[]	Create layout file format / reader for assigning functions to mini ports
[]	Create GUI that displays current config, and saves changes to file
[]	Screen brightness functionality
[]	Screen warmth functionality
[]	Media scrubber
[]	Document scroller
[]	Document/page zoomer
[]	Media keys mapping

# Config File Format

Programs correspond to layouts of the entire midi device, and are toggled using the 'bank' button on the device, which changes the `channel` midi property of the inputs from 0-3.
There are then nested arrays of tables for sliders, dials, toggles, and buttons. 
The latter two are distinguished by the behavior when pressed - a toggle will change states when pressed and remain changed when released, while a button will change states when pressed and change back when released. 
With the exception of the silver dial, all input types are labeled as `control_change` midi events and have the following properties:

* `channel` - corresponding to the program bank currently activated
* `control` - the index uniquely identifying the specific input dial/button/toggle/slider
* `value` - the position of the specific input, from 0-127 for dials and sliders, and 0 or 127 for buttons and toggles.
* `time` - not currently used in this project
