import React from 'react';
import ChatWidget from './ChatWidget';
import VoiceInput from './VoiceInput';

const FloatingButtonsManager = ({ setView }) => {
  const handleVoiceCommand = (transcript) => {
    console.log("Voice command:", transcript);
    const lower = transcript.toLowerCase();

    // Simple command mapping
    if (lower.includes('home')) setView('home');
    else if (lower.includes('report') || lower.includes('issue')) setView('report');
    else if (lower.includes('map')) setView('map');
    else if (lower.includes('pothole')) setView('pothole');
    else if (lower.includes('garbage')) setView('garbage');
    else if (lower.includes('vandalism') || lower.includes('graffiti')) setView('vandalism');
    else if (lower.includes('flood') || lower.includes('water')) setView('flood');
  };

  return (
    <>
      {/* Voice Input Button - Positioned above Chat Widget */}
      <div className="fixed bottom-24 right-5 z-50">
        <VoiceInput onTranscript={handleVoiceCommand} />
      </div>

      {/* Chat Widget - Self-positioned at bottom-right */}
      <ChatWidget />
    </>
  );
};

export default FloatingButtonsManager;
