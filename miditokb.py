import rtmidi
from time import sleep
from math import floor
import fluidsynth
from Xlib import display, X, XK, error
from Xlib.ext.xtest import fake_input

#coords base 273 44 94 

global mapping, mouse_hold_mapping, mouse_click_mapping, pitch_lower_cap, pitch_upper_cap, release_held_keys, min_volume, piano_velocity_range, piano, pitch, yaw, notes, pitch_bend_value, volume_slider_value, midiin, idle_yaw, yaw_scale, pitch_scale, pitch_imprecision, max_pitch, Xlib_display, neutral_pitch, input_type_map

#hardware-related options
resolution = (2560, 1440)
max_pitch = 127
neutral_pitch = 63
idle_yaw = 64

# custom options
yaw_sensitivity = 200 #THE HIGHER THE NUMBER THE LESS SENSITIVE IT IS
pitch_imprecision = 1 #from 1 to 127, 127 is horribly imprecise, 1 is kinda precise. helps add a deadzone without making every close area impossible to reach. may cause issues with scale especially with a fractional value
pitch_lower_cap = 0 #from 0 to resolution[1]
pitch_upper_cap = resolution[1] #from 0 to resolution[1]
release_held_keys = False #false might help if this program uses a lot of memory because all held keys are logged and never deleted. might also lag on cleanup with true.
soundfont_path = "/home/user/Projects/piano_minecraft/Yamaha_C3_Grand_Piano.sf2"
min_volume = 20
piano_velocity_limits = (63, 127)
continue_delay = 1/1000
regular_delay = 1/900

mapping = {
    49: "w",
    48: "a",
    50: "s",
    52: "d",
    47: "space",
    45: "Shift_L",
    57: "t",
    58: "2",
    43: "Caps_Lock",
    59: "F3",
    46: "Control_L",
}
mouse_hold_mapping = {
    51: 1,
    54: 3
}

mouse_click_mapping = {
    53: 4,
    55: 5,
    103: 4,
    104: 5,
    106: 1,
    107: 3
}
input_type_map = {
    "keydown": X.KeyPress,
    "keyup": X.KeyRelease,
    "mousedown": X.ButtonPress,
    "mouseup": X.ButtonRelease
}
#code
Xlib_display = display.Display()
def config_exceptions(resolution: tuple, piano_velocity_limits: tuple):
    global pitch_lower_cap, pitch_upper_cap, pitch_imprecision
    if pitch_lower_cap>=pitch_upper_cap:
        raise ValueError("pitch_lower_cap must be less than pitch_upper_cap")
    elif pitch_lower_cap<0 or pitch_upper_cap<0:
        print("warn: pitch caps should not be less than 0 (unless using a multimonitor setup)")
    elif pitch_lower_cap>resolution[1] or pitch_upper_cap>resolution[1]:
        print("warn: pitch caps should not be above the resolution. if using a multimonitor setup, set resolution appropriately")
    if pitch_imprecision < 1 and pitch_imprecision > 0:
        print("warn: pitch_imprecision below 1 not recommended")
    elif pitch_imprecision <= 0 :
        raise ValueError("pitch_imprecision cannot be 0 or negative")
    elif pitch_imprecision > 127:
        print("warn: pitch_imprecision above 127 not recommended")
    if piano_velocity_limits[0] > piano_velocity_limits[1]:
        raise ValueError("piano velocity upper limit must be higher or equal than lower limit")
    elif piano_velocity_limits[0] < 0:
        raise ValueError("velocity limits cannot be below 0")
    elif piano_velocity_limits[1] > 127:
        raise ValueError("velocity limits cannot be above 127")
config_exceptions(resolution, piano_velocity_limits)
def start_midi(): 
    global midiin, piano
    midiin = rtmidi.MidiIn()
    midiports = midiin.get_ports()
    for i in range(len(midiports)):
        print(i, midiports[i])
    midiin.open_port(1)
    piano = fluidsynth.Synth()
    piano.start()
    soundfont_id = piano.sfload(soundfont_path)
    piano.program_select(0, soundfont_id, 0, 0)
start_midi()
def initial_definitions(yaw_sensitivity: float, resolution:tuple):
    global notes, pitch, yaw, volume_slider_value, neutral_pitch, yaw_scale, pitch_scale, pitch_imprecision, bend_multiplier, pitch_bend_value, iteration_of_191, held_keys, mapping, keycode_mapping, held_buttons
    notes = ""
    pitch = neutral_pitch
    yaw = 0
    volume_slider_value = 64
    capped_resolution=(resolution[0], pitch_upper_cap-pitch_lower_cap)
    pitch_scale = (capped_resolution[1] / 127)*pitch_imprecision
    yaw_scale = capped_resolution[0] / 127
    yaw_scale = yaw_scale / yaw_sensitivity
    bend_multiplier = 8192 / 64
    pitch_bend_value = 8192
    iteration_of_191 = 1
    held_keys = []
    held_buttons = []
    keycode_mapping = {}
    for i in mapping.keys():
        keycode = Xlib_display.keysym_to_keycode(XK.string_to_keysym(mapping[i]))
        keycode_mapping[i] = keycode
    fake_input(Xlib_display, X.MotionNotify, False, 0, 0, int(resolution[0]/2), int(resolution[1]/2))
initial_definitions(yaw_sensitivity, resolution)
def set_piano_velocity_range(piano_velocity_limits: tuple):
    global piano_velocity_range
    piano_velocity_range = []
    piano_velocity_limits_delta = piano_velocity_limits[1] - piano_velocity_limits[0]
    piano_velocity_limits_delta_per_possible_value = piano_velocity_limits_delta/128
    for i in range(128):
        value = piano_velocity_limits[0] + piano_velocity_limits_delta_per_possible_value*i
        true_value = floor(value)
        piano_velocity_range += [true_value]
    print(piano_velocity_range)
set_piano_velocity_range(piano_velocity_limits)


def move_yaw(x: int):
    if yaw != 0:
        fake_input(Xlib_display, X.MotionNotify, True, 0, 0, x, 0)
def move_pitch(y: int):
    global pitch_lower_cap
    fake_input(Xlib_display, X.MotionNotify, True, 0, 0, 0, floor(y+pitch_lower_cap))  
def handle_pitch(velocity: int):
    global pitch, pitch_scale, pitch_imprecision, max_pitch
    old_pitch = pitch
    pitch = max_pitch-velocity # invert again because the regular thing is inverted by default
    pitch *= pitch_scale
    pitch = pitch/pitch_imprecision
    move_pitch(pitch-old_pitch)
def play_note(note: int, velocity: int):
    global piano, piano_velocity_range, min_volume, volume_slider_value
    volume_index = velocity*volume_slider_value//127
    volume = piano_velocity_range[volume_index]
    piano.noteon(0, note, max(volume, min_volume)) 
def simulate_press(type: int, key: int):
    fake_input(Xlib_display, type, key, 0, 0)  
    if release_held_keys:
        global held_buttons, held_keys
        if type == X.KeyPress:
            held_keys.append(key)
        elif type == X.ButtonPress:
            held_buttons.append(key)
    print(key)
def start_holding_note(note: int):
    global keycode_mapping, mouse_hold_mapping, mouse_click_mapping, notes, release_held_keys
    notes += str(note)
    notes += " "
    if note in mapping:
        simulate_press(X.KeyPress, keycode_mapping[note])
    elif note in mouse_hold_mapping:
        simulate_press(X.ButtonPress, mouse_hold_mapping[note])
    elif note in mouse_click_mapping:
        simulate_press(X.ButtonPress, mouse_click_mapping[note])
        simulate_press(X.ButtonRelease, mouse_click_mapping[note])
def stop_holding_note(note: int):
    global keycode_mapping, mouse_hold_mapping
    if note in mapping:
        simulate_press(X.KeyRelease, keycode_mapping[note])
    elif note in mouse_hold_mapping:
        simulate_press(X.ButtonRelease, mouse_hold_mapping[note])
def main():
    global pitch, yaw, idle_yaw, yaw_scale, pitch_bend_value, volume_slider_value, midiin, piano, continue_delay, regular_delay
    msg = midiin.get_message()
    if msg is None:
        move_yaw(yaw)
        try:
            Xlib_display.flush()
        except error.XError as e:
            print(type(e))
            print(e)
        sleep(continue_delay)
        return 0
    msg = msg[0] #remove delta time, the msg is [[status, note, velocity], delta_time]
    print(msg)
    status = msg[0]
    note = msg[1]
    velocity = msg[2]
    if status == 144 and velocity > 0:
        start_holding_note(note)
        play_note(note, velocity)
    elif status == 128 or (status == 144 and velocity == 0):
        piano.noteoff(0, note)
        stop_holding_note(note)
    elif status == 176 and note == 7:
        volume_slider_value = velocity
        handle_pitch(velocity)
    elif status == 224 and note == 0:
        pitch_bend_value = floor(velocity * bend_multiplier)
        yaw = velocity - idle_yaw
        yaw = yaw*yaw_scale
        yaw = floor(yaw)
    elif status == 191:
        start_holding_note(note)
        play_note(note, 127)
        piano.noteoff(0, note)
    else: 
        print(msg)
    move_yaw(yaw)
    piano.pitch_bend(0, pitch_bend_value)
    try:
        Xlib_display.flush()
    except error.XError as e:
        print(type(e))
        print(e)
    sleep(regular_delay)
while True:
    try:
        main()    
    except KeyboardInterrupt:
        print("")
        print(notes)
        if release_held_keys:
            for i in held_keys:
                keyboard.release(i)
        Xlib_display.flush()
        exit(0)
