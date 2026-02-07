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
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'open': return 'text-blue-600 bg-blue-100';
      case 'in_progress': return 'text-yellow-600 bg-yellow-100';
      case 'escalated': return 'text-red-600 bg-red-100';
      case 'resolved': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading grievances...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadData}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Grievance Management</h1>
          <p className="text-gray-600">Monitor and manage grievance escalations</p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-blue-600">{stats.total_grievances}</div>
              <div className="text-sm text-gray-600">Total Grievances</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-orange-600">{stats.escalated_grievances}</div>
              <div className="text-sm text-gray-600">Escalated</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-yellow-600">{stats.active_grievances}</div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-green-600">{stats.resolved_grievances}</div>
              <div className="text-sm text-gray-600">Resolved</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-2xl font-bold text-purple-600">{stats.escalation_rate.toFixed(1)}%</div>
              <div className="text-sm text-gray-600">Escalation Rate</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="border rounded px-3 py-2"
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
              className="border rounded px-3 py-2"
            />
            <input
              type="number"
              placeholder="Limit"
              value={filters.limit}
              onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value) || 20})}
              className="border rounded px-3 py-2"
              min="1"
              max="200"
            />
            <button
              onClick={() => setFilters({...filters, offset: Math.max(0, filters.offset - filters.limit)})}
              disabled={filters.offset === 0}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setFilters({...filters, offset: filters.offset + filters.limit})}
              disabled={grievances.length < filters.limit}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>

        {/* Grievances List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Authority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Escalations
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {grievances.map((grievance) => (
                  <tr key={grievance.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {grievance.unique_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {grievance.assigned_authority}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {grievance.escalation_history.length}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => setSelectedGrievance(grievance)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        View Details
                      </button>
                      {grievance.status !== 'resolved' && (
                        <button
                          onClick={() => handleEscalate(grievance.id)}
                          className="text-orange-600 hover:text-orange-900"
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
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">Grievance Details</h3>
                <button
                  onClick={() => setSelectedGrievance(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2">Basic Information</h4>
                  <div className="space-y-2 text-sm">
                    <p><strong>ID:</strong> {selectedGrievance.unique_id}</p>
                    <p><strong>Category:</strong> {selectedGrievance.category}</p>
                    <p><strong>Severity:</strong>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(selectedGrievance.severity)}`}>
                        {selectedGrievance.severity}
                      </span>
                    </p>
                    <p><strong>Status:</strong>
                      <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedGrievance.status)}`}>
                        {selectedGrievance.status.replace('_', ' ')}
                      </span>
                    </p>
                    <p><strong>Created:</strong> {new Date(selectedGrievance.created_at).toLocaleString()}</p>
                    <p><strong>SLA Deadline:</strong> {new Date(selectedGrievance.sla_deadline).toLocaleString()}</p>
                    <p><strong>Assigned Authority:</strong> {selectedGrievance.assigned_authority}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Location</h4>
                  <div className="space-y-2 text-sm">
                    <p><strong>Pincode:</strong> {selectedGrievance.pincode || 'N/A'}</p>
                    <p><strong>City:</strong> {selectedGrievance.city || 'N/A'}</p>
                    <p><strong>District:</strong> {selectedGrievance.district || 'N/A'}</p>
                    <p><strong>State:</strong> {selectedGrievance.state || 'N/A'}</p>
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="font-medium mb-2">Escalation History</h4>
                {selectedGrievance.escalation_history.length === 0 ? (
                  <p className="text-gray-500 text-sm">No escalations recorded</p>
                ) : (
                  <div className="space-y-3">
                    {selectedGrievance.escalation_history.map((escalation, index) => (
                      <div key={escalation.id} className="border rounded p-3 bg-gray-50">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-sm font-medium">
                              Escalation #{index + 1}
                            </p>
                            <p className="text-xs text-gray-600">
                              {new Date(escalation.timestamp).toLocaleString()}
                            </p>
                          </div>
                          <span className="px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800">
                            {escalation.reason.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="mt-2 text-sm">
                          <p><strong>From:</strong> {escalation.previous_authority}</p>
                          <p><strong>To:</strong> {escalation.new_authority}</p>
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