import React from 'react';
import GenericDetector from './components/GenericDetector';

const AbandonedVehicleDetector = ({ onBack }) => {
    return (
        <GenericDetector
            onBack={onBack}
            title="Live Abandoned Vehicle Detector"
            endpoint="/api/detect-abandoned-vehicle"
            description="Point your camera at vehicles. Abandoned or wrecked cars will be detected."
            color="#64748B"
            buttonClassName="bg-slate-700 hover:bg-slate-800"
        />
    );
};

export default AbandonedVehicleDetector;
