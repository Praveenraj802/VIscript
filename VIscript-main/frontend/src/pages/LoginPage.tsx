import React, { useState } from 'react';
import { Shield, Lock, Mail, User, ArrowRight, AlertCircle, UserPlus, LogIn } from 'lucide-react';
import { apiClient } from '../api/client';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Surveillance Operator');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      if (isSignUp) {
        await apiClient.register(email, password, name, role);
      } else {
        await apiClient.login(email, password);
      }
      onLoginSuccess();
    } catch (err: any) {
      console.error('Authentication failure:', err);
      if (!err.response) {
        setError('Cannot connect to VisualIQ backend (http://localhost:8000). Please ensure the backend server is running.');
      } else {
        const detail = err.response?.data?.detail || 'Authentication failed. Please verify your details.';
        setError(detail);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      background: 'radial-gradient(circle at 50% 30%, #152542 0%, #0e1726 100%)'
    }}>
      <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2.5rem' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #0fa37f, #152238)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid #283e65',
            margin: '0 auto 1rem'
          }}>
            <Shield size={28} color="#fff" />
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>
            Visual<span style={{ color: 'var(--accent-teal)' }}>IQ</span>
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Enterprise AI Surveillance Transcript Platform
          </p>
        </div>

        {/* Sign In / Sign Up Mode Switcher */}
        <div style={{
          display: 'flex',
          background: 'rgba(0, 0, 0, 0.25)',
          padding: '4px',
          borderRadius: '10px',
          marginBottom: '1.5rem',
          border: '1px solid var(--card-border)'
        }}>
          <button
            type="button"
            onClick={() => { setIsSignUp(false); setError(null); }}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: '0.55rem',
              borderRadius: '8px',
              border: 'none',
              background: !isSignUp ? 'var(--accent-teal)' : 'transparent',
              color: !isSignUp ? '#fff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <LogIn size={15} />
            <span>Sign In</span>
          </button>
          <button
            type="button"
            onClick={() => { setIsSignUp(true); setError(null); }}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: '0.55rem',
              borderRadius: '8px',
              border: 'none',
              background: isSignUp ? 'var(--accent-teal)' : 'transparent',
              color: isSignUp ? '#fff' : 'var(--text-secondary)',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <UserPlus size={15} />
            <span>Sign Up</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
            color: '#fca5a5',
            fontSize: '0.82rem'
          }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isSignUp && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Full Name / Officer Name
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required={isSignUp}
                  className="chat-input"
                  style={{ width: '100%', paddingLeft: '2.5rem' }}
                  placeholder="e.g. Sai Kumar"
                />
                <User size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              </div>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Security Officer Email
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="chat-input"
                style={{ width: '100%', paddingLeft: '2.5rem' }}
                placeholder="officer@facility.in"
              />
              <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            </div>
          </div>

          {isSignUp && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Operational Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="camera-select"
                style={{ width: '100%', padding: '0.75rem 1rem' }}
              >
                <option value="Chief Security Officer">Chief Security Officer</option>
                <option value="Surveillance Operator">Surveillance Operator</option>
                <option value="Society Admin">Society Management Admin</option>
                <option value="Duty Officer">Duty Patrol Officer</option>
              </select>
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Account Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="chat-input"
                style={{ width: '100%', paddingLeft: '2.5rem' }}
                placeholder="••••••••"
              />
              <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.85rem', marginTop: '0.5rem', fontSize: '0.95rem' }}
            disabled={isLoading}
          >
            <span>
              {isLoading
                ? (isSignUp ? 'Creating Security Account...' : 'Verifying with Security Hub...')
                : (isSignUp ? 'Register & Sign In' : 'Sign In with JWT')}
            </span>
            <ArrowRight size={16} />
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.25rem' }}>
          <button
            type="button"
            onClick={() => { setIsSignUp(!isSignUp); setError(null); }}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--accent-teal)',
              fontSize: '0.82rem',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
          </button>
        </div>

        <div style={{ textAlign: 'center', marginTop: '1.25rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Compliant with India DPDP Act 2023 • JWT HMAC-SHA256 Auth Active
        </div>
      </div>
    </div>
  );
};

