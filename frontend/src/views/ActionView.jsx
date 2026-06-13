import React from 'react';
import { useLocation, Link } from 'react-router-dom';

const ActionView = () => {
  const location = useLocation();
  const actionPlan = location.state?.actionPlan;

  if (!actionPlan) return <div className="text-center mt-10">No action plan found. <Link to="/" className="text-blue-600">Go Home</Link></div>;

  return (
    <div className="mt-6 space-y-6">
      <StatusTracker currentStep={actionPlan.status === 'generating' ? 2 : 3} />

      {/* Relevant Government Rule - Show immediately if available */}
      {actionPlan.relevant_government_rule && (
        <div className="bg-amber-50 p-4 rounded-lg border border-amber-200 shadow-sm">
          <h2 className="text-lg font-bold text-amber-800 mb-2 flex items-center gap-2">
            <span>📜</span> Relevant Government Rule
          </h2>
          <div className="bg-white/80 p-3 rounded text-sm mb-2 border border-amber-100 whitespace-pre-wrap text-amber-900 font-medium">
             {actionPlan.relevant_government_rule.replace(/\*\*/g, '')}
          </div>
          <p className="text-xs text-amber-700 italic">
            Use this rule to strengthen your complaint when talking to authorities.
          </p>
        </div>
      )}

      {actionPlan.status === 'generating' ? (
        <div className="text-center p-8 bg-white rounded-lg border border-gray-100 shadow-sm">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-bold text-gray-800">Generating Action Plan...</h2>
            <p className="text-gray-600 mt-2">AI is crafting the perfect message for authorities.</p>
        </div>
      ) : (
        <>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h2 className="text-xl font-bold text-green-800 mb-2">Action Plan Generated!</h2>
            <p className="text-green-700">Here are ready-to-use drafts to send to authorities.</p>
          </div>

      <Link to="/" className="text-blue-600 underline text-center w-full block">Back to Home</Link>
    </div>
  );
};

export default ActionView;
