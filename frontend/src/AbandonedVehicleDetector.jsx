import React from 'react';
import GenericDetector from './components/GenericDetector';

const AbandonedVehicleDetector = ({ onBack }) => {
    return (
        <GenericDetector
            apiEndpoint="/api/detect-abandoned-vehicle"
            title="Abandoned Vehicle Finder"
            instructions="Identify abandoned, wrecked, or rusted vehicles on public property."
            onBack={onBack}
        />
    );
};

export default AbandonedVehicleDetector;
