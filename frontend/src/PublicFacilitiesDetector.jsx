import React from 'react';
import GenericDetector from './components/GenericDetector';

const PublicFacilitiesDetector = ({ onBack }) => {
    return (
        <GenericDetector
            onBack={onBack}
            title="Public Facilities Monitor"
            endpoint="/api/detect-public-facilities"
            description="Monitor public facilities for cleanliness and maintenance issues."
            color="#0EA5E9"
            buttonClassName="bg-sky-600 hover:bg-sky-700"
        />
    );
};

export default PublicFacilitiesDetector;
