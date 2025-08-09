import json
import mido
import threading
import time
import os
from pynput import mouse, keyboard
import queue
from tkinter import filedialog
import tkinter as tk
import sys
from os import system
system("title " + "GoldenMIDI")

# For window focusing
try:
    import pygetwindow as gw
except ImportError:
    gw = None

class WebfishingNotFoundError(Exception):
    pass

def focus_game():
    if not gw:
        return
    # Look for windows with title starting "WEBFISHING v"
    titles = gw.getAllTitles()
    webfishing_found = False
    
    for title in titles:
        if title and title.startswith("WEBFISHING v"):
            webfishing_found = True
            wins = gw.getWindowsWithTitle(title)
            if wins:
                win = wins[0]
                try:
                    win.restore()
                    win.activate()
                except Exception:
                    pass
                break
    
    if not webfishing_found:
        raise WebfishingNotFoundError("WEBFISHING window not found")

# Default configuration
DEFAULT_CFG = {
    "use_velocity": True,
    "velocity_multiplier": 1.0,
    "velocity_threshold": 0.0,
    "cooldown": 0.0167,
    "transpose": 0,
    "string_base": {"1": 40, "2": 45, "3": 50, "4": 55, "5": 59, "6": 64},
    "max_fret": 15,
    "string_keys": {"1": "q", "2": "w", "3": "e", "4": "r", "5": "t", "6": "y"},
    "string_x": {"1": 340, "2": 375, "3": 410, "4": 445, "5": 480, "6": 515},
    "strum_x_mouse": {"1": 1455, "2": 1505, "3": 1555, "4": 1605, "5": 1655, "6": 1705},
    "strum_y_min_mouse": 271,
    "strum_y_max_mouse": 538,
    "y_base": 100,
    "y_offset": 60
}

# Load or initialize config
if not os.path.exists('config.json'):
    with open('config.json', 'w') as f:
        json.dump(DEFAULT_CFG, f, indent=4)
with open('config.json') as f:
    cfg = json.load(f)

# Input
try:
    import msvcrt
    def get_key(): return msvcrt.getch().decode()
except ImportError:
    import tty, termios
    def get_key():
        fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
        try: tty.setraw(fd); ch = sys.stdin.read(1)
        finally: termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

def clear_console(): os.system('cls' if os.name=='nt' else 'clear')

def save_cfg():
    with open('config.json', 'w') as f:
        json.dump(cfg, f, indent=4)

def reload_config():
    global USE_VELOCITY, VELOCITY_MULTIPLIER, VELOCITY_THRESHOLD, COOLDOWN, TRANSPOSE
    global STRING_BASE, MAX_FRET, STRING_KEYS, STRING_X, STRUM_X_M, STRUM_Y_MIN_M
    global STRUM_Y_MAX_M, Y_BASE, Y_OFFSET, LOWEST, HIGHEST

    USE_VELOCITY = cfg['use_velocity']
    VELOCITY_MULTIPLIER = cfg['velocity_multiplier']
    VELOCITY_THRESHOLD = cfg['velocity_threshold']
    COOLDOWN = cfg['cooldown']
    TRANSPOSE = cfg.get('transpose', 0)
    STRING_BASE = {int(k): v for k, v in cfg['string_base'].items()}
    MAX_FRET = cfg['max_fret']
    STRING_KEYS = {int(k): v for k, v in cfg['string_keys'].items()}
    STRING_X = {int(k): v for k, v in cfg['string_x'].items()}
    STRUM_X_M = {int(k): v for k, v in cfg['strum_x_mouse'].items()}
    STRUM_Y_MIN_M = cfg['strum_y_min_mouse']
    STRUM_Y_MAX_M = cfg['strum_y_max_mouse']
    Y_BASE = cfg['y_base']
    Y_OFFSET = cfg['y_offset']
    LOWEST = min(STRING_BASE.values())
    HIGHEST = max(v + MAX_FRET for v in STRING_BASE.values())

def check_webfishing_open():
    """Check if WEBFISHING is open before starting MIDI operations"""
    try:
        focus_game()
        return True
    except WebfishingNotFoundError:
        print("\033[33mMake sure that Webfishing is open\033[0m")
        print("Press any key to continue...")
        get_key()
        return False

# Quick Settings menu
def settings_menu():
    made_changes = False
    while True:
        clear_console()
        vel_label = "Enabled" if cfg['use_velocity'] else "Disabled"
        transpose_label = f"{cfg.get('transpose', 0):+d} semitones"
        print("Quick Settings:")
        print(f"[1] Use Velocity        -> {vel_label}")
        print(f"[2] Velocity Multiplier -> {cfg['velocity_multiplier']}")
        print(f"[3] Velocity Threshold  -> {cfg['velocity_threshold']}")
        print(f"[4] Cooldown            -> {cfg['cooldown']} (Increase if having issues with notes not playing, recommended value: 1/FPS)")
        print(f"[5] Transpose           -> {transpose_label}")
        print("[6] \033[90mRESET TO DEFAULT\033[0m")
        print("[0] Back")
        choice = get_key(); print(choice)

        if choice == '0':
            if made_changes:
                reload_config()
            return
        elif choice == '1':
            cfg['use_velocity'] = not cfg['use_velocity']
            made_changes = True
        elif choice == '2':
            val = input("Enter new Velocity Multiplier: ")
            try:
                cfg['velocity_multiplier'] = float(val)
                made_changes = True
            except ValueError: pass
        elif choice == '3':
            val = input("Enter new Velocity Threshold: ")
            try:
                cfg['velocity_threshold'] = float(val)
                made_changes = True
            except ValueError: pass
        elif choice == '4':
            val = input("Enter new Cooldown: ")
            try:
                cfg['cooldown'] = float(val)
                made_changes = True
            except ValueError: pass
        elif choice == '5':
            val = input("Enter transpose value (-12 to +12 recommended): ")
            try:
                transpose_val = int(val)
                cfg['transpose'] = transpose_val
                made_changes = True
            except ValueError: pass
        elif choice == '6':
            confirm = input("Reset all settings to default? (y/n): ")
            if confirm.lower() == 'y':
                cfg.clear()
                cfg.update(DEFAULT_CFG)
                made_changes = True

        if made_changes:
            save_cfg()
        time.sleep(0.2)

reload_config()

# Controllers
mouse_ctrl = mouse.Controller()
keyboard_ctrl = keyboard.Controller()

# MIDI processing
mapping = {}
lock = threading.Lock()
action_queue = queue.Queue()

def find_positions(n): return [(s, n-base) for s, base in STRING_BASE.items() if 0<=n-base<=MAX_FRET]

def click_fret(s, fret):
    try:
        focus_game()
    except WebfishingNotFoundError:
        return  # Silently fail during playback to avoid spam
    x = STRING_X[s]; y = Y_BASE + fret*Y_OFFSET
    mouse_ctrl.position = (x, y)
    mouse_ctrl.click(mouse.Button.left, 1)

def strum_mouse(s, velocity):
    try:
        focus_game()
    except WebfishingNotFoundError:
        return  # Silently fail during playback to avoid spam
    y = STRUM_Y_MIN_M - (velocity/127)*(STRUM_Y_MIN_M-STRUM_Y_MAX_M)*VELOCITY_MULTIPLIER
    x = STRUM_X_M[s]; clampY = max(min(y,STRUM_Y_MAX_M),STRUM_Y_MIN_M)
    mouse_ctrl.position = (x, clampY)
    mouse_ctrl.press(mouse.Button.left)
    time.sleep(COOLDOWN)
    mouse_ctrl.release(mouse.Button.left)

def consumer():
    while True:
        s, f, v = action_queue.get() # String, Fret, Velocity
        click_fret(s, f)

        if USE_VELOCITY:
            strum_mouse(s, v)
        else:
            key = STRING_KEYS[s]
            keyboard_ctrl.press(key)
            time.sleep(COOLDOWN)
            keyboard_ctrl.release(key)

        click_fret(s, f)
        action_queue.task_done()


def handle(msg):
    if msg.type=='note_on' and msg.velocity > VELOCITY_THRESHOLD:
        time.sleep(COOLDOWN)
        vel = msg.velocity if USE_VELOCITY else 127
        orig, n = msg.note, msg.note + TRANSPOSE  # Apply transpose here
        while n<LOWEST: n+=12
        while n>HIGHEST: n-=12
        pos = find_positions(n)
        if not pos: return
        with lock:
            occ = {s for s,_ in mapping.values()}
            chosen = next(((s,f) for s,f in pos if s not in occ), None)
            if not chosen:
                for old,(os,_) in mapping.items():
                    for s,f in pos:
                        if s==os:
                            mapping.pop(old)
                            chosen=(s,f)
                            break
                    if chosen: break
            if not chosen: return
            mapping[orig]=chosen
        action_queue.put((chosen[0],chosen[1],vel))
    elif msg.type=='note_off' or (msg.type=='note_on' and msg.velocity==0):
        with lock: mapping.pop(msg.note,None)

def listener(port_name=None):
    # Check if WEBFISHING is open before starting
    if not check_webfishing_open():
        return False
        
    clear_console()
    available = []
    for name in mido.get_input_names():
        try:
            with mido.open_input(name):
                available.append(name)
        except Exception:
            continue
    if not available:
        print("\033[33mNo MIDI ports available.\033[0m")
        print("[0] Back")
        get_key()
        return False
    if len(available)==1:
        port_name=available[0]
    else:
        for i,name in enumerate(available): print(f"[{i+1}] {name}")
        print("Select [0 to go back]:", end='', flush=True)
        idx_str=get_key(); print(idx_str)
        try:
            idx = int(idx_str)
            if idx == 0: return False
            port_name=available[idx-1]
        except (ValueError, IndexError):
            return False
    try:
        port=mido.open_input(port_name)
    except Exception as e:
        print("Failed to open port: ", e)
        print("[0] Back")
        get_key()
        return False
    clear_console()
    transpose_display = f"Transpose: {TRANSPOSE:+d}" if TRANSPOSE != 0 else ""
    print(f"Listening on {port_name} {transpose_display}")
    print("[0] Back")
    abort=threading.Event()
    def watch_back():
        while not abort.is_set():
            if get_key() == '0':
                abort.set()
    threading.Thread(target=watch_back, daemon=True).start()
    try:
        while not abort.is_set():
            for msg in port.iter_pending():
                handle(msg)
            time.sleep(max(COOLDOWN, 0.001))
    finally:
        port.close()
    return True

def play_midi_file(fp):
    # Check if WEBFISHING is open before starting
    if not check_webfishing_open():
        return
        
    clear_console()
    mid=mido.MidiFile(fp)
    transpose_display = f" | Transpose: {TRANSPOSE:+d}" if TRANSPOSE != 0 else ""
    print(f"Now playing: {os.path.basename(fp)}")
    print(f"Velocity: {'On' if USE_VELOCITY else 'Off'}{transpose_display}")
    print("Press any key to stop...")
    abort=threading.Event()
    def on_press(key):
        try:
            c = key.char.lower()
            if c in STRING_KEYS.values():
                return True
        except AttributeError:
            pass

        # anything else will stop playback
        abort.set()
        return False
    listener_k = keyboard.Listener(on_press=on_press)
    listener_k.start()
    for msg in mid:
        if abort.is_set(): break
        time.sleep(msg.time)
        if not msg.is_meta: handle(msg)
    listener_k.stop()

def main():
    threading.Thread(target=consumer, daemon=True).start()
    while True:
        clear_console()
        ascii_title = """
   \033[38;5;220m____       _     _            \033[0m__  __ ___ ____ ___ 
  \033[38;5;220m/ ___| ___ | | __| | ___ _ __ \033[0m|  \/  |_ _|  _ \_ _|
 \033[38;5;220m| |  _ / _ \| |/ _` |/ _ \ '_ |\033[0m| |\/| || || | | | | 
 \033[38;5;220m| |_| | (_) | | (_| |  __/ | | |\033[0m |  | || || |_| | | 
  \033[38;5;220m\____|\___/|_|\__,_|\___|_| |_|\033[0m_|  |_|___|____/___|
  
"""
        print(ascii_title)
        print("[1] MIDI Input  [2] MIDI File  [3] Quick Settings")
        print("Select: ", end='', flush=True)
        m=get_key(); print(m)
        if m=='1': listener()
        elif m=='2':
            root=tk.Tk(); root.withdraw()
            folder=os.path.join(os.getcwd(),'.midi')
            initial=folder if os.path.exists(folder) else os.getcwd()
            fp=filedialog.askopenfilename(title="Select MIDI file", initialdir=initial, filetypes=[("MIDI files","*.mid *.midi")])
            root.destroy()
            if fp: play_midi_file(fp)
        elif m=='3': settings_menu()

if __name__=='__main__': main()