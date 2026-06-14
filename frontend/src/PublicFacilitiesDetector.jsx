import React from 'react';
import GenericDetector from './components/GenericDetector';

const PublicFacilitiesDetector = ({ onBack }) => {
    return (
        <GenericDetector
            apiEndpoint="/api/detect-public-facilities"
            title="Public Facilities Check"
            instructions="Inspect benches, playgrounds, fountains, and other public amenities for damage."
            onBack={onBack}
        />
    );
};

export default PublicFacilitiesDetector;
