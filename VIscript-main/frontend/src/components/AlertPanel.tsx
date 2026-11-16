import React from 'react';
import { AlertCircle, CheckCircle, ShieldAlert, Clock } from 'lucide-react';

export interface AlertItem {
  id: string;
  camera_id: string;
  camera_name?: string;
  time?: string;
  activity?: string;
  anomaly_score: number;
  anomaly_reason?: string;
  resolved: boolean;
}

interface AlertPanelProps {
  alerts: AlertItem[];
  onResolve: (alertId: string) => void;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, onResolve }) => {
  const unresolvedAlerts = alerts.filter((a) => !a.resolved);

  return (
    <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--anomaly-red)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldAlert size={20} color="var(--anomaly-red)" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Security Anomaly Alerts (Score &gt; 6)</h2>
        </div>
        <span style={{
          background: unresolvedAlerts.length > 0 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
          color: unresolvedAlerts.length > 0 ? '#f87171' : '#34d399',
          padding: '3px 10px',
          borderRadius: '12px',
          fontSize: '0.8rem',
          fontWeight: 600
        }}>
          {unresolvedAlerts.length} Unresolved
        </span>
      </div>

      {unresolvedAlerts.length === 0 ? (
        <div style={{
          padding: '1.5rem',
          textAlign: 'center',
          color: 'var(--text-secondary)',
          background: 'rgba(0,0,0,0.15)',
          borderRadius: '8px'
        }}>
          <CheckCircle size={28} color="var(--accent-teal)" style={{ marginBottom: '8px' }} />
          <div>No active critical anomalies. Perimeter and gates are secure.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {unresolvedAlerts.map((alert) => (
            <div
              key={alert.id}
              style={{
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                padding: '0.85rem 1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px',
                flexWrap: 'wrap'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', flex: 1, minWidth: '280px' }}>
                <AlertCircle size={20} color="var(--anomaly-red)" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className="badge-anomaly-red">
                      CRITICAL {alert.anomaly_score}/10
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {alert.camera_name || alert.camera_id}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <Clock size={12} /> {alert.time}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#e2e8f0', marginBottom: '3px' }}>
                    {alert.activity}
                  </div>
                  {alert.anomaly_reason && (
                    <div style={{ fontSize: '0.75rem', color: '#fca5a5', fontStyle: 'italic' }}>
                      Reason: {alert.anomaly_reason}
                    </div>
                  )}
                </div>
              </div>

              <button
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
                onClick={() => onResolve(alert.id)}
              >
                <CheckCircle size={14} color="var(--accent-teal)" />
                <span>Mark Resolved</span>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
