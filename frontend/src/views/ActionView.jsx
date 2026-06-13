import React, { useEffect } from 'react';
import StatusTracker from '../components/StatusTracker';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

const ActionView = ({ actionPlan, setActionPlan, setView }) => {
  useEffect(() => {
    // Only poll if we have an action plan that is generating
    if (!actionPlan || actionPlan.status !== 'generating' || !actionPlan.id) {
        return;
    }

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/issues/recent`);
        if (res.ok) {
          const data = await res.json();
          // Find the issue by ID
          const issue = data.find(i => i.id === actionPlan.id);
          if (issue && issue.action_plan && issue.action_plan.whatsapp) {
             // Plan is ready! Merge with existing to keep status/id if needed, but actually we replace it completely
             // Issue.action_plan from DB has the full plan now (including rule and AI content)
             setActionPlan(issue.action_plan);
          }
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [actionPlan, setActionPlan]);

  if (!actionPlan) return null;

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

          <div className="bg-white p-4 rounded shadow border">
            <h3 className="font-bold text-lg mb-2 flex items-center">
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm mr-2">WhatsApp</span>
            </h3>
            <div className="bg-gray-100 p-3 rounded text-sm mb-3 whitespace-pre-wrap">
              {actionPlan.whatsapp}
            </div>
            <a
              href={`https://wa.me/?text=${encodeURIComponent(actionPlan.whatsapp)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center bg-green-500 text-white py-2 rounded hover:bg-green-600 transition"
            >
              Send on WhatsApp
            </a>
          </div>

          {actionPlan.x_post && (
            <div className="bg-white p-4 rounded shadow border">
              <h3 className="font-bold text-lg mb-2 flex items-center">
                <span className="bg-black text-white px-2 py-1 rounded text-sm mr-2">X.com</span>
              </h3>
              <div className="bg-gray-100 p-3 rounded text-sm mb-3 whitespace-pre-wrap">
                {actionPlan.x_post}
              </div>
              <a
                href={`https://x.com/intent/post?text=${encodeURIComponent(actionPlan.x_post)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full text-center bg-slate-900 text-white py-2 rounded hover:bg-slate-800 transition"
              >
                Post on X.com
              </a>
            </div>
          )}

          <div className="bg-white p-4 rounded shadow border">
            <h3 className="font-bold text-lg mb-2">Email Draft</h3>
            <div className="mb-2">
              <span className="font-semibold text-gray-700">Subject:</span> {actionPlan.email_subject}
            </div>
            <div className="bg-gray-100 p-3 rounded text-sm mb-3 whitespace-pre-wrap">
              {actionPlan.email_body}
            </div>
            <a
              href={`mailto:?subject=${encodeURIComponent(actionPlan.email_subject)}&body=${encodeURIComponent(actionPlan.email_body)}`}
               className="block w-full text-center bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition"
            >
              Open in Email App
            </a>
          </div>
        </>
      )}

      <button onClick={() => setView('home')} className="text-blue-600 underline text-center w-full block pb-4">Back to Home</button>
    </div>
  );
};

export default ActionView;
