import os
import tempfile
import uuid
import re
import time

class VoiceHandler:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.audio_dir = os.path.join(self.temp_dir, "interview_audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.speech_recognition_available = self._check_speech_recognition()
    
    def _check_speech_recognition(self):
        """Check if speech recognition is available"""
        try:
            import speech_recognition as sr
            return True
        except ImportError:
            return False
    
    def clean_text_for_speech(self, text):
        """Remove markdown and special characters"""
        text = re.sub(r'#+\s+', '', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
        text = re.sub(r'[\u2600-\u26FF\u2700-\u27BF]', '', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = ' '.join(text.split())
        return text.strip()
    
    def text_to_speech_realtime(self, text):
        """Convert text to speech using Google TTS - returns audio path"""
        try:
            from gtts import gTTS
            
            clean_text = self.clean_text_for_speech(text)
            audio_filename = f"interview_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = os.path.join(self.audio_dir, audio_filename)
            
            tts = gTTS(text=clean_text, lang='en', slow=False)
            tts.save(audio_path)
            
            if os.path.exists(audio_path):
                return audio_path
            return None
                
        except Exception as e:
            print(f"TTS Error: {str(e)}")
            return None
    
    def listen_continuous(self, timeout=180, phrase_time_limit=120):
        """
        Listen continuously until user stops speaking or timeout
        Returns (text, error)
        """
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            recognizer.pause_threshold = 2.0  # 2 seconds of silence to consider end
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen until silence or timeout
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                # Convert to text
                text = recognizer.recognize_google(audio, language='en-US')
                return text, None
                
        except ImportError:
            return None, "Speech recognition not installed"
        except sr.WaitTimeoutError:
            return None, "Timeout - no speech detected"
        except sr.UnknownValueError:
            return None, "Could not understand audio"
        except sr.RequestError as e:
            return None, f"Recognition error: {str(e)}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def cleanup_audio_files(self):
        """Clean up audio files"""
        try:
            if os.path.exists(self.audio_dir):
                for file in os.listdir(self.audio_dir):
                    file_path = os.path.join(self.audio_dir, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
        except Exception as e:
            print(f"Cleanup error: {e}")