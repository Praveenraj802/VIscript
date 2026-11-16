import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { QueryPage } from './pages/QueryPage';
import { LoginPage } from './pages/LoginPage';
import { AddCameraModal } from './components/AddCameraModal';
import { ErrorBoundary } from './components/ErrorBoundary';
import { apiClient, CameraData } from './api/client';

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(localStorage.getItem('visualiq_token'));
  });
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [cameras, setCameras] = useState<CameraData[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>('');
  const [alertsCount, setAlertsCount] = useState<number>(0);
  const [isAddCameraOpen, setIsAddCameraOpen] = useState<boolean>(false);

  // Validate active session token on mount
  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem('visualiq_token');
      if (!token) {
        setIsAuthenticated(false);
        return;
      }
      try {
        await apiClient.getMe();
        setIsAuthenticated(true);
      } catch (err) {
        console.warn('Session verification failed:', err);
        apiClient.logout();
        setIsAuthenticated(false);
      }
    };

    verifyAuth();

    // Listen for unauthorized 401 events from axios interceptor
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
    };
    window.addEventListener('visualiq:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('visualiq:unauthorized', handleUnauthorized);
    };
  }, []);

  const refreshCameras = async () => {
    try {
      const camList = await apiClient.getCameras();
      setCameras(camList);
    } catch (e) {
      console.warn('Failed to refresh cameras list:', e);
    }
  };

  // Fetch camera and alert metadata when authenticated
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchInitialMeta = async () => {
      try {
        const [camList, alertsList] = await Promise.all([
          apiClient.getCameras(),
          apiClient.getAlerts(),
        ]);
        setCameras(camList);
        setAlertsCount(alertsList.filter((a: any) => !a.resolved).length);
      } catch (e) {
        console.warn('Initial metadata load warning:', e);
      }
    };
    fetchInitialMeta();
  }, [isAuthenticated]);

  const handleLogout = () => {
    apiClient.logout();
    setIsAuthenticated(false);
  };

  const handleCameraAdded = (newCam: CameraData) => {
    setCameras((prev) => {
      const exists = prev.some((c) => c.id === newCam.id);
      return exists ? prev.map((c) => (c.id === newCam.id ? newCam : c)) : [...prev, newCam];
    });
    if (!selectedCameraId) {
      setSelectedCameraId(newCam.id);
    }
  };

  const handleCameraDeleted = (deletedId: string) => {
    setCameras((prev) => prev.filter((c) => c.id !== deletedId));
    if (selectedCameraId === deletedId) {
      setSelectedCameraId('');
    }
  };

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="app-container">
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        cameras={cameras}
        selectedCameraId={selectedCameraId}
        onSelectCamera={setSelectedCameraId}
        onLogout={handleLogout}
        alertsCount={alertsCount}
        onOpenAddCamera={() => setIsAddCameraOpen(true)}
      />

      <main className="main-content">
        <ErrorBoundary fallbackTitle="VisualIQ Module Error">
          {currentPage === 'dashboard' && (
            <DashboardPage
              selectedCameraId={selectedCameraId}
              cameras={cameras}
              onOpenAddCamera={() => setIsAddCameraOpen(true)}
              onCameraDeleted={handleCameraDeleted}
              onRefreshData={refreshCameras}
            />
          )}
          {currentPage === 'upload' && (
            <UploadPage
              onUploadSuccess={() => {
                refreshCameras();
                setCurrentPage('dashboard');
              }}
              cameras={cameras}
              defaultCameraId={selectedCameraId || (cameras[0]?.id ?? '')}
            />
          )}
          {currentPage === 'query' && (
            <QueryPage selectedCameraId={selectedCameraId} />
          )}
        </ErrorBoundary>
      </main>

      {/* Add Camera Modal */}
      <AddCameraModal
        isOpen={isAddCameraOpen}
        onClose={() => setIsAddCameraOpen(false)}
        onCameraAdded={handleCameraAdded}
      />

      <footer style={{
        textAlign: 'center',
        padding: '1.5rem',
        borderTop: '1px solid var(--card-border)',
        fontSize: '0.8rem',
        color: 'var(--text-muted)'
      }}>
        VisualIQ Enterprise V2.0 • Real-time Surveillance Intelligence • DPDP Act Compliant
      </footer>
    </div>
  );
};

export default App;
