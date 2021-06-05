#!/usr/bin/env python3

import mido
import pulsectl
import toml
import wx
import glob
import copy
import os
import fileinput

INTERFACES = ['button', 'slider', 'toggle', 'dial']

home = os.path.expanduser("~")
CONFIG_DIR = "{0}/.config/midi_shortcuts/".format(home)
DEFAULTS = CONFIG_DIR + "defaults"

class Selector(wx.Frame):

	def __init__(self, parent, size=(200,100), title="", key=None):
		wx.Frame.__init__(self, parent, title=title, size=size)
		self.key = key
		self.setting = None
		self.default = None

		self.ReadDefaults()

		if self.default:
			self.setting = self.default


	def ReadDefaults(self):
		defaults = open(DEFAULTS, "r")
		for line in defaults:
			tokens = line.strip().split("|")
			if len(tokens) == 2 and tokens[0].strip() == self.key:
				self.default = tokens[1].strip()
				break

	def SetDefaults(self, e):
		self.default = self.setting
		defaults_string = "{0}| {1}".format(self.key, self.setting)

		entry_found = False
		with fileinput.FileInput(files=[DEFAULTS], inplace=True) as f:
			for line in f:
				tokens = line.strip().split("|")
				if len(tokens) > 0 and tokens[0].strip() == self.key:
					print(defaults_string),
					entry_found = True
				else:
					print(line.strip()),

		if not entry_found:	
			defaults = open(DEFAULTS, "a")
			defaults.write(defaults_string + "\n")


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
		self.actions["pulse_volume"] = PulseAudioVolume(pulse, sinks[0])
		self.actions["pulse_mute"] = PulseAudioMute(pulse, sinks[0])


class MidiControl:
	def __init__(self, control=None, name=None, msg_type=None, action=None, interface=None):
		self._control = control
		self._name = name
		self._msg_type = msg_type
		self._interface = interface
	
		self.action = action

	def __str__(self):
		return "{4}, control {0} \"{1}\" ({2}): {3}".format(self._control, self._name, self._msg_type, self.action, self._interface)

	def set_name(self, name):
		self._name = name

	def set_action(self, action):
		self.action = action


class MidiDevice:
	_desktop = None
	_listener = None

	# A blank template of the available physical controls on the device
	_controls = {}

	# A mapping of the physical controls for each channel to desktop action types
	_programs = {}
	_program_names = {}

	def __init__(self, config_file="config.toml", name=None, dev_id=None, desktop=None):
		self._name = name
		self._id = dev_id
		self._desktop = desktop

		self._port = None
		self._listening_on = None

	def _get_action(self, channel, control_id):
		action = self._programs[channel][control_id].action
		return action

	def _send_action_to_desktop(self, action, value):
		self._desktop.actions[action].execute(value)

	def _read_device(self, device_file):
		toml_dict = toml.load(device_file)
		for key in toml_dict:
			category = toml_dict[key]

			if type(category) is list:
				control_cat = category
				for control in control_cat:
					new_control = MidiControl(control=control['control'], msg_type=control['msg_type'], interface=key)
					self._controls[control['control']] = new_control

		self._read_config('control_maps/worlde_nick_dev.toml')


	def _read_config(self, config_file):
		toml_dict = toml.load(config_file)


		programs = toml_dict['program']

		for program in programs:
			name = program['name']
			channel = program['channel']	

			controls = copy.deepcopy(self._controls)

			for category in program:
				if type(program[category]) is list:

					control_cat = program[category]

					for control in control_cat:
						control_id = control['control']
						name = control['name']
						action = control['action']

						controls[control_id].set_action(action)
						controls[control_id].set_name(name)

			self._programs[channel] = controls
			self._program_names[channel] = name


	def get_name(self):
		return self._name

	def set_dev_id(self, dev_id):
		self._id = dev_id
		self._name = self._id.split(":")[0]

	def get_dev_id(self):
		return self._id

	def load_device(self):
		device_files = glob.glob("devices/*.toml")
		for device in device_files:
			toml_dict = toml.load(device)
			print(toml_dict.keys())
			if toml_dict["name"] == self._name:
				self._read_device(device)
				break

	def summarize(self):
		for program in self._program_names:
			name = self._program_names[program]
			print("#### {0} ####".format(name))
			controls = self._programs[program]
			for control_id in controls:
				print(controls[control_id])

	def stop_listen(self):
		self.need_abort = 1

	def listen(self):
		self.need_abort = 0

		while True:
			wx.Yield()

			if self.need_abort == 1:
				print("ABORT")
				break
	
			if not self._port:
				self._port = mido.open_input(self._id)

			# We rename the device if it gets a new input, so if the current
			# name doesn't match the name of the port we're listening on, we
			# need to stop listening on the old port and start on the new one
			elif self._id != self._listening_on.name:
				self._port.close()
				self._port = mido.open_input(self._id)
	

			for message in self._port.iter_pending():
				self._current_program = message.channel
				action = self._get_action(message.channel, message.control)
				self._send_action_to_desktop(action, message.value)
				print(self._current_program, action, message.value, message.control)
	
			self._listening_on = self._port

#			print(self._id, "||", self._listening_on.name, "||", self._port.name)

class PulseSelect(Selector):
	def __init__(self, parent, title="", pulse=None, pulse_type=None):
		Selector.__init__(self, parent, title=title, key="{0}.pulse.{1}".format(title, pulse_type) )

		self.pulse = pulse
		self.pulse_type = pulse_type

		if pulse_type == "sink":
			self.choices = pulse.sink_list()
		elif pulse_type == "source":
			self.choices = pulse.source_list()

		self.pulseselect = wx.ComboBox(parent, choices = self.choices, style = wx.CB_READONLY)

		self.pulseselect.Bind(wx.EVT_COMBOBOX, self.OnCombo, self.pulseselect)

	def OnCombo(self, e):
		self.pulse_name = self.pulseselect.GetValue()
		print("value is:" + self.pulse_name)


class ActionSelect(wx.Frame):
	def __init__(self, parent, title=""):
		wx.Frame.__init__(self, parent, title=title, size=(200,100))

		self.choices = ["volume", "mute"]

		self.actionselect =  wx.ComboBox(parent, choices = self.choices, style = wx.CB_READONLY)
		self.actionselect.Bind(wx.EVT_COMBOBOX, self.OnCombo, self.actionselect)

	def OnCombo(self, e):
		self.action = self.actionselect.GetValue()
		print("value is:" + self.action)

ID_START = wx.NewId()
ID_STOP = wx.NewId()

class MidiSelect(Selector):
	def __init__(self, parent, title="", device=None):
		Selector.__init__(self, parent, title=title, key="midi device")

		self.device = device

		# Set up combobox and two buttons
		inputs = mido.get_input_names()

		self.midiselect = wx.Choice(parent, choices = inputs)

		if self.default in inputs:
			self.midiselect.SetSelection(inputs.index(self.default))
			self.SetDevice(self.default)
			

		self.start = wx.Button(parent, ID_START, 'Start', pos=(0, 50))
		self.stop = wx.Button(parent, ID_STOP, 'Stop', pos=(100, 50))

		self.midiselect.Bind(wx.EVT_CHOICE, self.OnChoice, self.midiselect)
		self.start.Bind(wx.EVT_BUTTON, self.OnStart, self.start)
		self.stop.Bind(wx.EVT_BUTTON, self.OnStop, self.stop)

	def SetDevice(self, dev_id):
		self.device.set_dev_id(dev_id)
		self.setting = self.device.get_dev_id()
		self.device.load_device()


	def OnChoice(self, e):
		midi_description = self.midiselect.GetString(self.midiselect.GetSelection())

		self.SetDevice(midi_description)

		print("description is: " + midi_description)
		print("name is: " + self.device.get_name())

		self.SetDefaults(e=0)
	
	def OnStart(self, e):
		self.device.listen()

	def OnStop(self, e):
		self.device.stop_listen()


class ConfigSelect(Selector):
	def __init__(self, parent, title=""):
		Selector.__init__(self, parent, title=title, key="config")

		self.config_selector = wx.FileDialog(parent, message="Select a configuration file", 
			defaultDir="control_maps/", style=wx.FD_OPEN)	
	
		self.readout = wx.StaticText(parent, pos=(0, 250), label="Active Config: {0}".format(self.setting))
	
		self.config_button = wx.Button(parent, ID_START, 'Config', pos=(0, 150))
		self.save_default = wx.Button(parent, ID_START, 'Save', pos=(100, 150))

		self.config_button.Bind(wx.EVT_BUTTON, self.OnConfig, self.config_button)
		self.save_default.Bind(wx.EVT_BUTTON, self.SetDefaults, self.save_default)

	def OnConfig(self, e):
		self.config_selector.ShowModal()
		
		self.setting = self.config_selector.GetPath()
		self.readout.SetLabel("Active Config: {0}".format(self.setting))

		self.config_selector.Destroy()


class MainApplication(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, title=title, size=(800,600))

		self.settings()

		# The main application serves to connect the midi device to the
		# desktop functions through a variety of dropdown menus
		self._desktop = DesktopControl()
		self._midi_device = MidiDevice(desktop=self._desktop)

		self.midiselect = MidiSelect(self, device=self._midi_device)
		self.configselect = ConfigSelect(parent=self)

		self.CreateStatusBar()
		
		# Set up the menu
		filemenu = wx.Menu()

		# Add standard about & exit menu items
		menuAbout = filemenu.Append(wx.ID_ABOUT, "&About", "Information about this program")
		filemenu.AppendSeparator()
		menuExit = filemenu.Append(wx.ID_EXIT, "&Exit", "Terminate the program")

		# Create the menubar
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu, "&File")
		self.SetMenuBar(menuBar)

		# Set events
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
		self.Bind(wx.EVT_CLOSE, self.StopBackground)

		self.Show(True)

	def OnAbout(self, e):
		# A message dialog box with an OK button
		dlg = wx.MessageDialog(self, "Assign convenience shortcuts to a MIDI device", "About MIDI Shortcuts", wx.OK)
		dlg.ShowModal()
		dlg.Destroy()

	def StopBackground(self, e=0):
		self.midiselect.device.stop_listen()
		self.Destroy()

	def OnExit(self, e):
		self.StopBackground()
		self.Close(True)

	def settings(self):
		os.makedirs(CONFIG_DIR, exist_ok=True)

		if not os.path.exists(DEFAULTS):
			defaults = open(DEFAULTS, "w")
			defaults.write("# User config file for MIDI shortcuts\n")
			defaults.close()

if __name__ == "__main__":
	app = wx.App(False)
	frame = MainApplication(None, "MIDI Shortcuts")
	app.MainLoop()


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
