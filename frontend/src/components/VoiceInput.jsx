import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';

const VoiceInput = ({ onTranscript, language = 'en' }) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const [error, setError] = useState(null);
  const [supported] = useState(!!(window.SpeechRecognition || window.webkitSpeechRecognition));

  const getLanguageCode = (lang) => {
    const langMap = {
      'en': 'en-US',
      'hi': 'hi-IN',
      'mr': 'mr-IN'
    };
    return langMap[lang] || 'en-US';
  };

  useEffect(() => {
    if (!supported) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognitionInstance = new SpeechRecognition();
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = false;
    recognitionInstance.lang = getLanguageCode(language);

    recognitionInstance.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognitionInstance.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
    };

    recognitionInstance.onerror = (event) => {
      setError(`Speech recognition error: ${event.error}`);
      setIsListening(false);
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognitionInstance;

    return () => {
      if (recognitionInstance) {
        recognitionInstance.stop();
      }
    };
  }, [language, onTranscript]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  if (!supported) {
    return (
      <div className="text-red-500 text-sm mt-1">
        Speech recognition not supported
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 text-sm mt-1">
        {error}
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      className={`p-2 rounded-full transition-colors ${
        isListening
          ? 'bg-red-500 text-white animate-pulse'
          : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
      }`}
      title={isListening ? 'Stop listening' : 'Start voice input'}
    >
      {isListening ? <MicOff size={20} /> : <Mic size={20} />}
    </button>
  );
};

export default VoiceInput;