import datetime
import os
import random
import struct
import subprocess
import os
import subprocess
import webbrowser   # <-- ADD THIS
import pyautogui
import datetime
import speech_recognition as sr

import sys
import time as t

import pvporcupine
import pyaudio
import pyautogui
import pyjokes
import pyttsx3
import speech_recognition as sr
import wikipedia
# Optional imports (used if available)
try:
    import pywhatkit
except Exception:
    pywhatkit = None
# ------------------------------------------------------------------------------------
# Compatibility fix for distutils removal in some Python versions
try:
    import distutils.version
except ImportError:
    try:
        from setuptools import distutils  # type: ignore
    except Exception:
        pass
# ------------------------------------------------------------------------------------

# ------------------------------- Voice Engine Setup --------------------------------
engine = pyttsx3.init()
voices = engine.getProperty("voices")
# If index error occurs, fallback to default voice index 0
try:
    engine.setProperty("voice", voices[1].id)
except Exception:
    engine.setProperty("voice", voices[2].id)
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)


def speak(text: str) -> None:
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()


# ------------------------------ Wake Word Detection --------------------------------
def wait_for_wake_word():
    """Wait for the Porcupine wake-word 'jarvis' then return.
    If Porcupine fails to initialize (missing/invalid access key, platform issue),
    this function will announce a fallback and return immediately so the program
    can use manual listening (takecommand()) instead.
    """
    # Read access key from environment (recommended) or fall back to a literal (less secure)
    access_key = os.environ.get("PICOVOICE_ACCESS_KEY", None)
    # If you prefer to hardcode (not recommended), set: access_key = "pk_XXXX..."
    if not access_key:
        # If you don't have an env var, you can still set it here (but don't commit it)
        access_key = "TLEY5yc2O58mniRBWI07GYUUZH3zb0tr5xvLLPRYRiDUcQTQ0vIw+Q=="

    porcupine = None
    pa = None
    stream = None

    try:
        # Initialize Porcupine with access key
        porcupine = pvporcupine.create(access_key=access_key, keywords=["jarvis"])

        # Open microphone stream matching Porcupine's requirements
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        print("🔊 Waiting for wake word: 'Jarvis'...")
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm_unpacked)
            if keyword_index >= 0:
                speak("Yes sir?")
                print("Wake word detected!")
                break

    except Exception as e:
        # Porcupine failed to initialize or runtime error occurred
        print("Porcupine init/processing error:", e)
        speak("Wake-word engine failed. Falling back to manual listening.")
        # Ensure resources are cleaned up (if partially created)
        try:
            if stream is not None:
                stream.stop_stream()
                stream.close()
        except Exception:
            pass
        try:
            if pa is not None:
                pa.terminate()
        except Exception:
            pass
        try:
            if porcupine is not None:
                porcupine.delete()
        except Exception:
            pass
        # Return, so caller will proceed to manual listening (takecommand)
        return

    finally:
        # Normal cleanup after detection loop
        try:
            if stream is not None:
                stream.stop_stream()
                stream.close()
        except Exception:
            pass
        try:
            if pa is not None:
                pa.terminate()
        except Exception:
            pass
        try:
            if porcupine is not None:
                porcupine.delete()
        except Exception:
            pass
# ------------------------------ Basic Helper Functions ------------------------------
def time_now() -> None:
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    speak(f"The current time is {current_time}")
    print("Time:", current_time)


def date_now() -> None:
    now = datetime.datetime.now()
    day_suffix = "th" if 11 <= now.day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(now.day % 10, "th")
    formatted_date = f"{now.day}{day_suffix} of {now.strftime('%B')} {now.year}"
    speak("Today's date is " + formatted_date)
    print("Date:", formatted_date)


def load_name() -> str:
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        name_path = os.path.join(script_dir, "assistant_name.txt")
        with open(name_path, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Jarvis"


def wishme() -> None:
    assistant_name = load_name()
    speak(f"Welcome back, sir! I am {assistant_name}.")
    hour = datetime.datetime.now().hour
    if 4 <= hour < 12:
        greeting = "Good morning!"
    elif 12 <= hour < 16:
        greeting = "Good afternoon!"
    elif 16 <= hour < 24:
        greeting = "Good evening!"
    else:
        greeting = "Good night, see you tomorrow."
    speak(greeting)
    speak("Please tell me how may I assist you.")


# -------------------------------- Screenshot Feature --------------------------------
def screenshot() -> None:
    """Takes a screenshot and saves it to Pictures\Screenshots (creates folder if needed)."""
    try:
        img = pyautogui.screenshot()
        screenshot_folder = os.path.expanduser(r"~\Pictures\Screenshots")
        os.makedirs(screenshot_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        img_path = os.path.join(screenshot_folder, f"Jarvis_Screenshot_{timestamp}.png")
        img.save(img_path)
        speak("Screenshot saved to your Screenshots folder.")
        print(f"Screenshot saved as {img_path}")
    except Exception as e:
        speak("I was unable to take a screenshot.")
        print("Screenshot error:", e)


# --------------------------------- Take Command -------------------------------------
def takecommand() -> str:
    """Listens for a voice command and returns it as lowercase string. Returns '' on timeout/error."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        r.energy_threshold = 4000
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            print("Timeout occurred. No speech detected.")
            return ""
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print("User said:", query)
        return query.lower()
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that.")
        return ""
    except sr.RequestError:
        speak("Speech recognition service is unavailable. Check internet connection.")
        return ""
    except Exception as e:
        print("Recognition error:", e)
        return ""


# --------------------------------- Music Player -------------------------------------
def play_music(song_name: str = "") -> None:
    music_dir = os.path.expanduser(r"~\Music")
    if not os.path.exists(music_dir):
        speak("Your music directory was not found.")
        return
    songs = os.listdir(music_dir)
    if song_name:
        songs = [s for s in songs if song_name.lower() in s.lower() and s.endswith((".mp3", ".wav", ".flac"))]
    if not songs:
        speak("No matching songs found.")
        return
    song = random.choice(songs)
    try:
        os.startfile(os.path.join(music_dir, song))
        speak(f"Playing {song.split('.')[0]}")
    except Exception as e:
        speak("Unable to play this file.")
        print("Music error:", e)


# --------------------------------- Name Setter --------------------------------------
def set_name() -> None:
    speak("What would you like to name me?")
    name = takecommand()
    if name:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        name_path = os.path.join(script_dir, "assistant_name.txt")
        with open(name_path, "w") as file:
            file.write(name)
        speak(f"Alright, I will be called {name} from now on.")
    else:
        speak("I couldn't catch that.")


# ------------------------------- Wikipedia Search -----------------------------------
def search_wikipedia(query: str) -> None:
    try:
        speak(f"Searching Wikipedia for {query}")
        result = wikipedia.summary(query, sentences=3, auto_suggest=False)
        speak(result)
        print(result)
    except wikipedia.exceptions.DisambiguationError:
        speak("There are multiple results. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("No page found for that topic.")
    except Exception as e:
        speak("An error occurred while searching Wikipedia.")
        print("Wikipedia error:", e)


# ----------------------------- System Commands (shutdown/restart) --------------------
def execute_system_command(command, name: str) -> None:
    try:
        speak(f"{name} in one second. Goodbye!")
        subprocess.Popen(command)
    except Exception as e:
        speak(f"Failed to perform {name}.")
        print("System command error:", e)


# ------------------------------- Volume Control Helpers -----------------------------
# Uses Windows virtual key events (works without extra packages)
if sys.platform.startswith("win"):
    import ctypes

    # Virtual key codes
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF

    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002

    def volume_up(steps: int = 1) -> None:
        for _ in range(steps):
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_EXTENDEDKEY, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

    def volume_down(steps: int = 1) -> None:
        for _ in range(steps):
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, KEYEVENTF_EXTENDEDKEY, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

    def volume_mute_toggle() -> None:
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_EXTENDEDKEY, 0)
        ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)

    def set_volume_percentage(target_percent: int) -> None:
        """
        Set system volume to approx target_percent by stepping volume up/down.
        This is a coarse method (using media keys). For precise control, install 'pycaw'.
        """
        # crude strategy: max 50 steps; first mute, then increase from 0
        try:
            # attempt to mute then raise
            volume_mute_toggle()
        except Exception:
            pass
        # raise volume to target (approx) by sending volume_up many times
        steps = max(0, min(50, int(target_percent / 2)))  # rough mapping
        for _ in range(steps):
            volume_up()


else:
    # Non-Windows placeholders
    def volume_up(steps: int = 1) -> None:
        speak("Volume control is only implemented for Windows in this script.")

    def volume_down(steps: int = 1) -> None:
        speak("Volume control is only implemented for Windows in this script.")

    def volume_mute_toggle() -> None:
        speak("Volume control is only implemented for Windows in this script.")

    def set_volume_percentage(percent: int) -> None:
        speak("Volume control is only implemented for Windows in this script.")


# ------------------------------ Brightness Control ---------------------------------
def set_brightness(percent: int) -> bool:
    """
    Attempts to set brightness using PowerShell WMI call.
    Returns True if no exception (likely success), False otherwise.
    """
    percent = max(0, min(100, int(percent)))
    cmd = (
        f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
        f".WmiSetBrightness(1,{percent})"
    )
    try:
        # Run PowerShell command
        completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if completed.returncode == 0:
            speak(f"Brightness set to {percent} percent.")
            return True
        else:
            print("Brightness command stderr:", completed.stderr)
            speak("Could not set brightness using PowerShell.")
            return False
    except Exception as e:
        print("Brightness error:", e)
        speak("Failed to set brightness.")
        return False


def brightness_up(step: int = 10) -> None:
    # Try to read current brightness and increase it - best-effort
    try:
        get_cmd = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
        completed = subprocess.run(["powershell", "-Command", get_cmd], capture_output=True, text=True)
        if completed.returncode == 0 and completed.stdout.strip().isdigit():
            current = int(completed.stdout.strip())
            set_brightness(min(100, current + step))
        else:
            # fallback: just increase by step to 70 as default
            set_brightness(70)
    except Exception as e:
        print("Brightness up error:", e)
        speak("Couldn't change brightness.")


def brightness_down(step: int = 10) -> None:
    try:
        get_cmd = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"
        completed = subprocess.run(["powershell", "-Command", get_cmd], capture_output=True, text=True)
        if completed.returncode == 0 and completed.stdout.strip().isdigit():
            current = int(completed.stdout.strip())
            set_brightness(max(0, current - step))
        else:
            set_brightness(30)
    except Exception as e:
        print("Brightness down error:", e)
        speak("Couldn't change brightness.")


# --------------------------- Desktop Automation: Open / Close -----------------------
# Basic mapping of friendly names -> executable / process names (add more as needed)
APP_MAP = {
    "chrome": (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "chrome.exe"),
    "vscode": (r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe", "Code.exe"),
    "notepad": ("notepad.exe", "notepad.exe"),
    "calculator": ("calc.exe", "Calculator.exe"),
    "spotify": (r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe", "Spotify.exe"),
    "edge": (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "msedge.exe"),
}


def open_app(app_name):
    app_name = app_name.lower()

    # Common apps
    apps = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "google": "https://www.google.com",
        "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "settings": "ms-settings:",
    }

    if app_name in apps:
        try:
            path = apps[app_name]

            # If it's a website, open with webbrowser
            if path.startswith("http"):
                speak("Opening Google")
                webbrowser.open(path)
                return

            speak(f"Opening {app_name}")
            os.startfile(path)
        except Exception as e:
            print("Open app error:", e)
            speak(f"Could not open {app_name}.")
    else:
        speak(f"I don't know how to open {app_name}.")


# ------------------------------ Play YouTube by Voice ------------------------------
def play_youtube(query: str) -> None:
    """Play a YouTube video for the query. Uses pywhatkit if available, else opens search results."""
    query = query.strip()
    if not query:
        speak("What should I play on YouTube?")
        return
    speak(f"Playing {query} on YouTube.")
    if pywhatkit:
        try:
            pywhatkit.playonyt(query)
            return
        except Exception as e:
            print("pywhatkit play error:", e)
    # fallback: open search results
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    wb.open(url)


# ------------------------------- Main Logic ----------------------------------------
if __name__ == "__main__":
    wishme()
    ASSISTANT_NAME = load_name().lower()

    # Main loop using wake-word detection
    while True:
        # Wait for wake word (will fall back to manual listening if porcupine fails)
        wait_for_wake_word()

        # After wake word, listen for the actual command
        query = takecommand()
        if not query:
            continue

        # ---------------------- Sleep / Stop Listening -----------------------
        if (
            "offline" in query
            or "stop listening" in query
            or "jarvis sleep" in query
            or (ASSISTANT_NAME in query and "sleep" in query)
            or "stop now" in query
        ):
            speak("Going to sleep. Say 'Jarvis' to wake me up.")
            # go back to waiting for wake word
            continue

        # ---------------------- Volume Commands ------------------------------
        if "volume up" in query or "increase volume" in query:
            volume_up(steps=2)
            speak("Volume increased.")
            continue
        if "volume down" in query or "decrease volume" in query:
            volume_down(steps=2)
            speak("Volume decreased.")
            continue
        if "mute" in query and "unmute" not in query:
            volume_mute_toggle()
            speak("Toggled mute.")
            continue
        if "unmute" in query:
            volume_mute_toggle()
            speak("Toggled unmute.")
            continue
        # set volume to X percent
        if "set volume to" in query:
            # extract number
            import re

            m = re.search(r"set volume to (\d{1,3})", query)
            if m:
                pct = int(m.group(1))
                set_volume_percentage(pct)
                speak(f"Set volume to approximately {pct} percent.")
            else:
                speak("I could not understand the volume percentage.")
            continue

        # ---------------------- Brightness Commands --------------------------
        if "set brightness to" in query:
            import re

            m = re.search(r"set brightness to (\d{1,3})", query)
            if m:
                pct = int(m.group(1))
                set_brightness(pct)
            else:
                speak("I couldn't understand the brightness percentage.")
            continue
        if "brightness up" in query or "increase brightness" in query:
            brightness_up(step=10)
            continue
        if "brightness down" in query or "decrease brightness" in query:
            brightness_down(step=10)
            continue

        # ---------------------- Play YouTube -------------------------------
        if query.startswith("play youtube") or query.startswith("youtube play") or "play on youtube" in query:
            # extract phrase after keywords
            search = query.replace("play youtube", "").replace("youtube play", "").replace("play on youtube", "").strip()
            play_youtube(search)
            continue
        if query.startswith("play ") and "youtube" in query:
            # e.g., "play never gonna give you up on youtube"
            search = query.replace("on youtube", "").replace("youtube", "").replace("play", "").strip()
            play_youtube(search)
            continue
        if query.startswith("play ") and ("song" in query or "music" in query):
            # fallback to local music
            term = query.replace("play", "").replace("song", "").replace("music", "").strip()
            play_music(term)
            continue

        # ---------------------- Desktop Automation -------------------------
        if query.startswith("open ") or query.startswith("start "):
            # e.g., open chrome / start vscode / open C:\Program Files\App\app.exe
            app = query.replace("open", "").replace("start", "").strip()
            open_app(app)
            continue
        if query.startswith("close ") or query.startswith("kill "):
            app = query.replace("close", "").replace("kill", "").strip()
            close_app(app)
            continue

        # ---------------------- Screenshot -------------------------------
        if "screenshot" in query or "take screenshot" in query or "capture screen" in query:
            # optional "in X seconds"
            import re

            m = re.search(r"in (\d{1,2}) seconds", query)
            if m:
                delay = int(m.group(1))
                speak(f"Taking screenshot in {delay} seconds.")
                t.sleep(delay)
            screenshot()
            continue

        # ---------------------- Basic Commands -----------------------------
        if "time" in query:
            time_now()
            continue
        if "date" in query:
            date_now()
            continue
        if "tell me about" in query or "who is" in query or "what is" in query:
            term = (
                query.replace("tell me about", "")
                .replace("who is", "")
                .replace("what is", "")
                .strip()
            )
            if term:
                search_wikipedia(term)
            else:
                speak("What should I search on Wikipedia?")
            continue

        # ---------------------- Web Search / Open Sites --------------------
        if "search for" in query or query.startswith("google "):
            term = query.replace("search for", "").replace("google", "").strip()
            if term:
                wb.open(f"https://www.google.com/search?q={term.replace(' ', '+')}")
                speak(f"Searching Google for {term}")
            else:
                speak("What do you want me to search for?")
            continue
        if "open youtube" in query and "play" not in query:
            wb.open("https://youtube.com")
            speak("Opening YouTube.")
            continue
        if "open google" in query:
            wb.open("https://google.com")
            speak("Opening Google.")
            continue

        # ---------------------- Music / Jokes / Name ----------------------
        if "play music" in query or "play song" in query:
            term = query.replace("play music", "").replace("play song", "").strip()
            play_music(term)
            continue
        if "set your name" in query or "change your name" in query:
            set_name()
            ASSISTANT_NAME = load_name().lower()
            continue
        if "tell me a joke" in query or "make me laugh" in query or "joke" in query:
            j = pyjokes.get_joke()
            speak(j)
            print("Joke:", j)
            continue

        # ---------------------- System Commands --------------------------
        if "shutdown" in query or "shut down" in query:
            execute_system_command(["shutdown", "/s", "/f", "/t", "1"], "shutdown")
            break
        if "restart" in query:
            execute_system_command(["shutdown", "/r", "/f", "/t", "1"], "restart")
            break

        # ---------------------- Exit / Fallback --------------------------
        if "exit" in query or "quit" in query or "goodbye" in query:
            speak("Going offline. Have a good day!")
            break

        # If command not understood:
        speak("Sorry, I did not understand that command.")
