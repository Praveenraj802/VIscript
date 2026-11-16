import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, CheckCircle2, AlertTriangle, FileVideo, Cpu, ArrowRight, Loader2, RotateCcw } from 'lucide-react';
import { apiClient, JobStatusData } from '../api/client';

interface UploadPageProps {
  onUploadSuccess: () => void;
  cameras: Array<{ id: string; name: string }>;
  defaultCameraId: string;
}

const MAX_FILE_SIZE_MB = 500;

export const UploadPage: React.FC<UploadPageProps> = ({
  onUploadSuccess,
  cameras,
  defaultCameraId,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCamera, setSelectedCamera] = useState(defaultCameraId || (cameras[0]?.id ?? ''));
  const [isUploading, setIsUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [jobStatus, setJobStatus] = useState<JobStatusData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync selected camera if cameras list loads or changes
  useEffect(() => {
    if (cameras.length > 0 && (!selectedCamera || !cameras.some((c) => c.id === selectedCamera))) {
      setSelectedCamera(cameras[0].id);
    }
  }, [cameras]);

  // Poll job status every 1 second while active; terminate on done OR failed.
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    const activeStatuses = new Set(['pending', 'extracting', 'analyzing', 'synthesizing', 'storing']);

    if (jobStatus && activeStatuses.has(jobStatus.status)) {
      interval = setInterval(async () => {
        try {
          const updated = await apiClient.getJobStatus(jobStatus.job_id);
          setJobStatus((prev) => (prev && prev.job_id === updated.job_id ? updated : prev));
          if (updated.status === 'done' || updated.status === 'failed') {
            clearInterval(interval!);
          }
        } catch (err) {
          console.warn('Job status poll warning:', err);
        }
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobStatus]);

  const validateAndSetFile = (file: File) => {
    const sizeInMB = file.size / (1024 * 1024);
    if (sizeInMB > MAX_FILE_SIZE_MB) {
      setErrorMessage(`File is too large (${sizeInMB.toFixed(1)}MB). The maximum allowed upload size is ${MAX_FILE_SIZE_MB}MB.`);
      setSelectedFile(null);
      return false;
    }
    setSelectedFile(file);
    setErrorMessage(null);
    setJobStatus(null);
    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleStartIngestion = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadPercent(0);
    setErrorMessage(null);

    try {
      const camIdToUse = (selectedCamera || 'camera_01').trim();
      const initialJob = await apiClient.uploadVideo(
        selectedFile,
        camIdToUse,
        (percent) => setUploadPercent(percent)
      );
      setJobStatus(initialJob);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to upload surveillance footage.';
      setErrorMessage(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setJobStatus(null);
    setErrorMessage(null);
    setUploadPercent(0);
  };

  const getStageStatus = (stage: string) => {
    if (!jobStatus) return 'idle';
    const stages = ['pending', 'extracting', 'analyzing', 'synthesizing', 'storing', 'done'];
    const currentIdx = stages.indexOf(jobStatus.status);
    const stageIdx = stages.indexOf(stage);

    if (jobStatus.status === 'failed') return 'failed';
    if (currentIdx > stageIdx || jobStatus.status === 'done') return 'complete';
    if (currentIdx === stageIdx) return 'active';
    return 'pending';
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff' }}>
          Ingest Surveillance Footage
        </h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Upload MP4/AVI CCTV video. The VisualIQ pipeline extracts frames, runs Gemini 2.5 Flash with temporal context, and builds searchable transcripts.
        </p>
      </div>

      <div className="card" style={{ padding: '2rem' }}>
        {/* Camera Target Selector */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
            Assign to Surveillance Camera:
          </label>
          {cameras.length > 0 ? (
            <select
              className="camera-select"
              style={{ width: '100%', padding: '0.75rem 1rem' }}
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
              disabled={isUploading || (jobStatus !== null && jobStatus.status !== 'done' && jobStatus.status !== 'failed')}
            >
              {cameras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.id})
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              className="chat-input"
              style={{ width: '100%', padding: '0.75rem 1rem' }}
              placeholder="e.g. Main Gate Camera (cam_01)"
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
              disabled={isUploading || (jobStatus !== null && jobStatus.status !== 'done' && jobStatus.status !== 'failed')}
            />
          )}
        </div>

        {/* Drag and Drop Zone */}
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed',
            borderColor: selectedFile ? 'var(--accent-teal)' : 'var(--card-border)',
            borderRadius: '12px',
            padding: '3rem 2rem',
            textAlign: 'center',
            cursor: 'pointer',
            background: selectedFile ? 'rgba(15, 163, 127, 0.05)' : 'rgba(0, 0, 0, 0.15)',
            transition: 'all 0.2s ease',
            marginBottom: '1.5rem'
          }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="video/mp4,video/avi,video/mkv,video/quicktime,video/webm"
            style={{ display: 'none' }}
          />

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(15, 163, 127, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-teal)'
            }}>
              {selectedFile ? <FileVideo size={28} /> : <UploadCloud size={28} />}
            </div>

            <div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#fff' }}>
                {selectedFile ? selectedFile.name : 'Select or drop surveillance video file here'}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {selectedFile
                  ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for edge ingestion`
                  : `Supports MP4, AVI, MKV up to ${MAX_FILE_SIZE_MB}MB (Uniform sample @ 0.2 FPS)`}
              </div>
            </div>
          </div>
        </div>

        {/* Upload Progress Bar */}
        {isUploading && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Uploading stream to backend buffer...</span>
              <span style={{ color: 'var(--accent-teal)', fontWeight: 600 }}>{uploadPercent}%</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'var(--card-border)', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${uploadPercent}%`,
                  height: '100%',
                  background: 'var(--accent-teal)',
                  transition: 'width 0.2s ease'
                }}
              />
            </div>
          </div>
        )}

        {/* Action Button */}
        {!jobStatus && (
          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.9rem', fontSize: '1rem' }}
            disabled={!selectedFile || isUploading}
            onClick={handleStartIngestion}
          >
            <Cpu size={18} />
            <span>Start AI Vision Pipeline</span>
          </button>
        )}

        {/* Pipeline Stage Tracker */}
        {jobStatus && (
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '10px', border: '1px solid var(--card-border)', marginTop: '1rem' }}>
            <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span>Pipeline Status: <span style={{
                color: jobStatus.status === 'failed' ? '#ef4444' : 'var(--accent-teal)',
                textTransform: 'uppercase'
              }}>{jobStatus.status}</span></span>
              {jobStatus.status !== 'done' && jobStatus.status !== 'failed' && (
                <Loader2 size={18} color="var(--accent-teal)" className="pulse-alert" />
              )}
            </div>

            {/* Stepper items */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { key: 'extracting', label: '1. Frame & Motion-Burst Extraction', detail: 'OpenCV uniform sampling + pixel diff analysis' },
                { key: 'analyzing', label: '2. Vision AI Frame Analysis', detail: 'Gemini 2.5 Flash with temporal context & loitering detection' },
                { key: 'synthesizing', label: '3. Transcript Synthesis', detail: 'Structured narrative log & safety assessment' },
                { key: 'storing', label: '4. Vector Indexing & DB Persistence', detail: 'ChromaDB embeddings + Supabase events table' },
              ].map((step) => {
                const st = getStageStatus(step.key);
                return (
                  <div key={step.key} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    {st === 'complete' && <CheckCircle2 size={18} color="var(--accent-teal)" style={{ marginTop: '2px' }} />}
                    {st === 'active' && <Loader2 size={18} color="var(--accent-teal)" style={{ marginTop: '2px', animation: 'spin 1s linear infinite' }} />}
                    {st === 'failed' && <AlertTriangle size={18} color="#ef4444" style={{ marginTop: '2px' }} />}
                    {st === 'pending' && <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: '2px solid var(--card-border)', marginTop: '2px' }} />}
                    
                    <div>
                      <div style={{
                        fontSize: '0.85rem',
                        fontWeight: st === 'active' ? 700 : 500,
                        color: st === 'active' ? 'var(--text-primary)' : st === 'complete' ? 'var(--accent-teal)' : st === 'failed' ? '#f87171' : 'var(--text-muted)'
                      }}>
                        {step.label}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {step.detail}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {jobStatus.message && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '6px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                ℹ️ {jobStatus.message}
              </div>
            )}

            {jobStatus.status === 'failed' && (
              <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
                <div style={{ color: '#ef4444', fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.75rem' }}>
                  Pipeline failed: {jobStatus.error || jobStatus.message || 'Unknown processing error'}
                </div>
                <button
                  className="btn btn-secondary"
                  onClick={handleReset}
                  style={{ padding: '0.6rem 1.25rem' }}
                >
                  <RotateCcw size={14} />
                  <span>Try Again / Choose Another File</span>
                </button>
              </div>
            )}

            {jobStatus.status === 'done' && (
              <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
                <div style={{ color: 'var(--accent-teal)', fontWeight: 700, fontSize: '1rem', marginBottom: '1rem' }}>
                  ✓ Video processed successfully! Transcripts and alerts generated.
                </div>
                <button
                  className="btn btn-primary"
                  onClick={onUploadSuccess}
                  style={{ padding: '0.8rem 1.5rem' }}
                >
                  <span>View in Dashboard &amp; Timeline</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>
        )}

        {errorMessage && (
          <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>
    </div>
  );
};
