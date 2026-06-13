import React, { useState, useEffect } from 'react';
import { adminApi } from '../api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const AdminDashboard = () => {
    const [activeTab, setActiveTab] = useState('users');
    const [users, setUsers] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            if (activeTab === 'users') {
                const data = await adminApi.getUsers();
                setUsers(data);
            } else if (activeTab === 'stats') {
                const data = await adminApi.getStats();
                setStats(data);
            }
        } catch (err) {
            setError(err.message || 'Failed to fetch data');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <div className="w-64 bg-gray-800 text-white flex flex-col">
                <div className="p-6 text-2xl font-bold border-b border-gray-700">
                    Admin Portal
                </div>
                <nav className="flex-1 p-4 space-y-2">
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`w-full text-left px-4 py-2 rounded ${activeTab === 'users' ? 'bg-gray-700' : 'hover:bg-gray-700'}`}
                    >
                        User Management
                    </button>
                    <button
                        onClick={() => setActiveTab('stats')}
                        className={`w-full text-left px-4 py-2 rounded ${activeTab === 'stats' ? 'bg-gray-700' : 'hover:bg-gray-700'}`}
                    >
                        System Statistics
                    </button>
                </nav>
                <div className="p-4 border-t border-gray-700">
                    <div className="mb-4">
                        <p className="text-sm text-gray-400">Logged in as:</p>
                        <p className="font-semibold">{user?.full_name}</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded transition"
                    >
                        Logout
                    </button>
                    <button
                        onClick={() => navigate('/')}
                        className="w-full mt-2 text-center text-gray-400 hover:text-white text-sm"
                    >
                        Back to App
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
                <header className="bg-white shadow p-6">
                    <h1 className="text-2xl font-bold text-gray-800 capitalize">
                        {activeTab === 'users' ? 'User Management' : 'System Statistics'}
                    </h1>
                </header>

                <main className="p-6">
                    {loading ? (
                        <div className="flex justify-center items-center h-64">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        </div>
                    ) : error ? (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            {error}
                        </div>
                    ) : (
                        <div>
                            {activeTab === 'users' && (
                                <div className="bg-white shadow rounded-lg overflow-hidden">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {users.map((u) => (
                                                <tr key={u.id}>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm font-medium text-gray-900">{u.full_name || 'N/A'}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm text-gray-500">{u.email}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'}`}>
                                                            {u.role}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                            {u.is_active ? 'Active' : 'Inactive'}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {activeTab === 'stats' && stats && (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-gray-500 text-sm uppercase font-semibold">Total Users</div>
                                        <div className="text-3xl font-bold text-gray-800 mt-2">{stats.total_users}</div>
                                    </div>
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-gray-500 text-sm uppercase font-semibold">Active Users</div>
                                        <div className="text-3xl font-bold text-green-600 mt-2">{stats.active_users}</div>
                                    </div>
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-gray-500 text-sm uppercase font-semibold">Admin Users</div>
                                        <div className="text-3xl font-bold text-purple-600 mt-2">{stats.admin_count}</div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default AdminDashboard;
