import React, { useState, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { miscApi } from '../api';

const VoiceInput = ({ onTranscript }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop()); // Stop microphone access

        await processAudio(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setError(null);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setError("Microphone access denied or not supported.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (blob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      // Filename is needed for backend to detect type properly, though we rely on content
      formData.append('file', blob, 'recording.webm');

      const data = await miscApi.transcribeAudio(formData);
      if (data && data.text) {
        onTranscript(data.text);
      }
    } catch (err) {
      console.error("Transcription failed:", err);
      setError("Transcription failed. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (!isSupported) {
      return null; // Or render a disabled state
  }

  if (error) {
    return (
      <div className="flex flex-col items-end">
          <button
            type="button"
            onClick={toggleRecording}
            className="p-2 rounded-full bg-gray-200 text-gray-600 hover:bg-gray-300"
          >
              <Mic size={20} />
          </button>
          <div className="text-red-500 text-xs mt-1">
            {error}
          </div>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleRecording}
      disabled={isProcessing}
      className={`p-2 rounded-full transition-colors flex items-center justify-center ${
        isRecording
          ? 'bg-red-500 text-white animate-pulse shadow-red-200 shadow-lg'
          : isProcessing
          ? 'bg-blue-100 text-blue-600'
          : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
      }`}
      title={isRecording ? 'Stop recording' : 'Start voice report'}
    >
      {isProcessing ? (
        <Loader2 size={20} className="animate-spin" />
      ) : isRecording ? (
        <MicOff size={20} />
      ) : (
        <Mic size={20} />
      )}
    </button>
  );
};

export default VoiceInput;
