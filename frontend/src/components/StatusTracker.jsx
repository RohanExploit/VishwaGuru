import React from 'react';
import { CheckCircle, Circle, Clock } from 'lucide-react';

const StatusTracker = ({ currentStep = 3 }) => {
  const steps = [
    { id: 1, label: 'Reported' },
    { id: 2, label: 'AI Analyzed' },
    { id: 3, label: 'Plan Ready' },
    { id: 4, label: 'Sent to Auth' },
  ];

  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between relative">
        {/* Progress Bar Background */}
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-gray-200 -z-10"></div>

        {/* Progress Bar Fill */}
        <div
            className="absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-green-500 -z-10 transition-all duration-500"
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        ></div>

        {steps.map((step) => (
          <div key={step.id} className="flex flex-col items-center bg-white px-2">
            {step.id < currentStep ? (
              <CheckCircle className="text-green-500 w-6 h-6 bg-white" />
            ) : step.id === currentStep ? (
              <div className="relative">
                 <div className="absolute inset-0 bg-green-200 rounded-full animate-ping opacity-75"></div>
                 <CheckCircle className="text-green-600 w-6 h-6 bg-white relative" />
              </div>
            ) : (
              <Circle className="text-gray-300 w-6 h-6 bg-white" />
            )}
            <span className={`text-xs mt-1 font-medium ${step.id <= currentStep ? 'text-gray-800' : 'text-gray-400'}`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StatusTracker;
