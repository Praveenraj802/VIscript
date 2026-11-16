import React, { useState, useEffect } from 'react';
import { StatCards } from '../components/StatCards';
import { AlertPanel } from '../components/AlertPanel';
import { Timeline, TimelineEvent, TranscriptItem } from '../components/Timeline';
import { CctvLiveGrid } from '../components/CctvLiveGrid';
import { apiClient, CameraData } from '../api/client';
import { Sparkles, RefreshCw, FileText, Calendar, AlertCircle, Plus } from 'lucide-react';

interface DashboardPageProps {
  selectedCameraId: string;
  cameras: CameraData[];
  onOpenAddCamera: () => void;
  onCameraDeleted: (cameraId: string) => void;
  onRefreshData?: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  selectedCameraId,
  cameras,
  onOpenAddCamera,
  onCameraDeleted,
  onRefreshData,
}) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [activeView, setActiveView] = useState<'events' | 'transcripts'>('events');
  const [digest, setDigest] = useState<string | null>(null);
  const [isGeneratingDigest, setIsGeneratingDigest] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [eventsData, transcriptsData, alertsData] = await Promise.all([
        apiClient.getEvents(selectedCameraId),
        apiClient.getTranscripts(selectedCameraId),
        apiClient.getAlerts(selectedCameraId),
      ]);
      setEvents(eventsData);
      setTranscripts(transcriptsData);
      setAlerts(alertsData);
      if (onRefreshData) {
        onRefreshData();
      }
    } catch (err: any) {
      console.error('Error loading dashboard data:', err);
      setLoadError('Unable to sync live surveillance streams. Please verify the backend service connection.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCameraId]);

  const handleResolveAlert = async (alertId: string) => {
    await apiClient.resolveAlert(alertId);
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, resolved: true } : a))
    );
  };

  const handleGenerateDigest = async () => {
    setIsGeneratingDigest(true);
    try {
      const res = await apiClient.generateDigest();
      setDigest(res.digest);
    } catch (err) {
      console.error('Error generating digest:', err);
    } finally {
      setIsGeneratingDigest(false);
    }
  };

  const highestSeverity = events.length > 0
    ? Math.max(...events.map((e) => e.anomaly_score))
    : 0;

  const activeCamerasCount = selectedCameraId
    ? (cameras.some((c) => c.id === selectedCameraId) ? 1 : 0)
    : cameras.filter((c) => c.status === 'active').length;

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.5px', color: '#fff' }}>
            Surveillance Intelligence Dashboard
          </h1>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={14} />
            <span>Live Surveillance Monitoring &amp; Event Analysis</span>
            {selectedCameraId && (
              <span style={{ background: 'var(--card-bg)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--card-border)', color: 'var(--accent-teal)' }}>
                Filtered: {selectedCameraId}
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={loadData} disabled={isLoading}>
            <RefreshCw size={14} className={isLoading ? 'pulse-alert' : ''} />
            <span>{isLoading ? 'Syncing...' : 'Refresh Feeds'}</span>
          </button>
          <button
            className="btn btn-secondary"
            onClick={onOpenAddCamera}
            style={{ borderColor: 'rgba(15, 163, 127, 0.4)', color: 'var(--accent-teal)' }}
          >
            <Plus size={15} />
            <span>Add Camera</span>
          </button>
          <button
            className="btn btn-primary"
            onClick={handleGenerateDigest}
            disabled={isGeneratingDigest}
          >
            <Sparkles size={16} />
            <span>{isGeneratingDigest ? 'Synthesizing Digest...' : 'Generate Today Summary'}</span>
          </button>
        </div>
      </div>

      {/* Connectivity / Sync Error Banner */}
      {loadError && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '8px',
          padding: '0.75rem 1.25rem',
          marginBottom: '1.5rem',
          color: '#fca5a5',
          fontSize: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} />
            <span>{loadError}</span>
          </div>
          <button className="btn btn-secondary" onClick={loadData} style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}>
            Retry Sync
          </button>
        </div>
      )}

      {/* Stat Cards with Loading Skeleton */}
      <StatCards
        totalEvents={events.length}
        activeAlerts={alerts.filter((a) => !a.resolved).length}
        activeCameras={activeCamerasCount}
        highestSeverity={highestSeverity}
        isLoading={isLoading}
      />

      {/* Real-time CCTV Live Video Wall */}
      <CctvLiveGrid
        cameras={cameras}
        selectedCameraId={selectedCameraId}
        onOpenAddModal={onOpenAddCamera}
        onCameraDeleted={onCameraDeleted}
        onDataUpdated={loadData}
      />

      {/* Daily Digest Newspaper / Executive Card */}
      {digest && (
        <div className="card" style={{ marginBottom: '1.5rem', background: 'linear-gradient(145deg, #1b2f4f, #152238)', border: '1px solid #385170' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <FileText size={18} color="var(--accent-teal)" />
            <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--accent-teal)' }}>
              Executive Daily Intelligence Report
            </span>
          </div>
          <p style={{ fontSize: '1rem', color: '#f1f5f9', lineHeight: 1.7, fontStyle: 'normal' }}>
            "{digest}"
          </p>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Synthesized by Gemini 2.5 Flash from all active camera shifts • Ready for Society Management Committee review
          </div>
        </div>
      )}

      {/* Anomaly Alerts Panel */}
      <AlertPanel alerts={alerts} onResolve={handleResolveAlert} />

      {/* Event Timeline & Transcripts */}
      <Timeline
        events={events}
        transcripts={transcripts}
        activeView={activeView}
        onToggleView={setActiveView}
      />
    </div>
  );
};
