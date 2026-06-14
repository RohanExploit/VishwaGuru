import React, { useState, useEffect } from 'react';
import { grievancesApi } from '../api';

const GrievanceView = () => {
  const [grievances, setGrievances] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGrievance, setSelectedGrievance] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    category: '',
    limit: 20,
    offset: 0
  });

  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [grievancesData, statsData] = await Promise.all([
        grievancesApi.getAll(filters),
        grievancesApi.getStats()
      ]);

      setGrievances(grievancesData);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading grievance data:', err);
      setError('Failed to load grievance data');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleEscalate = async (grievanceId) => {
    const reason = prompt('Enter reason for escalation:');
    if (!reason) return;

    try {
      await grievancesApi.escalate(grievanceId, reason);
      alert('Grievance escalated successfully');
      loadData(); // Refresh data
    } catch (err) {
      console.error('Error escalating grievance:', err);
      alert('Failed to escalate grievance');
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      case 'high': return 'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
      case 'low': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700/50';
    }
  };

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'open': return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30';
      case 'in_progress': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
      case 'escalated': return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      case 'resolved': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700/50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading grievances...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <p className="text-red-600 dark:text-red-400">{error}</p>
            <button
              onClick={loadData}
              className="mt-4 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded hover:bg-blue-700 dark:hover:bg-blue-600 transition"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Grievance Management</h1>
          <p className="text-gray-600 dark:text-gray-400">Monitor and manage grievance escalations</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-md border dark:border-gray-700">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total_grievances}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Grievances</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-md border dark:border-gray-700">
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">{stats.escalated_grievances}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Escalated</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-md border dark:border-gray-700">
              <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.active_grievances}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Active</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-md border dark:border-gray-700">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.resolved_grievances}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Resolved</div>
            </div>
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-md border dark:border-gray-700">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">{stats.escalation_rate.toFixed(1)}%</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Escalation Rate</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-md border dark:border-gray-700 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="escalated">Escalated</option>
              <option value="resolved">Resolved</option>
            </select>
            <input
              type="text"
              placeholder="Filter by category"
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value})}
              className="border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
            />
            <input
              type="number"
              placeholder="Limit"
              value={filters.limit}
              onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value) || 20})}
              className="border dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              min="1"
              max="200"
            />
            <button
              onClick={() => setFilters({...filters, offset: Math.max(0, filters.offset - filters.limit)})}
              disabled={filters.offset === 0}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition"
            >
              Previous
            </button>
            <button
              onClick={() => setFilters({...filters, offset: filters.offset + filters.limit})}
              disabled={grievances.length < filters.limit}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition"
            >
              Next
            </button>
          </div>
        </div>

        {/* Grievances List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-md overflow-hidden border dark:border-gray-700">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Authority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Escalations
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {grievances.map((grievance) => (
                  <tr key={grievance.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      {grievance.unique_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {grievance.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(grievance.severity)}`}>
                        {grievance.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(grievance.status)}`}>
                        {grievance.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {grievance.assigned_authority}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {grievance.escalation_history.length}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => setSelectedGrievance(grievance)}
                        className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 mr-4 transition"
                      >
                        View Details
                      </button>
                      {grievance.status !== 'resolved' && (
                        <button
                          onClick={() => handleEscalate(grievance.id)}
                          className="text-orange-600 dark:text-orange-400 hover:text-orange-900 dark:hover:text-orange-300 transition"
                        >
                          Escalate
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Grievance Detail Modal */}
        {selectedGrievance && (
          <div className="fixed inset-0 bg-gray-600 dark:bg-gray-950 bg-opacity-50 dark:bg-opacity-75 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border border-gray-300 dark:border-gray-600 w-11/12 max-w-4xl shadow-lg dark:shadow-2xl rounded-md bg-white dark:bg-gray-800">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Grievance Details</h3>
                <button
                  onClick={() => setSelectedGrievance(null)}
                  className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400 transition"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2 text-gray-900 dark:text-white">Basic Information</h4>
                  <div className="space-y-2 text-sm text-gray-900 dark:text-gray-300">
                    <p><strong className="text-gray-700 dark:text-gray-200">ID:</strong> {selectedGrievance.unique_id}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">Category:</strong> {selectedGrievance.category}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">Severity:</strong>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(selectedGrievance.severity)}`}>
                        {selectedGrievance.severity}
                      </span>
                    </p>
                    <p><strong className="text-gray-700 dark:text-gray-200">Status:</strong>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedGrievance.status)}`}>
                        {selectedGrievance.status.replace('_', ' ')}
                      </span>
                    </p>
                    <p><strong className="text-gray-700 dark:text-gray-200">Created:</strong> {new Date(selectedGrievance.created_at).toLocaleString()}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">SLA Deadline:</strong> {new Date(selectedGrievance.sla_deadline).toLocaleString()}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">Assigned Authority:</strong> {selectedGrievance.assigned_authority}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2 text-gray-900 dark:text-white">Location</h4>
                  <div className="space-y-2 text-sm text-gray-900 dark:text-gray-300">
                    <p><strong className="text-gray-700 dark:text-gray-200">Pincode:</strong> {selectedGrievance.pincode || 'N/A'}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">City:</strong> {selectedGrievance.city || 'N/A'}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">District:</strong> {selectedGrievance.district || 'N/A'}</p>
                    <p><strong className="text-gray-700 dark:text-gray-200">State:</strong> {selectedGrievance.state || 'N/A'}</p>
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="font-medium mb-2 text-gray-900 dark:text-white">Escalation History</h4>
                {selectedGrievance.escalation_history.length === 0 ? (
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No escalations recorded</p>
                ) : (
                  <div className="space-y-3">
                    {selectedGrievance.escalation_history.map((escalation, index) => (
                      <div key={escalation.id} className="border border-gray-200 dark:border-gray-700 rounded p-3 bg-gray-50 dark:bg-gray-700">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              Escalation #{index + 1}
                            </p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {new Date(escalation.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                            {escalation.reason.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="mt-2 text-sm text-gray-900 dark:text-gray-300">
                          <p><strong className="text-gray-700 dark:text-gray-200">From:</strong> {escalation.previous_authority}</p>
                          <p><strong className="text-gray-700 dark:text-gray-200">To:</strong> {escalation.new_authority}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GrievanceView;