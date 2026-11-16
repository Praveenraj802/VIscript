import React from 'react';
import { Clock, Users, MapPin, Tag, FileText } from 'lucide-react';

export interface TimelineEvent {
  id?: string;
  time: string;
  camera_id: string;
  camera_name?: string;
  people_count: number;
  activity: string;
  objects: string[];
  anomaly_score: number;
  anomaly_reason?: string;
  location_zone: string;
}

export interface TranscriptItem {
  id: string;
  camera_id: string;
  camera_name?: string;
  period_start: string;
  period_end: string;
  narrative: string;
  event_count: number;
  created_at?: string;
}

interface TimelineProps {
  events: TimelineEvent[];
  transcripts: TranscriptItem[];
  activeView: 'events' | 'transcripts';
  onToggleView: (view: 'events' | 'transcripts') => void;
}

export const Timeline: React.FC<TimelineProps> = ({
  events,
  transcripts,
  activeView,
  onToggleView,
}) => {
  const getBadgeClass = (score: number) => {
    if (score >= 7) return 'badge-anomaly-red';
    if (score >= 4) return 'badge-anomaly-amber';
    return 'badge-anomaly-green';
  };

  return (
    <div className="card">
      {/* Header & Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Surveillance Activity Feed
          </h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Real-time chronological events synthesized by Gemini 2.5 Flash
          </span>
        </div>

        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.2)', padding: '3px', borderRadius: '8px', border: '1px solid var(--card-border)' }}>
          <button
            className={`btn ${activeView === 'events' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem', borderRadius: '6px' }}
            onClick={() => onToggleView('events')}
          >
            Detailed Frame Events ({events.length})
          </button>
          <button
            className={`btn ${activeView === 'transcripts' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem', borderRadius: '6px' }}
            onClick={() => onToggleView('transcripts')}
          >
            Narrative Shifts ({transcripts.length})
          </button>
        </div>
      </div>

      {/* Narrative Transcripts View */}
      {activeView === 'transcripts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {transcripts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No transcripts generated for this camera yet. Ingest an MP4 video to generate new transcripts.
            </div>
          ) : (
            transcripts.map((t) => (
              <div
                key={t.id}
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--card-border)',
                  borderRadius: '10px',
                  padding: '1.25rem',
                  borderLeft: '4px solid var(--accent-teal)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={16} color="var(--accent-teal)" />
                    <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                      {t.camera_name || t.camera_id}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-teal)', fontFamily: 'var(--font-mono)' }}>
                    {t.period_start} — {t.period_end}
                  </span>
                </div>
                <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: 1.6, marginBottom: '10px' }}>
                  {t.narrative}
                </p>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Aggregated from {t.event_count} visual frames • Indexed in ChromaDB for Semantic Search
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Frame Events Timeline View */}
      {activeView === 'events' && (
        <div className="timeline">
          {events.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No surveillance events recorded yet. Ingest video footage in "Ingest Footage" to analyze events.
            </div>
          ) : (
            events.map((evt, idx) => (
              <div key={evt.id || idx} className="timeline-item">
                <div className={`timeline-dot ${evt.anomaly_score >= 7 ? 'alert' : 'normal'}`} />
                
                <div
                  style={{
                    background: evt.anomaly_score >= 7 ? 'rgba(239, 68, 68, 0.06)' : 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid',
                    borderColor: evt.anomaly_score >= 7 ? 'rgba(239, 68, 68, 0.3)' : 'var(--card-border)',
                    borderRadius: '8px',
                    padding: '0.9rem 1.1rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        background: 'rgba(0,0,0,0.3)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        color: '#38bdf8'
                      }}>
                        {evt.time}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                        {evt.camera_name || evt.camera_id}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <MapPin size={12} /> {evt.location_zone}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={getBadgeClass(evt.anomaly_score)}>
                        Score {evt.anomaly_score}/10
                      </span>
                      {evt.people_count > 0 && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          <Users size={12} /> {evt.people_count}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ fontSize: '0.9rem', color: '#e2e8f0', lineHeight: 1.5, marginBottom: '8px' }}>
                    {evt.activity}
                  </div>

                  {evt.anomaly_reason && (
                    <div style={{
                      fontSize: '0.75rem',
                      color: '#f87171',
                      background: 'rgba(239, 68, 68, 0.1)',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      marginBottom: '8px'
                    }}>
                      ⚠️ {evt.anomaly_reason}
                    </div>
                  )}

                  {/* Detected objects */}
                  {evt.objects && evt.objects.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Objects:</span>
                      {evt.objects.map((obj, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '0.7rem',
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'var(--text-secondary)',
                            padding: '1px 6px',
                            borderRadius: '4px',
                            border: '1px solid rgba(255, 255, 255, 0.08)'
                          }}
                        >
                          {obj}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
