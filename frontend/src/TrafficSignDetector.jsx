import React from 'react';
import GenericDetector from './components/GenericDetector';

const TrafficSignDetector = ({ onBack }) => {
    return (
        <GenericDetector
            apiEndpoint="/api/detect-traffic-sign"
            title="Traffic Sign Inspector"
            instructions="Point camera at traffic signs to detect damage, graffiti, or poor visibility."
            onBack={onBack}
        />
    );
};

export default TrafficSignDetector;
