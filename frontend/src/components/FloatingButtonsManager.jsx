import React from 'react';
import ChatWidget from './ChatWidget';
import VoiceInput from './VoiceInput';
import { ArrowUp } from 'lucide-react';

const FloatingButtonsManager = ({ setView }) => {

  const scrollToTop = () => {
    console.log('Arrow button clicked!');
    window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
  };

  const handleVoiceCommand = (transcript) => {
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
      {/* Scroll to Top Button - Always visible above Voice Input */}
      <button
        onClick={scrollToTop}
        className="fixed bottom-36 right-5 z-50 p-3 bg-orange-500 hover:bg-orange-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-110"
        aria-label="Scroll to top"
        title="Scroll to top"
      >
        <ArrowUp size={20} />
      </button>

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
