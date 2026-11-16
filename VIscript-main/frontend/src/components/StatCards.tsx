import React from 'react';
import { Eye, AlertTriangle, Video, ShieldCheck } from 'lucide-react';

interface StatCardsProps {
  totalEvents: number;
  activeAlerts: number;
  activeCameras: number;
  highestSeverity: number;
  isLoading?: boolean;
}

export const StatCards: React.FC<StatCardsProps> = ({
  totalEvents,
  activeAlerts,
  activeCameras,
  highestSeverity,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="stats-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-card" style={{ opacity: 0.7 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <div style={{ height: '14px', width: '90px', background: 'var(--card-border)', borderRadius: '4px' }} className="pulse-alert" />
              <div style={{ height: '18px', width: '18px', background: 'var(--card-border)', borderRadius: '4px' }} />
            </div>
            <div style={{ height: '28px', width: '60px', background: 'var(--card-border)', borderRadius: '6px', marginBottom: '8px' }} className="pulse-alert" />
            <div style={{ height: '12px', width: '120px', background: 'var(--card-border)', borderRadius: '4px' }} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="stats-grid">
      {/* Total Events */}
      <div className="stat-card">
        <div className="stat-label">
          <span>Processed Events</span>
          <Eye size={18} color="var(--accent-teal)" />
        </div>
        <div className="stat-value">{totalEvents}</div>
        <div className="stat-sub">↑ 100% temporal continuity logged</div>
      </div>

      {/* Active Alerts */}
      <div className={`stat-card ${activeAlerts > 0 ? 'pulse-alert' : ''}`} style={{
        borderColor: activeAlerts > 0 ? 'rgba(239, 68, 68, 0.4)' : 'var(--card-border)'
      }}>
        <div className="stat-label">
          <span>Unresolved Anomalies</span>
          <AlertTriangle size={18} color={activeAlerts > 0 ? 'var(--anomaly-red)' : 'var(--accent-teal)'} />
        </div>
        <div className="stat-value" style={{ color: activeAlerts > 0 ? 'var(--anomaly-red)' : 'inherit' }}>
          {activeAlerts}
        </div>
        <div className="stat-sub" style={{ color: activeAlerts > 0 ? 'var(--anomaly-red)' : 'var(--accent-teal)' }}>
          {activeAlerts > 0 ? 'Requires guard review' : 'All clear across zones'}
        </div>
      </div>

      {/* Monitored Cameras */}
      <div className="stat-card">
        <div className="stat-label">
          <span>Active CCTV Feeds</span>
          <Video size={18} color="#60a5fa" />
        </div>
        <div className="stat-value">{activeCameras}</div>
        <div className="stat-sub" style={{ color: '#60a5fa' }}>RTSP live stream ready</div>
      </div>

      {/* Highest Severity */}
      <div className="stat-card">
        <div className="stat-label">
          <span>Peak Threat Score</span>
          <ShieldCheck size={18} color={highestSeverity >= 8 ? 'var(--anomaly-red)' : 'var(--accent-teal)'} />
        </div>
        <div className="stat-value" style={{ color: highestSeverity >= 8 ? 'var(--anomaly-red)' : 'inherit' }}>
          {highestSeverity} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 10</span>
        </div>
        <div className="stat-sub">
          {highestSeverity >= 8 ? 'Perimeter trespass flag' : 'Nominal activity levels'}
        </div>
      </div>
    </div>
  );
};
