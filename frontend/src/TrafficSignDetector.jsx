import React from 'react';
import GenericDetector from './components/GenericDetector';

const TrafficSignDetector = ({ onBack }) => {
    return (
        <GenericDetector
            onBack={onBack}
            title="Live Traffic Sign Detector"
            endpoint="/api/detect-traffic-sign"
            description="Point your camera at traffic signs. Damaged or vandalized signs will be detected."
            color="#F59E0B"
            buttonClassName="bg-amber-600 hover:bg-amber-700"
        />
    );
};

export default TrafficSignDetector;
