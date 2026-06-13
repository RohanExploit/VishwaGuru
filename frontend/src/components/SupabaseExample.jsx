/**
 * 📝 Example Supabase Component
 * 
 * This component demonstrates how to use Supabase for:
 * - Authentication
 * - Database operations (CRUD)
 * - Real-time subscriptions
 * 
 * You can use this as a reference when implementing Supabase features
 */

import React, { useState, useEffect } from 'react';
import {
    useAuth,
    useSupabaseQuery,
    useSupabaseInsert,
    useSupabaseUpdate,
    useSupabaseDelete,
    useSupabaseSubscription
} from '../lib/supabaseHooks';
import { signIn, signUp, signOut } from '../lib/supabase';

function SupabaseExample() {
    const { user, loading: authLoading } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [newReportTitle, setNewReportTitle] = useState('');
    const [reports, setReports] = useState([]);

    // Fetch reports (example)
    const { data: fetchedReports, loading: reportsLoading, refetch } = useSupabaseQuery(
        'civic_reports',
        {
            select: 'id, title, description, status, created_at',
            order: { column: 'created_at', ascending: false },
            limit: 10
        }
    );

    // CRUD operations
    const { insert: insertReport, loading: insertLoading } = useSupabaseInsert('civic_reports');
    const { update: updateReport } = useSupabaseUpdate('civic_reports');
    const { deleteRecord: deleteReport } = useSupabaseDelete('civic_reports');

    // Real-time subscription (example)
    useSupabaseSubscription('civic_reports', (payload) => {
        console.log('Real-time update:', payload);
        // Refresh data when changes occur
        refetch();
    });

    useEffect(() => {
        if (fetchedReports) {
            setReports(fetchedReports);
        }
    }, [fetchedReports]);

    // Authentication handlers
    const handleSignUp = async (e) => {
        e.preventDefault();
        const { data, error } = await signUp(email, password);
        if (error) {
            alert(`Sign up error: ${error.message}`);
        } else {
            alert('Sign up successful! Check your email for verification.');
            setEmail('');
            setPassword('');
        }
    };

    const handleSignIn = async (e) => {
        e.preventDefault();
        const { data, error } = await signIn(email, password);
        if (error) {
            alert(`Sign in error: ${error.message}`);
        } else {
            alert('Sign in successful!');
            setEmail('');
            setPassword('');
        }
    };

    const handleSignOut = async () => {
        const { error } = await signOut();
        if (error) {
            alert(`Sign out error: ${error.message}`);
        } else {
            alert('Signed out successfully!');
        }
    };

    // Database operation handlers
    const handleCreateReport = async (e) => {
        e.preventDefault();
        if (!user) {
            alert('Please sign in first');
            return;
        }

        const { data, error } = await insertReport({
            title: newReportTitle,
            description: 'Example report',
            category: 'example',
            user_id: user.id,
            status: 'pending'
        });

        if (error) {
            alert(`Create error: ${error.message}`);
        } else {
            alert('Report created!');
            setNewReportTitle('');
            refetch();
        }
    };

    const handleUpdateStatus = async (reportId, newStatus) => {
        const { error } = await updateReport(reportId, { status: newStatus });
        if (error) {
            alert(`Update error: ${error.message}`);
        } else {
            alert('Status updated!');
            refetch();
        }
    };

    const handleDeleteReport = async (reportId) => {
        if (!confirm('Are you sure you want to delete this report?')) return;

        const { error } = await deleteReport(reportId);
        if (error) {
            alert(`Delete error: ${error.message}`);
        } else {
            alert('Report deleted!');
            refetch();
        }
    };

    if (authLoading) {
        return <div className="p-8">Loading authentication...</div>;
    }

    return (
        <div className="max-w-4xl mx-auto p-8">
            <h1 className="text-3xl font-bold mb-6">Supabase Integration Example</h1>

            {/* Authentication Section */}
            <div className="mb-8 p-6 bg-white rounded-lg shadow">
                <h2 className="text-2xl font-semibold mb-4">Authentication</h2>

                {user ? (
                    <div>
                        <p className="mb-4">
                            ✅ Signed in as: <strong>{user.email}</strong>
                        </p>
                        <button
                            onClick={handleSignOut}
                            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                            Sign Out
                        </button>
                    </div>
                ) : (
                    <form className="space-y-4">
                        <div>
                            <label className="block mb-2">Email:</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-3 py-2 border rounded"
                                placeholder="your@email.com"
                            />
                        </div>
                        <div>
                            <label className="block mb-2">Password:</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-3 py-2 border rounded"
                                placeholder="••••••••"
                            />
                        </div>
                        <div className="flex gap-4">
                            <button
                                onClick={handleSignIn}
                                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                            >
                                Sign In
                            </button>
                            <button
                                onClick={handleSignUp}
                                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                            >
                                Sign Up
                            </button>
                        </div>
                    </form>
                )}
            </div>

            {/* Database Operations Section */}
            {user && (
                <div className="mb-8 p-6 bg-white rounded-lg shadow">
                    <h2 className="text-2xl font-semibold mb-4">Create Report</h2>
                    <form onSubmit={handleCreateReport} className="space-y-4">
                        <div>
                            <label className="block mb-2">Report Title:</label>
                            <input
                                type="text"
                                value={newReportTitle}
                                onChange={(e) => setNewReportTitle(e.target.value)}
                                className="w-full px-3 py-2 border rounded"
                                placeholder="Enter report title"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={insertLoading}
                            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
                        >
                            {insertLoading ? 'Creating...' : 'Create Report'}
                        </button>
                    </form>
                </div>
            )}

            {/* Reports List Section */}
            <div className="p-6 bg-white rounded-lg shadow">
                <h2 className="text-2xl font-semibold mb-4">Reports</h2>

                {reportsLoading ? (
                    <p>Loading reports...</p>
                ) : reports.length === 0 ? (
                    <p className="text-gray-500">No reports found. Create one above!</p>
                ) : (
                    <div className="space-y-4">
                        {reports.map((report) => (
                            <div key={report.id} className="p-4 border rounded">
                                <h3 className="text-xl font-semibold">{report.title}</h3>
                                <p className="text-gray-600">{report.description}</p>
                                <p className="text-sm text-gray-500 mt-2">
                                    Status: <span className="font-semibold">{report.status}</span>
                                </p>

                                {user && (
                                    <div className="mt-4 flex gap-2">
                                        <button
                                            onClick={() => handleUpdateStatus(report.id, 'resolved')}
                                            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                                        >
                                            Mark Resolved
                                        </button>
                                        <button
                                            onClick={() => handleDeleteReport(report.id)}
                                            className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Info Section */}
            <div className="mt-8 p-6 bg-blue-50 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">ℹ️ Note</h3>
                <p className="text-gray-700">
                    This is an example component demonstrating Supabase integration.
                    To use this in your app, make sure you have:
                </p>
                <ul className="list-disc list-inside mt-2 text-gray-700">
                    <li>Created the <code>civic_reports</code> table in Supabase</li>
                    <li>Enabled Row Level Security (RLS) policies</li>
                    <li>Configured your environment variables in <code>.env</code></li>
                </ul>
                <p className="mt-2 text-sm text-gray-600">
                    See <code>docs/SUPABASE_INTEGRATION.md</code> for complete setup instructions.
                </p>
            </div>
        </div>
    );
}

export default SupabaseExample;
