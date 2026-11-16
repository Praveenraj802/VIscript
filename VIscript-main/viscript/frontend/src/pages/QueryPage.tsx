import React from 'react';
import { ChatBox } from '../components/ChatBox';
import { Sparkles, HelpCircle } from 'lucide-react';

interface QueryPageProps {
  selectedCameraId?: string;
}

export const QueryPage: React.FC<QueryPageProps> = ({ selectedCameraId }) => {
  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>Intelligence Q&amp;A Agent</span>
            <span className="brand-badge">RAG Powered</span>
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Ask natural language questions against the surveillance transcripts. Powered by Gemini 2.5 Flash with Groq Llama 4 fallback.
          </p>
        </div>

        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid var(--card-border)',
          borderRadius: '8px',
          padding: '6px 12px',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <Sparkles size={14} color="var(--accent-teal)" />
          <span>Active Scope: {selectedCameraId || 'All Cameras'}</span>
        </div>
      </div>

      <ChatBox selectedCameraId={selectedCameraId} />
    </div>
  );
};
