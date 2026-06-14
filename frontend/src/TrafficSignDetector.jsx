import React from 'react';
import BaseDetector from './components/BaseDetector';
import { detectorsApi } from './api/detectors';

const TrafficSignDetector = ({ onBack }) => {
  return (
    <BaseDetector
      title="Traffic Sign Inspector"
      apiCall={detectorsApi.trafficSign}
      detectionName="traffic sign issue"
      onBack={onBack}
    />
  );
};

export default TrafficSignDetector;
