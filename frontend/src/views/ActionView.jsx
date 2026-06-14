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
             // Plan is ready!
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

  if (actionPlan.status === 'generating') {
      return (
        <div className="mt-6 space-y-6 text-center">
            <StatusTracker currentStep={2} />
            <div className="p-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h2 className="text-xl font-bold text-gray-800 dark:text-white">Generating Action Plan...</h2>
                <p className="text-gray-600 dark:text-gray-400">AI is crafting the perfect message for authorities.</p>
            </div>
        </div>
      );
  }

  return (
    <div className="mt-6 space-y-6">
      <StatusTracker currentStep={3} />

      <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border border-green-200 dark:border-green-800/30">
        <h2 className="text-xl font-bold text-green-800 dark:text-green-400 mb-2">Action Plan Generated!</h2>
        <p className="text-green-700 dark:text-green-300">Here are ready-to-use drafts to send to authorities.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:shadow-md border border-gray-200 dark:border-gray-700">
        <h3 className="font-bold text-lg mb-2 flex items-center text-gray-900 dark:text-white">
          <span className="bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 px-2 py-1 rounded text-sm mr-2">WhatsApp</span>
        </h3>
        <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded text-sm mb-3 whitespace-pre-wrap text-gray-800 dark:text-gray-300">
          {actionPlan.whatsapp}
        </div>
        <a
          href={`https://wa.me/?text=${encodeURIComponent(actionPlan.whatsapp)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full text-center bg-green-500 dark:bg-green-600 text-white py-2 rounded hover:bg-green-600 dark:hover:bg-green-700 transition"
        >
          Send on WhatsApp
        </a>
      </div>

      {actionPlan.x_post && (
        <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:shadow-md border border-gray-200 dark:border-gray-700">
          <h3 className="font-bold text-lg mb-2 flex items-center text-gray-900 dark:text-white">
            <span className="bg-black dark:bg-gray-900 text-white dark:text-white px-2 py-1 rounded text-sm mr-2">X.com</span>
          </h3>
          <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded text-sm mb-3 whitespace-pre-wrap text-gray-800 dark:text-gray-300">
            {actionPlan.x_post}
          </div>
          <a
            href={`https://x.com/intent/post?text=${encodeURIComponent(actionPlan.x_post)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="block w-full text-center bg-slate-900 dark:bg-slate-800 text-white py-2 rounded hover:bg-slate-800 dark:hover:bg-slate-700 transition"
          >
            Post on X.com
          </a>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 p-4 rounded shadow dark:shadow-md border border-gray-200 dark:border-gray-700">
        <h3 className="font-bold text-lg mb-2 text-gray-900 dark:text-white">Email Draft</h3>
        <div className="mb-2 text-gray-900 dark:text-white">
          <span className="font-semibold text-gray-700 dark:text-gray-300">Subject:</span> {actionPlan.email_subject}
        </div>
        <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded text-sm mb-3 whitespace-pre-wrap text-gray-800 dark:text-gray-300">
          {actionPlan.email_body}
        </div>
        <a
          href={`mailto:?subject=${encodeURIComponent(actionPlan.email_subject)}&body=${encodeURIComponent(actionPlan.email_body)}`}
          className="block w-full text-center bg-blue-500 dark:bg-blue-600 text-white py-2 rounded hover:bg-blue-600 dark:hover:bg-blue-700 transition"
        >
          Open in Email App
        </a>
      </div>

      <button onClick={() => setView('home')} className="text-blue-600 dark:text-blue-400 underline text-center w-full block hover:text-blue-700 dark:hover:text-blue-300 transition">Back to Home</button>
    </div>
  );
};

export default ActionView;
