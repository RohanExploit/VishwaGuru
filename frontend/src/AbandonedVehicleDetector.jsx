import React from 'react';
import BaseDetector from './components/BaseDetector';
import { detectorsApi } from './api/detectors';

const AbandonedVehicleDetector = ({ onBack }) => {
  return (
    <BaseDetector
      title="Abandoned Vehicle Scanner"
      apiCall={detectorsApi.abandonedVehicle}
      detectionName="abandoned vehicle"
      onBack={onBack}
    />
  );
};

export default AbandonedVehicleDetector;
