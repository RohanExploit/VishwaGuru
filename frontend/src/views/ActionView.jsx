import React from 'react';
import { useLocation, Link } from 'react-router-dom';

const ActionView = () => {
  const location = useLocation();
  const actionPlan = location.state?.actionPlan;

  if (!actionPlan) return <div className="text-center mt-10">No action plan found. <Link to="/" className="text-blue-600">Go Home</Link></div>;

  return (
    <div className="mt-6 space-y-6">
      <StatusTracker currentStep={3} />

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

      <Link to="/" className="text-blue-600 underline text-center w-full block">Back to Home</Link>
    </div>
  );
};

export default ActionView;
