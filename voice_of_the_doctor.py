import os
import platform
import subprocess
from gtts import gTTS
import elevenlabs
from elevenlabs.client import ElevenLabs

# Get API key from environment variables
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

def text_to_speech_with_gtts(input_text, output_filepath):
    """
    Convert text to speech using Google Text-to-Speech and play it.
    Automatically handles MP3 to WAV conversion for Windows.
    """
    language = "en"
    
    # Generate MP3 file
    audioobj = gTTS(
        text=input_text,
        lang=language,
        slow=False
    )
    audioobj.save(output_filepath)
    
    # Play the audio based on operating system
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(['afplay', output_filepath])
        elif os_name == "Windows":  # Windows
            # Convert MP3 to WAV for Windows Media.SoundPlayer
            try:
                from pydub import AudioSegment
                wav_filepath = output_filepath.replace(".mp3", ".wav")
                AudioSegment.from_mp3(output_filepath).export(wav_filepath, format="wav")
                subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{wav_filepath}").PlaySync();'])
            except ImportError:
                print("Please install pydub: pip install pydub")
                print("And make sure ffmpeg is installed and in your PATH")
        elif os_name == "Linux":  # Linux
            subprocess.run(['mpg123', output_filepath])  # Better for MP3 than aplay
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")
    
    return output_filepath

def text_to_speech_with_elevenlabs(input_text, output_filepath):
    """
    Convert text to speech using ElevenLabs API and play it.
    Automatically handles MP3 to WAV conversion for Windows.
    """
    if not ELEVENLABS_API_KEY:
        print("Warning: ELEVENLABS_API_KEY not found in environment variables")
        # Fall back to gTTS if ElevenLabs API key is not available
        return text_to_speech_with_gtts(input_text, output_filepath)
    
    # Generate MP3 with ElevenLabs
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio = client.generate(
        text=input_text,
        voice="Aria",
        output_format="mp3_22050_32",
        model="eleven_turbo_v2"
    )
    elevenlabs.save(audio, output_filepath)
    
    # Play the audio based on operating system
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(['afplay', output_filepath])
        elif os_name == "Windows":  # Windows
            # Convert MP3 to WAV for Windows Media.SoundPlayer
            try:
                from pydub import AudioSegment
                wav_filepath = output_filepath.replace(".mp3", ".wav")
                AudioSegment.from_mp3(output_filepath).export(wav_filepath, format="wav")
                subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{wav_filepath}").PlaySync();'])
            except ImportError:
                print("Please install pydub: pip install pydub")
                print("And make sure ffmpeg is installed and in your PATH")
        elif os_name == "Linux":  # Linux
            subprocess.run(['mpg123', output_filepath])  # Better for MP3 than aplay
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")
    
    return output_filepath

# Test functionality
if __name__ == "__main__":
    input_text = "Hi this is a test for text to speech functionality!"
    text_to_speech_with_gtts(input_text=input_text, output_filepath="gtts_testing.mp3")
    
    if ELEVENLABS_API_KEY:
        text_to_speech_with_elevenlabs(input_text, output_filepath="elevenlabs_testing.mp3")