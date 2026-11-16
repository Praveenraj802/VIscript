import React, { useState } from 'react';
import { Video, Plus, X, AlertCircle, Radio, Info, Smartphone, HelpCircle } from 'lucide-react';
import { apiClient, CameraData } from '../api/client';

interface AddCameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCameraAdded: (newCamera: CameraData) => void;
}

export const AddCameraModal: React.FC<AddCameraModalProps> = ({
  isOpen,
  onClose,
  onCameraAdded,
}) => {
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [streamUrl, setStreamUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPhoneGuide, setShowPhoneGuide] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please provide a name for the camera.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const createdCam = await apiClient.addCamera({
        name: name.trim(),
        location: location.trim() || 'Main Zone',
        stream_url: streamUrl.trim() || undefined,
      });

      onCameraAdded(createdCam);
      // Reset form & close
      setName('');
      setLocation('');
      setStreamUrl('');
      onClose();
    } catch (err: any) {
      console.error('Failed to add camera:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to register camera.';
      setError(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickPreset = (type: 'webcam' | 'rtsp_sample' | 'mobile') => {
    if (type === 'webcam') {
      setName('Workstation Camera (Index 0 or 1)');
      setLocation('Command Center');
      setStreamUrl('0');
      setShowPhoneGuide(false);
    } else if (type === 'mobile') {
      setName('Mobile Phone Camera');
      setLocation('Mobile Patrol / Room Feed');
      setStreamUrl('http://192.168.1.50:8080/video');
      setShowPhoneGuide(true);
    } else {
      setName('Main Gate Surveillance Cam');
      setLocation('Gate 1 Perimeter');
      setStreamUrl('rtsp://admin:admin123@192.168.1.100:554/live/ch0');
      setShowPhoneGuide(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        backgroundColor: 'rgba(5, 11, 20, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose();
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '540px',
          maxHeight: '90vh',
          overflowY: 'auto',
          background: 'linear-gradient(160deg, #182844 0%, #0e1726 100%)',
          border: '1px solid #2e4a78',
          borderRadius: '16px',
          boxShadow: '0 20px 50px rgba(0,0,0,0.6), 0 0 30px rgba(15, 163, 127, 0.15)',
          padding: '1.75rem',
          position: 'relative',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'rgba(15, 163, 127, 0.15)',
                border: '1px solid rgba(15, 163, 127, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-teal)',
              }}
            >
              <Video size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff', margin: 0 }}>
                Register Surveillance Camera
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
                Connect an IP, Mobile Phone, RTSP, or PC webcam feed
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            disabled={isSubmitting}
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '8px',
              padding: '0.65rem 0.9rem',
              color: '#fca5a5',
              fontSize: '0.82rem',
              marginBottom: '1.25rem',
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Camera Identifier Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Mobile Phone Cam, Gate 01 - Main Entry"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.9rem',
                borderRadius: '8px',
                background: 'rgba(10, 18, 32, 0.7)',
                border: '1px solid var(--card-border)',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Physical Location / Zone
            </label>
            <input
              type="text"
              placeholder="e.g. Desk Room, Living Room, Entrance"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.9rem',
                borderRadius: '8px',
                background: 'rgba(10, 18, 32, 0.7)',
                border: '1px solid var(--card-border)',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                Live Stream URL or Device Index
              </label>
              <span style={{ fontSize: '0.72rem', color: 'var(--accent-teal)' }}>
                Phone Wi-Fi URL / RTSP / Index
              </span>
            </div>
            <input
              type="text"
              placeholder="e.g. http://192.168.1.50:8080/video or 1 for DroidCam USB"
              value={streamUrl}
              onChange={(e) => setStreamUrl(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.9rem',
                borderRadius: '8px',
                background: 'rgba(10, 18, 32, 0.7)',
                border: '1px solid var(--card-border)',
                color: '#fff',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />

            {/* Quick Presets */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Quick Presets:</span>
              
              <button
                type="button"
                onClick={() => handleQuickPreset('mobile')}
                style={{
                  background: 'rgba(15, 163, 127, 0.18)',
                  border: '1px solid rgba(15, 163, 127, 0.45)',
                  color: 'var(--accent-teal)',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <Smartphone size={12} />
                Mobile Phone (Wi-Fi)
              </button>

              <button
                type="button"
                onClick={() => handleQuickPreset('webcam')}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: 'var(--text-secondary)',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <Radio size={11} />
                USB / PC Cam (0 or 1)
              </button>

              <button
                type="button"
                onClick={() => handleQuickPreset('rtsp_sample')}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  color: 'var(--text-secondary)',
                  padding: '3px 8px',
                  borderRadius: '6px',
                  fontSize: '0.72rem',
                  cursor: 'pointer',
                }}
              >
                RTSP IP Camera
              </button>
            </div>
          </div>

          {/* Mobile Camera Setup Guide Box */}
          <div
            style={{
              background: 'rgba(15, 163, 127, 0.08)',
              border: '1px solid rgba(15, 163, 127, 0.25)',
              borderRadius: '10px',
              padding: '0.85rem',
              marginBottom: '1rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
              onClick={() => setShowPhoneGuide(!showPhoneGuide)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-teal)' }}>
                <Smartphone size={16} />
                <span>How to use your Mobile Phone as a Camera:</span>
              </div>
              <span style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', textDecoration: 'underline' }}>
                {showPhoneGuide ? 'Hide details' : 'Show 3-step setup'}
              </span>
            </div>

            {showPhoneGuide && (
              <div style={{ marginTop: '0.65rem', fontSize: '0.76rem', color: '#cbd5e1', lineHeight: 1.5, borderTop: '1px solid rgba(15, 163, 127, 0.15)', paddingTop: '0.65rem' }}>
                <div style={{ marginBottom: '4px' }}>
                  <strong>Option A (Wi-Fi Wireless - Recommended):</strong>
                </div>
                <ul style={{ paddingLeft: '1.2rem', marginBottom: '8px' }}>
                  <li><strong>Android:</strong> Install free app <em>"IP Webcam"</em> (by Pavel Khlebovich) from Google Play. Tap <em>Start server</em> at the bottom.</li>
                  <li><strong>iPhone:</strong> Install free app <em>"IP Camera Lite"</em> from App Store. Turn camera on.</li>
                  <li>Make sure your phone and laptop are on the <strong>same Wi-Fi network</strong>.</li>
                  <li>Enter the URL shown on your phone screen (e.g. <code>http://192.168.1.XX:8080/video</code>) above.</li>
                </ul>
                <div style={{ marginBottom: '4px' }}>
                  <strong>Option B (USB Cable via DroidCam / Iriun):</strong>
                </div>
                <div style={{ paddingLeft: '0.5rem' }}>
                  Install <em>DroidCam</em> or <em>Iriun Webcam</em> on PC & Phone. Plug USB cable in, then enter device index <code>1</code> or <code>2</code> in the URL field above!
                </div>
              </div>
            )}
          </div>

          {/* Architecture note */}
          <div
            style={{
              background: 'rgba(14, 23, 38, 0.6)',
              border: '1px solid rgba(40, 62, 101, 0.5)',
              borderRadius: '8px',
              padding: '0.75rem',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
            }}
          >
            <Info size={15} color="var(--accent-teal)" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              <strong style={{ color: '#fff' }}>Continuous AI Transcription:</strong> As soon as your phone camera connects, VisualIQ samples live frames every 12s, flags anomalies with Vision AI, and synthesizes continuous narrative security transcripts.
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
              style={{ padding: '0.55rem 1rem', fontSize: '0.85rem' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || !name.trim()}
              style={{ padding: '0.55rem 1.25rem', fontSize: '0.85rem' }}
            >
              <Plus size={16} />
              <span>{isSubmitting ? 'Registering...' : 'Add Camera & Connect'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
