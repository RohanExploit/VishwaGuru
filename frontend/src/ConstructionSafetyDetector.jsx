import React from 'react';
import GenericDetector from './components/GenericDetector';

const ConstructionSafetyDetector = ({ onBack }) => {
    return (
        <GenericDetector
            onBack={onBack}
            title="Construction Safety Scanner"
            endpoint="/api/detect-construction-safety"
            description="Detect safety violations at construction sites (e.g., missing helmets)."
            color="#EF4444"
            buttonClassName="bg-red-600 hover:bg-red-700"
        />
    );
};

export default ConstructionSafetyDetector;
