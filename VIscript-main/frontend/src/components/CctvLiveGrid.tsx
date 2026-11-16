import React, { useState } from 'react';
import { Video, Plus, Trash2, Maximize2, Minimize2, RefreshCw, MapPin, AlertCircle, Sparkles, Loader2, Check } from 'lucide-react';
import { CameraData, apiClient } from '../api/client';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface CctvLiveGridProps {
  cameras: CameraData[];
  selectedCameraId?: string;
  onOpenAddModal: () => void;
  onCameraDeleted: (cameraId: string) => void;
  onDataUpdated?: () => void;
}

export const CctvLiveGrid: React.FC<CctvLiveGridProps> = ({
  cameras,
  selectedCameraId,
  onOpenAddModal,
  onCameraDeleted,
  onDataUpdated,
}) => {
  const [fullscreenCamId, setFullscreenCamId] = useState<string | null>(null);
  const [streamKeys, setStreamKeys] = useState<Record<string, number>>({});
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [transcribingId, setTranscribingId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<Record<string, string>>({});

  // Filter cameras if user selected a specific camera from Navbar dropdown
  const displayedCameras = selectedCameraId
    ? cameras.filter((c) => c.id === selectedCameraId)
    : cameras;

  const handleRefreshStream = (cameraId: string) => {
    setStreamKeys((prev) => ({
      ...prev,
      [cameraId]: (prev[cameraId] || 0) + 1,
    }));
  };

  const handleTranscribeNow = async (cameraId: string) => {
    setTranscribingId(cameraId);
    try {
      const res = await apiClient.transcribeLiveCamera(cameraId);
      setSuccessMsg((prev) => ({
        ...prev,
        [cameraId]: `Transcribed: ${res.event.activity.slice(0, 40)}...`,
      }));
      if (onDataUpdated) {
        onDataUpdated();
      }
      setTimeout(() => {
        setSuccessMsg((prev) => {
          const next = { ...prev };
          delete next[cameraId];
          return next;
        });
      }, 5000);
    } catch (err: any) {
      console.error('Failed to transcribe live feed:', err);
      alert(err.response?.data?.detail || 'Failed to capture or analyze live camera frame.');
    } finally {
      setTranscribingId(null);
    }
  };

  const handleDelete = async (cameraId: string, cameraName: string) => {
    if (!window.confirm(`Are you sure you want to disconnect and remove camera "${cameraName}"?`)) {
      return;
    }
    setDeletingId(cameraId);
    try {
      await apiClient.deleteCamera(cameraId);
      onCameraDeleted(cameraId);
      if (fullscreenCamId === cameraId) {
        setFullscreenCamId(null);
      }
    } catch (err) {
      console.error('Failed to delete camera:', err);
      alert('Failed to remove camera. Please verify backend connection.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div style={{ marginBottom: '2rem' }}>
      {/* Section Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(15, 163, 127, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-teal)',
            }}
          >
            <Video size={18} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              Live CCTV Video Wall
              {displayedCameras.length > 0 && (
                <span
                  style={{
                    background: 'rgba(15, 163, 127, 0.15)',
                    color: 'var(--accent-teal)',
                    border: '1px solid rgba(15, 163, 127, 0.3)',
                    fontSize: '0.7rem',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    fontWeight: 600,
                  }}
                >
                  {displayedCameras.length} {displayedCameras.length === 1 ? 'Feed Active' : 'Feeds Active'}
                </span>
              )}
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
              Continuous Vision AI frame sampling, real-time anomaly detection &amp; narrative transcript synthesis
            </p>
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={onOpenAddModal}
          style={{ padding: '0.5rem 1rem', fontSize: '0.84rem' }}
        >
          <Plus size={15} />
          <span>Add CCTV Camera</span>
        </button>
      </div>

      {/* Empty State when no cameras exist */}
      {displayedCameras.length === 0 ? (
        <div
          className="card"
          style={{
            textAlign: 'center',
            padding: '3rem 2rem',
            background: 'linear-gradient(145deg, #16243b, #101a2d)',
            border: '1px dashed var(--card-border)',
            borderRadius: '16px',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(15, 163, 127, 0.1)',
              border: '1px solid rgba(15, 163, 127, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem',
              color: 'var(--accent-teal)',
            }}
          >
            <Video size={30} />
          </div>

          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>
            {selectedCameraId ? 'Selected Camera Not Found' : 'No CCTV Cameras Connected Yet'}
          </h3>
          <p
            style={{
              fontSize: '0.86rem',
              color: 'var(--text-secondary)',
              maxWidth: '540px',
              margin: '0 auto 1.5rem',
              lineHeight: 1.5,
            }}
          >
            Connect your RTSP IP cameras or local system webcams. VisualIQ continuously transcribes the live stream using Vision AI, flags security anomalies, and compiles searchable transcripts automatically.
          </p>

          <button
            className="btn btn-primary"
            onClick={onOpenAddModal}
            style={{ padding: '0.65rem 1.4rem' }}
          >
            <Plus size={16} />
            <span>Connect First CCTV Camera</span>
          </button>
        </div>
      ) : (
        /* Video Feeds Grid */
        <div
          style={{
            display: 'grid',
            gridTemplateColumns:
              fullscreenCamId
                ? '1fr'
                : displayedCameras.length === 1
                ? '1fr'
                : 'repeat(auto-fill, minmax(440px, 1fr))',
            gap: '1.25rem',
          }}
        >
          {displayedCameras
            .filter((cam) => !fullscreenCamId || cam.id === fullscreenCamId)
            .map((cam) => {
              const streamKey = streamKeys[cam.id] || 0;
              const liveUrl = `${API_BASE_URL}/api/cameras/${cam.id}/live?k=${streamKey}`;
              const isFullscreen = fullscreenCamId === cam.id;
              const isTranscribing = transcribingId === cam.id;
              const feedback = successMsg[cam.id];

              return (
                <div
                  key={cam.id}
                  className="card"
                  style={{
                    padding: 0,
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    background: '#0d1524',
                    border: '1px solid #283e65',
                    borderRadius: '14px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                    transition: 'all 0.25s ease',
                  }}
                >
                  {/* Stream Card Header */}
                  <div
                    style={{
                      padding: '0.75rem 1rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'rgba(18, 30, 50, 0.95)',
                      borderBottom: '1px solid rgba(40, 62, 101, 0.6)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: '#10b981',
                          boxShadow: '0 0 8px #10b981',
                          display: 'inline-block',
                        }}
                      />
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff' }}>
                        {cam.name}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <button
                        onClick={() => handleTranscribeNow(cam.id)}
                        disabled={isTranscribing}
                        title="Analyze current live frame and generate transcript now"
                        style={{
                          background: 'rgba(15, 163, 127, 0.15)',
                          border: '1px solid rgba(15, 163, 127, 0.4)',
                          color: 'var(--accent-teal)',
                          cursor: 'pointer',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '0.74rem',
                          fontWeight: 600,
                        }}
                      >
                        {isTranscribing ? <Loader2 size={12} className="pulse-alert" /> : <Sparkles size={12} />}
                        <span>{isTranscribing ? 'Analyzing...' : 'Transcribe Now'}</span>
                      </button>

                      <button
                        onClick={() => handleRefreshStream(cam.id)}
                        title="Reconnect stream"
                        style={{
                          background: 'rgba(255,255,255,0.06)',
                          border: 'none',
                          color: 'var(--text-secondary)',
                          cursor: 'pointer',
                          padding: '5px 7px',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                          fontSize: '0.75rem',
                        }}
                      >
                        <RefreshCw size={13} />
                      </button>
                      <button
                        onClick={() => setFullscreenCamId(isFullscreen ? null : cam.id)}
                        title={isFullscreen ? 'Exit Fullscreen' : 'Expand Stream'}
                        style={{
                          background: 'rgba(255,255,255,0.06)',
                          border: 'none',
                          color: 'var(--text-secondary)',
                          cursor: 'pointer',
                          padding: '5px 7px',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
                      </button>
                      <button
                        onClick={() => handleDelete(cam.id, cam.name)}
                        disabled={deletingId === cam.id}
                        title="Remove Camera"
                        style={{
                          background: 'rgba(239, 68, 68, 0.12)',
                          border: 'none',
                          color: '#f87171',
                          cursor: 'pointer',
                          padding: '5px 7px',
                          borderRadius: '6px',
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>

                  {/* Video Viewport */}
                  <div
                    style={{
                      position: 'relative',
                      width: '100%',
                      aspectRatio: isFullscreen ? '16/9' : '16/10',
                      maxHeight: isFullscreen ? '620px' : '360px',
                      background: '#070c14',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                    }}
                  >
                    {cam.stream_url ? (
                      <img
                        src={liveUrl}
                        alt={`Live stream for ${cam.name}`}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'contain',
                          display: 'block',
                        }}
                        onError={() => {
                          console.warn(`Stream load failed for camera ${cam.id}`);
                        }}
                      />
                    ) : (
                      <div
                        style={{
                          textAlign: 'center',
                          padding: '1.5rem',
                          color: 'var(--text-muted)',
                        }}
                      >
                        <AlertCircle size={28} style={{ margin: '0 auto 8px', color: 'var(--anomaly-amber)' }} />
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                          No Live Stream URL Configured
                        </div>
                      </div>
                    )}

                    {/* Stream Overlay Badges */}
                    <div
                      style={{
                        position: 'absolute',
                        top: '10px',
                        left: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        background: 'rgba(0, 0, 0, 0.65)',
                        backdropFilter: 'blur(4px)',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        color: '#fff',
                      }}
                    >
                      <span
                        style={{
                          width: '7px',
                          height: '7px',
                          borderRadius: '50%',
                          background: '#ef4444',
                          animation: 'pulse-slow 2s infinite',
                          display: 'inline-block',
                        }}
                      />
                      <span>LIVE</span>
                    </div>

                    <div
                      style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        background: 'rgba(15, 163, 127, 0.25)',
                        backdropFilter: 'blur(4px)',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: '1px solid rgba(15, 163, 127, 0.4)',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        color: 'var(--accent-teal)',
                      }}
                    >
                      <Sparkles size={11} />
                      <span>AI Transcribing</span>
                    </div>

                    {/* Instant Feedback Toast */}
                    {feedback && (
                      <div
                        style={{
                          position: 'absolute',
                          bottom: '12px',
                          left: '12px',
                          right: '12px',
                          background: 'rgba(15, 163, 127, 0.95)',
                          color: '#fff',
                          padding: '6px 12px',
                          borderRadius: '6px',
                          fontSize: '0.76rem',
                          fontWeight: 600,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                        }}
                      >
                        <Check size={14} />
                        <span>{feedback}</span>
                      </div>
                    )}

                    <div
                      style={{
                        position: 'absolute',
                        bottom: '8px',
                        right: '10px',
                        background: 'rgba(0, 0, 0, 0.7)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.68rem',
                        color: '#94a3b8',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      ID: {cam.id}
                    </div>
                  </div>

                  {/* Stream Card Footer Details */}
                  <div
                    style={{
                      padding: '0.65rem 1rem',
                      background: 'rgba(14, 23, 38, 0.8)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.78rem',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <MapPin size={13} color="var(--accent-teal)" />
                      <span>{cam.location || 'Main Zone'}</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {cam.stream_url ? (cam.stream_url.length > 25 ? `${cam.stream_url.slice(0, 22)}...` : cam.stream_url) : 'Offline File Mode'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
};
