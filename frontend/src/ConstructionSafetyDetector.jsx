import React from 'react';
import GenericDetector from './components/GenericDetector';

const ConstructionSafetyDetector = ({ onBack }) => {
    return (
        <GenericDetector
            apiEndpoint="/api/detect-construction-safety"
            title="Construction Site Safety"
            instructions="Scan construction sites for safety violations like unsafe scaffolding or missing PPE."
            onBack={onBack}
        />
    );
};

export default ConstructionSafetyDetector;
