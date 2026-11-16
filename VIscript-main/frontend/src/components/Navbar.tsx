import React from 'react';
import { Shield, Video, UploadCloud, MessageSquare, LogOut, Plus } from 'lucide-react';
import { apiClient } from '../api/client';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  cameras: Array<{ id: string; name: string }>;
  selectedCameraId: string;
  onSelectCamera: (cameraId: string) => void;
  onLogout: () => void;
  alertsCount: number;
  onOpenAddCamera?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPage,
  onNavigate,
  cameras,
  selectedCameraId,
  onSelectCamera,
  onLogout,
  alertsCount,
  onOpenAddCamera,
}) => {
  return (
    <header className="navbar">
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div className="brand" onClick={() => onNavigate('dashboard')} style={{ cursor: 'pointer' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #0fa37f, #152238)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid #283e65'
          }}>
            <Shield size={20} color="#fff" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Visual<span style={{ color: 'var(--accent-teal)' }}>IQ</span></span>
              <span className="brand-badge">V2.0 PRO</span>
            </div>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 400 }}>
              AI Surveillance Transcript Engine
            </span>
          </div>
        </div>

        {/* Camera Selector & Add Camera Action */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Video size={16} color="var(--accent-teal)" />
          <select
            className="camera-select"
            value={selectedCameraId}
            onChange={(e) => onSelectCamera(e.target.value)}
          >
            <option value="">All Monitored Cameras ({cameras.length})</option>
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          {onOpenAddCamera && (
            <button
              onClick={onOpenAddCamera}
              className="btn btn-primary"
              title="Add New CCTV Camera"
              style={{
                padding: '0.42rem 0.75rem',
                fontSize: '0.8rem',
                borderRadius: '6px',
                whiteSpace: 'nowrap',
              }}
            >
              <Plus size={14} />
              <span>Add Camera</span>
            </button>
          )}
        </div>
      </div>

      {/* Nav Items */}
      <nav className="nav-links">
        <button
          className={`nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
          onClick={() => onNavigate('dashboard')}
        >
          <Shield size={16} />
          <span>Dashboard & Timeline</span>
          {alertsCount > 0 && (
            <span style={{
              background: 'var(--anomaly-red)',
              color: '#fff',
              fontSize: '0.65rem',
              padding: '1px 6px',
              borderRadius: '10px',
              fontWeight: 700
            }}>
              {alertsCount}
            </span>
          )}
        </button>

        <button
          className={`nav-item ${currentPage === 'upload' ? 'active' : ''}`}
          onClick={() => onNavigate('upload')}
        >
          <UploadCloud size={16} />
          <span>Ingest Footage</span>
        </button>

        <button
          className={`nav-item ${currentPage === 'query' ? 'active' : ''}`}
          onClick={() => onNavigate('query')}
        >
          <MessageSquare size={16} />
          <span>Intelligence Q&A</span>
        </button>
      </nav>

      {/* User profile & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--accent-teal)' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-teal)', display: 'inline-block' }}></span>
          <span style={{ fontWeight: 600 }}>Gemini 2.5 Flash</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', borderLeft: '1px solid var(--card-border)', paddingLeft: '16px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {apiClient.getCurrentUser()?.name || apiClient.getCurrentUser()?.email || 'Officer'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {apiClient.getCurrentUser()?.role || 'Security Operator'}
            </div>
          </div>
          <button
            onClick={onLogout}
            title="Log Out"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px'
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};
