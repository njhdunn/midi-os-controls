#!/usr/bin/env python3

import mido
import pulsectl
import toml
import tkinter as tk

INTERFACES = ['button', 'slider', 'toggle', 'dial']


class DesktopAction:
	action = None
	def execute(self):
		return None

class NullAction(DesktopAction):
	action = ""

	def execute(self, *arguments):
		return None

class PulseAudioVolume(DesktopAction):
	action = "pulse_volume"

	def __init__(self, pulse, sink):
		self.sink = sink
		self.pulse = pulse

#	def _get_volume(self):
#		sink = self.pulse.get_sink_by_name(self.sink.name)
#		return sink.volume.value_flat

	def execute(self, midi_value):
		volume = midi_value / 127
		self.pulse.volume_set_all_chans(self.sink, volume)
		self.sink_list = self.pulse.sink_list()

class PulseAudioMute(DesktopAction):
	action = "pulse_mute"

	def __init__(self, pulse, sink):
		self.sink = sink
		self.pulse = pulse

	def execute(self, midi_value):
		if midi_value == 127:
			self.pulse.mute(self.sink, mute=True)
		elif midi_value == 0:
			self.pulse.mute(self.sink, mute=False)

class DesktopControl:

	actions = {}

	def __init__(self):

		pulse = pulsectl.Pulse('localhost')
		sinks = pulse.sink_list()
		sources = pulse.source_list()

		self.actions[""] = NullAction()
		self.actions["pulse_volume"] = PulseAudioVolume(pulse, sinks[2])
		self.actions["pulse_mute"] = PulseAudioMute(pulse, sinks[2])


class MidiControl:
	def __init__(self, channel=None, name=None, msg_type=None, action=None, interface=None):
			self._channel = channel
			self._name = name
			self._msg_type = msg_type
			self._interface = interface
	
			self.action = action

	def __str__(self):
			return "{4}, channel {0} \"{1}\" ({2}): {3}".format(self._channel, self._name, self._msg_type, self.action, self._interface)


class MidiDevice:
	_controls = []
	_program_names = []
	_desktop = None
	_current_program = 0

	_listener = None

	def __init__(self, tk_parent, config_file="config.toml", name=None):
		self._name = name
		self._read_config(config_file)
		self._desktop = DesktopControl()
		self._tk_parent = tk_parent

		self._port = None
		self._listening_on = None

	def _get_action(self, control_id):
		ii = int(control_id)
		action = self._controls[self._current_program][ii].action
		return action

	def _send_action_to_desktop(self, action, value):
		self._desktop.actions[action].execute(value)

	def _read_config(self, config_file):
		toml_dict = toml.load(config_file)
		for key in toml_dict:

			for program in toml_dict[key]:
				self._program_names.append(program['name'])
				self._controls.append({})
				prog_index = self._program_names.index(program['name'])

				for entry in program:
					if type(program[entry]) is list:
						control_cat = program[entry]
						for control in control_cat:
							new_control = MidiControl(control['control'], control['name'], 
									control['msg_type'], control['action'], entry)
							self._controls[prog_index][control['control']] = new_control

	def set_name(self, name):
		self._name = name

	def summarize(self):
		for program_name in self._program_names:
			ii = self._program_names.index(program_name)
			program = self._controls[ii]
			print("Program[{0}]: {1}".format(ii, program_name))
			for control in program:
				print(program[control])

	def stop_listening(self):
		self._tk_parent.after_cancel(self._listener)

	def listen(self):

		if not self._port:
			self._port = mido.open_input(self._name)
		
		# We rename the device if it gets a new input, so if the current
		# name doesn't match the name of the port we're listening on, we
		# need to stop listening on the old port and start on the new one
		elif self._name != self._listening_on.name:
			self.stop_listening()
			self._port = mido.open_input(self._name)

		for message in self._port.iter_pending():
			action = self._get_action(message.control)
			self._send_action_to_desktop(action, message.value)

		self._listener = self._tk_parent.after(5, self.listen)
		self._listening_on = self._port

class MidiSelect(tk.Frame):
	def __init__(self, parent, *args, **kwargs):
		tk.Frame.__init__(self, parent, *args, **kwargs)

		inputs = mido.get_input_names()
		
		self.midi_input = tk.StringVar(self)
		self.midi_input.set(inputs[0])

		self.w = tk.OptionMenu(self, self.midi_input, *inputs)
		self.w.pack()

		self.ok = tk.Button(self, text="Start", command=self.ok)
		self.ok.pack()

		self.stop = tk.Button(self, text="Stop", command=self.stop)
		self.stop.pack()

		self.device = MidiDevice(tk_parent=self)
		self.device.summarize()


	def ok(self):
		midi_name = self.midi_input.get()

		print("value is:" + midi_name)

		self.device.set_name(midi_name)
		self.device.listen()

	def stop(self):
		self.device.stop_listening()

class MainApplication(tk.Frame):
	def __init__(self, parent, *args, **kwargs):
		tk.Frame.__init__(self, parent, *args, **kwargs)

		self.midiselect = MidiSelect(self)

		self.close = tk.Button(self, text="Close", command=parent.destroy)

		self.midiselect.pack()
		self.close.pack()


if __name__ == "__main__":
    root = tk.Tk()
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()


#worlde_board = MidiDevice(name=inputs[1])
#worlde_board = MidiDevice(name=midi_name)
#worlde_board.summarize()
#worlde_board.listen()


#for sink in sinks:
#	print("")
#	print(sink)

#for source in sources:
#	print("")
#	print(source)

#with mido.open_input(inputs[1]) as port:
#	for message in port:
#		#print(message.value)
#		print(message)
#		if (message.type == "control_change"):
#			volume = message.value / 127
#		
##			pulse.volume_set_all_chans(sinks[2], volume)
#			print(sinks[2])
