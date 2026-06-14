import Dexie from 'dexie';

class OfflineQueueDB extends Dexie {
  constructor() {
    super('OfflineQueueDB');
    this.version(1).stores({
      reports: '++id, category, description, latitude, longitude, imageBlob, timestamp, synced'
    });
  }
}

const db = new OfflineQueueDB();

export const saveReportOffline = async (reportData) => {
  try {
    const id = await db.reports.add({
      ...reportData,
      timestamp: new Date(),
      synced: false
    });
    return id;
  } catch (error) {
    console.error('Failed to save report offline:', error);
    throw error;
  }
};

export const getPendingReports = async () => {
  return await db.reports.where('synced').equals(false).toArray();
};

export const markReportSynced = async (id) => {
  await db.reports.update(id, { synced: true });
};

export const deleteReport = async (id) => {
  await db.reports.delete(id);
};

export const syncReports = async (apiUrl) => {
  const pendingReports = await getPendingReports();

  for (const report of pendingReports) {
    try {
      const formData = new FormData();
      formData.append('category', report.category);
      formData.append('description', report.description);
      formData.append('latitude', report.latitude);
      formData.append('longitude', report.longitude);
      if (report.imageBlob) {
        formData.append('image', report.imageBlob, 'offline-report.jpg');
      }

      const response = await fetch(`${apiUrl}/api/issues`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        await markReportSynced(report.id);
      } else {
        console.error('Failed to sync report:', report.id);
      }
    } catch (error) {
      console.error('Sync error for report:', report.id, error);
    }
  }
};

// Register background sync
export const registerBackgroundSync = () => {
  if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
    navigator.serviceWorker.ready.then(registration => {
      registration.sync.register('sync-reports');
    });
  }
};

// Listen for online event to sync
window.addEventListener('online', () => {
  syncReports(import.meta.env.VITE_API_URL || '');
});

// Listen for SW messages
navigator.serviceWorker?.addEventListener('message', event => {
  if (event.data && event.data.type === 'SYNC_REPORTS') {
    syncReports(import.meta.env.VITE_API_URL || '');
  }
});