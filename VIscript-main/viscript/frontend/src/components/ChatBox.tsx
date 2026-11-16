import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Clock, Sparkles, Cpu } from 'lucide-react';
import { apiClient, QueryResponseData } from '../api/client';

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  sources?: string[];
  provider?: string;
  latency_ms?: number;
  time: string;
}

interface ChatBoxProps {
  selectedCameraId?: string;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ selectedCameraId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init_1',
      sender: 'ai',
      text: 'Hello! I am VisualIQ Intelligence. Ask me anything about today\'s CCTV surveillance footage, visitors, vehicle entries, or flagged anomalies.',
      time: 'Just now',
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const starterQuestions = [
    'Summarize recent surveillance events for this camera',
    'Were there any flagged anomalies or high severity scores?',
    'How many people or vehicles were detected in the footage?',
    'What activities were recorded during this shift?',
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || inputQuery).trim();
    if (!textToSend || isLoading) return;

    const userMsg: Message = {
      id: `user_${Date.now()}`,
      sender: 'user',
      text: textToSend,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res: QueryResponseData = await apiClient.askQuery(textToSend, selectedCameraId);
      const aiMsg: Message = {
        id: `ai_${Date.now()}`,
        sender: 'ai',
        text: res.answer,
        sources: res.sources,
        provider: res.provider,
        latency_ms: res.latency_ms,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg: Message = {
        id: `ai_err_${Date.now()}`,
        sender: 'ai',
        text: 'Sorry, I encountered an issue retrieving the transcript intelligence. Please verify your connection.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Messages Scroll Area */}
      <div className="chat-messages">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`chat-bubble ${m.sender === 'user' ? 'chat-user' : 'chat-ai'}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              {m.sender === 'user' ? (
                <>
                  <User size={14} />
                  <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>Security Officer</span>
                </>
              ) : (
                <>
                  <Bot size={14} color="var(--accent-teal)" />
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-teal)' }}>VisualIQ Agent</span>
                </>
              )}
              <span style={{ fontSize: '0.7rem', color: m.sender === 'user' ? 'rgba(255,255,255,0.7)' : 'var(--text-muted)', marginLeft: 'auto' }}>
                {m.time}
              </span>
            </div>

            <div style={{ fontSize: '0.92rem', lineHeight: 1.55 }}>
              {m.text}
            </div>

            {/* Citations & AI Provider Tag */}
            {m.sources && m.sources.length > 0 && (
              <div className="chat-sources">
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Clock size={12} color="var(--accent-teal)" />
                  <span style={{ fontWeight: 600 }}>Sources:</span>
                </div>
                {m.sources.map((src, i) => (
                  <span
                    key={i}
                    style={{
                      background: 'rgba(15, 163, 127, 0.15)',
                      color: 'var(--accent-teal)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.7rem',
                    }}
                  >
                    {src}
                  </span>
                ))}

                {m.provider && (
                  <span style={{
                    marginLeft: 'auto',
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <Cpu size={11} /> {m.provider} {m.latency_ms ? `(${m.latency_ms}ms)` : ''}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="chat-bubble chat-ai" style={{ width: 'fit-content' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={16} color="var(--accent-teal)" className="pulse-alert" />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                RAG Engine searching ChromaDB & synthesizing answer with Gemini 2.5 Flash...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Starter Prompts */}
      <div style={{ padding: '0.75rem 1.5rem', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--card-border)', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Sparkles size={12} /> Suggested:
        </span>
        {starterQuestions.map((sq, i) => (
          <button
            key={i}
            onClick={() => handleSend(sq)}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--card-border)',
              borderRadius: '16px',
              padding: '4px 10px',
              color: 'var(--text-secondary)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.borderColor = 'var(--accent-teal)')}
            onMouseOut={(e) => (e.currentTarget.style.borderColor = 'var(--card-border)')}
          >
            {sq}
          </button>
        ))}
      </div>

      {/* Input Field */}
      <div className="chat-input-bar">
        <input
          type="text"
          className="chat-input"
          placeholder="Ask anything about CCTV events (e.g., 'Were there any strangers after 10 PM?')..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={isLoading}
        />
        <button
          className="btn btn-primary"
          onClick={() => handleSend()}
          disabled={isLoading || !inputQuery.trim()}
        >
          <Send size={16} />
          <span>Ask</span>
        </button>
      </div>
    </div>
  );
};
