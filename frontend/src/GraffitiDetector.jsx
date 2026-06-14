import React from 'react';
import BaseDetector from './components/BaseDetector';
import { detectorsApi } from './api/detectors';

const GraffitiDetector = ({ onBack }) => {
  return (
    <BaseDetector
      title="Graffiti Detector"
      apiCall={detectorsApi.graffiti}
      detectionName="graffiti"
      onBack={onBack}
    />
  );
};

export default GraffitiDetector;
