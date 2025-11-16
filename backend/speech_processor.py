"""
Speech Processor for Voice Assistant
Wraps speech recognition functionality for easy integration
"""

import os
import logging
import time
import threading
from typing import Optional, Callable, Dict, Any
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from the SpeechRecognition project
import sys
sys.path.append('../SpeechRecognition')

# Use faster-whisper directly instead of external modules
try:
    from faster_whisper import WhisperModel
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    import tempfile
    import os
    WHISPER_AVAILABLE = True
except ImportError:
    print("Warning: faster-whisper not available. Speech recognition will be limited.")
    WHISPER_AVAILABLE = False

class SpeechProcessor:
    """
    Wrapper for speech recognition functionality.
    """
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "float32",
        language: Optional[str] = None,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 30,
        silence_threshold_ms: int = 1000,
        speech_threshold_ms: int = 300,
        vad_mode: int = 3
    ):
        """
        Initialize the speech processor.
        
        Args:
            model_size: Whisper model size
            device: Device to run on (cpu, cuda)
            compute_type: Compute type for the model
            language: Language code for transcription
            sample_rate: Audio sample rate
            chunk_duration_ms: Audio chunk duration
            silence_threshold_ms: Silence threshold for VAD
            speech_threshold_ms: Minimum speech duration
            vad_mode: VAD aggressiveness
        """
        # Load configuration from environment
        self.model_size = os.getenv('WHISPER_MODEL_SIZE', model_size)
        self.device = os.getenv('DEVICE', device)
        self.compute_type = os.getenv('COMPUTE_TYPE', 'float32')
        self.language = os.getenv('LANGUAGE', language)
        self.sample_rate = int(os.getenv('SAMPLE_RATE', sample_rate))
        self.chunk_duration_ms = int(os.getenv('CHUNK_DURATION_MS', chunk_duration_ms))
        self.silence_threshold_ms = int(os.getenv('SILENCE_THRESHOLD_MS', silence_threshold_ms))
        self.speech_threshold_ms = int(os.getenv('SPEECH_THRESHOLD_MS', speech_threshold_ms))
        self.vad_mode = int(os.getenv('VAD_MODE', vad_mode))
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.whisper_model = None
        self.audio_processor = None
        self.is_recording = False
        
        # Callbacks
        self.on_transcription_callback = None
        self.on_speech_start_callback = None
        self.on_speech_end_callback = None
        
        # Statistics
        self.stats = {
            "total_segments": 0,
            "total_words": 0,
            "total_duration": 0.0,
            "start_time": None,
            "last_transcription_time": None
        }
        
        # Initialize components if available
        if WHISPER_AVAILABLE:
            self._initialize_components()
        else:
            self.logger.warning("Speech recognition components not available")
    
    def _initialize_components(self):
        """Initialize the Whisper model."""
        try:
            # Initialize Whisper model
            self.logger.info("Initializing Whisper model...")
            self.whisper_model = WhisperModel(
                model_size_or_path=self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            
            self.logger.info("Whisper model initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper model: {e}")
            self.whisper_model = None
            
            # Set up callbacks
            self.audio_processor.set_callbacks(
                on_speech_start=self._on_speech_start,
                on_speech_end=self._on_speech_end,
                on_audio_chunk=self._on_audio_chunk
            )
            
            self.logger.info("Speech processor components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech components: {e}")
            raise
    
    def set_callbacks(
        self,
        on_transcription: Optional[Callable[[str, Dict], None]] = None,
        on_speech_start: Optional[Callable[[], None]] = None,
        on_speech_end: Optional[Callable[[], None]] = None
    ):
        """
        Set callback functions for speech events.
        
        Args:
            on_transcription: Called when transcription is complete
            on_speech_start: Called when speech is detected
            on_speech_end: Called when speech ends
        """
        self.on_transcription_callback = on_transcription
        self.on_speech_start_callback = on_speech_start
        self.on_speech_end_callback = on_speech_end
    
    def start_recording(self):
        """Start recording and transcribing audio."""
        self.logger.warning("Real-time recording not implemented in this version")
        return
    
    def stop_recording(self):
        """Stop recording audio."""
        self.is_recording = False
        self.logger.info("Stopped recording")
    
    def _handle_transcription_segment(self, segment, info):
        """Handle a transcription segment."""
        # Update statistics
        self.stats["total_segments"] += 1
        self.stats["total_duration"] += segment.end - segment.start
        self.stats["last_transcription_time"] = time.time()
        
        # Count words
        words = segment.text.strip().split()
        self.stats["total_words"] += len(words)
        
        # Call transcription callback
        if self.on_transcription_callback:
            transcription_data = {
                "text": segment.text,
                "start": segment.start,
                "end": segment.end,
                "language": getattr(info, 'language', None),
                "language_probability": getattr(info, 'language_probability', None)
            }
            self.on_transcription_callback(segment.text, transcription_data)
    
    def _on_speech_start(self):
        """Callback when speech starts."""
        if self.on_speech_start_callback:
            self.on_speech_start_callback()
    
    def _on_speech_end(self):
        """Callback when speech ends."""
        if self.on_speech_end_callback:
            self.on_speech_end_callback()
    
    def _on_audio_chunk(self, audio_chunk: np.ndarray, is_speech: bool):
        """Callback for each audio chunk."""
        # This can be used for real-time audio visualization
        pass
    
    def transcribe_audio_file(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        if not self.whisper_model:
            raise RuntimeError("Whisper model not initialized")
        
        try:
            # Transcribe using faster-whisper
            segments, info = self.whisper_model.transcribe(
                audio_file_path,
                language=self.language,
                beam_size=5
            )
            
            # Combine all segments
            transcription = " ".join([segment.text for segment in segments])
            return transcription.strip()
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio file: {e}")
            return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the speech processor."""
        status = {
            "is_recording": self.is_recording,
            "model_info": f"Whisper {self.model_size} on {self.device}" if self.whisper_model else None,
            "stats": self.stats.copy(),
            "configuration": {
                "model_size": self.model_size,
                "device": self.device,
                "language": self.language,
                "sample_rate": self.sample_rate
            }
        }
        return status
    
    def is_available(self) -> bool:
        """Check if speech recognition is available."""
        return self.whisper_model is not None
