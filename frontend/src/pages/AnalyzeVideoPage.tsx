import React, { useState, useEffect, useRef } from 'react';
import { api, getAssetUrl } from '../api/client';
import { VideoJob, Violation } from '../types';
import {
  UploadCloud, Video, AlertCircle, CheckCircle2,
  Clock, Cpu, ShieldAlert, Eye, RefreshCw, FileVideo,
  PlayCircle, ArrowRight, Download, Sparkles, FolderOpen
} from 'lucide-react';

export const AnalyzeVideoPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const [jobStatus, setJobStatus] = useState<VideoJob | null>(null);
  const [recentJobs, setRecentJobs] = useState<VideoJob[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [detectedViolations, setDetectedViolations] = useState<Violation[]>([]);
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);

  const [workerInfo, setWorkerInfo] = useState<{ mode?: string; worker_online?: boolean; message?: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchRecentJobs = async () => {
    try {
      const res = await api.get('/api/jobs');
      setRecentJobs(res.data);
    } catch (err) {
      console.warn("Could not fetch recent jobs", err);
    }
  };

  const fetchWorkerStatus = async () => {
    try {
      const res = await api.get('/api/worker/status');
      setWorkerInfo(res.data);
    } catch {
      // optional
    }
  };

  useEffect(() => {
    fetchRecentJobs();
    fetchWorkerStatus();
    const wInterval = setInterval(fetchWorkerStatus, 10000);
    return () => clearInterval(wInterval);
  }, []);

  // Polling active job
  useEffect(() => {
    if (!activeJobId) return;

    const pollJob = async () => {
      try {
        const res = await api.get(`/api/jobs/${activeJobId}`);
        const data: VideoJob = res.data;
        setJobStatus(data);

        if (data.status === 'completed' || data.status === 'failed') {
          fetchRecentJobs();
          if (data.status === 'completed') {
            try {
              const vRes = await api.get(`/api/violations?video_job_id=${activeJobId}&page_size=50`);
              setDetectedViolations(vRes.data.items || []);
            } catch (vErr) {
              console.error("Error fetching violations for job", vErr);
            }
          }
        }
      } catch (err: any) {
        console.error("Error polling job", err);
      }
    };

    pollJob();
    const interval = setInterval(pollJob, 2000);
    return () => clearInterval(interval);
  }, [activeJobId]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      const ext = selected.name.split('.').pop()?.toLowerCase();
      if (!['mp4', 'avi', 'mov'].includes(ext || '')) {
        setErrorMsg("Invalid file format. Please upload an MP4, AVI, or MOV video.");
        setFile(null);
        return;
      }
      if (selected.size > 50 * 1024 * 1024) {
        setErrorMsg("File exceeds the maximum 50 MB limit. Please select a shorter clip.");
        setFile(null);
        return;
      }
      setErrorMsg(null);
      setFile(selected);
    }
  };

  // One-click fetch sample video and load into file input
  const loadSampleVideo = async (filename: string, label: string) => {
    setLoadingSample(filename);
    setErrorMsg(null);
    try {
      const response = await fetch(getAssetUrl(`/samples/${filename}`));
      if (!response.ok) throw new Error("Could not fetch sample video");
      const blob = await response.blob();
      const sampleFile = new File([blob], filename, { type: 'video/mp4' });
      setFile(sampleFile);
    } catch (err) {
      setErrorMsg(`Failed to load ${filename}. You can also browse to backend/samples/${filename} directly.`);
    } finally {
      setLoadingSample(null);
    }
  };

  const loadJobViolations = async (jobId: number) => {
    try {
      setActiveJobId(jobId);
      const vRes = await api.get(`/api/violations?video_job_id=${jobId}&page_size=50`);
      setDetectedViolations(vRes.data.items || []);
    } catch (err) {
      console.error("Failed to load job violations", err);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg("Please select or load a video file first.");
      return;
    }

    setErrorMsg(null);
    setUploading(true);
    setDetectedViolations([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/api/videos/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setActiveJobId(res.data.job_id);
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Failed to upload video for AI analysis.";
      setErrorMsg(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold font-['Outfit'] text-white">AI Traffic Video Ingestion & Analysis</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Upload road camera footage to automatically detect vehicles, speed, signal jumping, helmet violations, wrong-way driving, and extract license plates
          </p>
        </div>
        {workerInfo && (
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border shrink-0 ${
            workerInfo.worker_online
              ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/40'
              : 'bg-amber-950/60 text-amber-300 border-amber-800/40'
          }`}>
            <span className={`w-2 h-2 rounded-full ${workerInfo.worker_online ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            <span>{workerInfo.message}</span>
          </div>
        )}
      </div>

      {/* Preloaded Sample Videos Picker Banner */}
      <div className="glass-panel p-5 rounded-2xl border border-indigo-900/60 bg-gradient-to-r from-indigo-950/40 via-gray-950 to-gray-950">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Ready-to-Test Sample Clips</h2>
              <p className="text-xs text-gray-400">
                Stored in <code className="text-cyan-300 font-mono text-[11px]">backend/samples/</code> — click either clip below to auto-load, or drag & drop yourself:
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              type="button"
              onClick={() => loadSampleVideo('cctv_junction_720p.mp4', 'Overhead CCTV Intersection')}
              disabled={loadingSample !== null}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-md shadow-indigo-600/30 transition-all"
            >
              {loadingSample === 'cctv_junction_720p.mp4' ? (
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <FileVideo className="w-4 h-4 text-white" />
              )}
              <span>Load Real Overhead CCTV Intersection (Traffic Light POV &bull; 12s)</span>
            </button>

            <button
              type="button"
              onClick={() => loadSampleVideo('real_cctv_intersection.mp4', 'Multi-Lane Intersection')}
              disabled={loadingSample !== null}
              className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gray-900 hover:bg-gray-800 text-purple-300 border border-purple-800/60 shadow-sm transition-all"
            >
              {loadingSample === 'real_cctv_intersection.mp4' ? (
                <div className="w-3.5 h-3.5 border-2 border-purple-400/30 border-t-purple-400 rounded-full animate-spin"></div>
              ) : (
                <FileVideo className="w-4 h-4 text-purple-400" />
              )}
              <span>Load 1080p Overhead Intersection</span>
            </button>

            <button
              type="button"
              onClick={() => loadSampleVideo('cctv_traffic.mp4', 'Multi-Vehicle Stream')}
              disabled={loadingSample !== null}
              className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-gray-900 hover:bg-gray-800 text-cyan-300 border border-cyan-800/60 shadow-sm transition-all"
            >
              {loadingSample === 'cctv_traffic.mp4' ? (
                <div className="w-3.5 h-3.5 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin"></div>
              ) : (
                <FileVideo className="w-4 h-4 text-cyan-400" />
              )}
              <span>Load Highway Camera Feed</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Upload & Monitor Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Card */}
        <div className="glass-panel p-6 rounded-3xl border border-gray-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Video className="w-4 h-4 text-indigo-400" />
              </div>
              <h2 className="text-sm font-semibold text-white">Upload Surveillance Video</h2>
            </div>

            {errorMsg && (
              <div className="mb-4 p-3.5 rounded-xl bg-red-950/60 border border-red-800/60 flex items-start gap-2.5 text-xs text-red-300">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleUpload}>
              <div
                onClick={() => fileInputRef.current?.click()}
                className="cursor-pointer border-2 border-dashed border-gray-700 hover:border-indigo-500/70 bg-gray-950/50 hover:bg-gray-900/50 rounded-2xl p-8 text-center transition-all group"
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".mp4,.avi,.mov,video/*"
                  className="hidden"
                />
                <div className="w-12 h-12 rounded-2xl bg-indigo-950/60 border border-indigo-700/40 text-cyan-400 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <p className="text-xs sm:text-sm font-semibold text-white mb-1">
                  {file ? file.name : "Click or Drag & Drop Video File"}
                </p>
                <p className="text-[11px] text-gray-400">
                  {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB — Ready to analyze` : "Supported formats: MP4, AVI, MOV (Max 50 MB, 90s duration)"}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
                <span>Single-job queue concurrency lock</span>
                <span>ByteTrack + YOLOv8n</span>
              </div>

              <button
                type="submit"
                disabled={!file || uploading || jobStatus?.status === 'processing'}
                className="w-full mt-4 flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
              >
                {uploading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <>
                    <Cpu className="w-4 h-4" />
                    <span>Run AI Detection Engine</span>
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-800/70 text-[11px] text-gray-400 leading-relaxed">
            <span className="font-semibold text-gray-300">Detection Pipeline:</span> Processes every 3rd frame, extracts helmet regions of motorcyclists, confirms violations after 3 positive frames, and extracts plate OCR automatically.
          </div>
        </div>

        {/* Live Job Progress Monitor */}
        <div className="glass-panel p-6 rounded-3xl border border-gray-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                </div>
                <h2 className="text-sm font-semibold text-white">Live Engine Telemetry</h2>
              </div>
              {jobStatus && (
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  jobStatus.status === 'completed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/50' :
                  jobStatus.status === 'processing' ? 'bg-indigo-950 text-cyan-300 border border-cyan-700/50 animate-pulse' :
                  jobStatus.status === 'queued' ? 'bg-amber-950 text-amber-400 border border-amber-800/50' :
                  'bg-red-950 text-red-400 border border-red-800/50'
                }`}>
                  {jobStatus.status}
                </span>
              )}
            </div>

            {jobStatus ? (
              <div className="space-y-5">
                {/* File & Job Info */}
                <div className="p-3.5 rounded-xl bg-gray-950/70 border border-gray-800 text-xs">
                  <div className="flex justify-between text-gray-400 mb-1">
                    <span>Job ID: #{jobStatus.id}</span>
                    <span>Frames: {jobStatus.total_frames || 'Calculating...'}</span>
                  </div>
                  <p className="font-semibold text-white truncate">{jobStatus.filename}</p>
                </div>

                {/* Progress Bar */}
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-gray-400">Processing Progress</span>
                    <span className="font-mono font-bold text-cyan-400">{jobStatus.progress}%</span>
                  </div>
                  <div className="w-full h-3 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 transition-all duration-300"
                      style={{ width: `${jobStatus.progress}%` }}
                    ></div>
                  </div>
                </div>

                {/* Real-time counters */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800">
                    <span className="text-[11px] text-gray-400">Vehicles Tracked</span>
                    <p className="text-xl font-bold font-['Outfit'] text-white mt-0.5">{jobStatus.vehicles_detected}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800">
                    <span className="text-[11px] text-gray-400">Helmet Violations</span>
                    <p className="text-xl font-bold font-['Outfit'] text-red-400 mt-0.5">{jobStatus.violations_found}</p>
                  </div>
                </div>

                {jobStatus.error && (
                  <div className="p-3 rounded-xl bg-red-950/60 border border-red-800/60 text-xs text-red-300">
                    <strong>Error:</strong> {jobStatus.error}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center text-gray-500 text-xs">
                <PlayCircle className="w-10 h-10 mx-auto text-gray-600 mb-2 opacity-50" />
                <p>No video currently being analyzed.</p>
                <p className="text-[11px] text-gray-600 mt-1">Click one of the sample buttons above or upload your own video.</p>
              </div>
            )}
          </div>

          {/* Violations generated in this job */}
          {detectedViolations.length > 0 && (
            <div className="mt-5 pt-4 border-t border-gray-800">
              <h3 className="text-xs font-semibold text-white mb-2 flex items-center justify-between">
                <span>Violations Found in this Video ({detectedViolations.length})</span>
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {detectedViolations.map((v) => (
                  <div
                    key={v.id}
                    onClick={() => setSelectedViolation(v)}
                    className="cursor-pointer p-2.5 rounded-xl bg-gray-950/80 hover:bg-gray-900 border border-gray-800 hover:border-indigo-500/50 flex items-center justify-between text-xs transition-all group"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-cyan-300">{v.plate_number}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        v.violation_type === 'Red Light Violation' ? 'bg-red-950 text-red-400 border border-red-800/60' :
                        v.violation_type === 'Over Speeding' ? 'bg-amber-950 text-amber-400 border border-amber-800/60' :
                        v.violation_type === 'Helmet Violation' ? 'bg-purple-950 text-purple-400 border border-purple-800/60' :
                        'bg-rose-950 text-rose-400 border border-rose-800/60'
                      }`}>
                        {v.violation_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400 font-semibold">₹{v.fine_amount}</span>
                      <span className="text-[10px] text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">Inspect &rarr;</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Processing History Table */}
      <div className="glass-panel p-5 rounded-2xl border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-white">Recent Video Ingestion History</h2>
            <p className="text-[11px] text-gray-400">Past CCTV analysis jobs and vehicle detection records</p>
          </div>
          <button
            onClick={fetchRecentJobs}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-white p-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                <th className="pb-3 font-semibold">Job ID</th>
                <th className="pb-3 font-semibold">Video File</th>
                <th className="pb-3 font-semibold">Status</th>
                <th className="pb-3 font-semibold">Vehicles</th>
                <th className="pb-3 font-semibold">Violations</th>
                <th className="pb-3 font-semibold">Date & Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {recentJobs.map((j) => (
                <tr
                  key={j.id}
                  onClick={() => loadJobViolations(j.id)}
                  className="hover:bg-gray-800/50 cursor-pointer transition-colors group"
                  title="Click to view detections for this video"
                >
                  <td className="py-2.5 font-mono text-gray-400 group-hover:text-cyan-400">#{j.id}</td>
                  <td className="py-2.5 font-medium text-white truncate max-w-xs">{j.filename}</td>
                  <td className="py-2.5">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      j.status === 'completed' ? 'bg-emerald-950 text-emerald-400' :
                      j.status === 'processing' ? 'bg-indigo-950 text-cyan-300' :
                      'bg-red-950 text-red-400'
                    }`}>
                      {j.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-gray-300">{j.vehicles_detected}</td>
                  <td className="py-2.5 font-bold text-red-400">{j.violations_found}</td>
                  <td className="py-2.5 text-gray-400 flex items-center justify-between">
                    <span>{new Date(j.created_at).toLocaleString()}</span>
                    <span className="text-[10px] text-cyan-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity">View &rarr;</span>
                  </td>
                </tr>
              ))}
              {recentJobs.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-gray-500">
                    No video jobs recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Violation Detail Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-2xl rounded-3xl border border-gray-700 shadow-2xl p-6 overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between pb-4 border-b border-gray-800">
              <h3 className="text-base font-bold text-white">Detection Evidence: {selectedViolation.fine_ref}</h3>
              <button onClick={() => setSelectedViolation(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            <div className="mt-4 space-y-4 text-xs">
              {selectedViolation.evidence_url && (
                <img
                  src={getAssetUrl(selectedViolation.evidence_url)}
                  alt="Evidence"
                  className="w-full rounded-xl border border-gray-800 max-h-72 object-contain bg-black"
                />
              )}
              {selectedViolation.plate_crop_url && (
                <div>
                  <p className="text-gray-400 mb-1">Plate Crop:</p>
                  <img src={getAssetUrl(selectedViolation.plate_crop_url)} alt="Plate" className="h-16 rounded border border-gray-700 bg-white" />
                </div>
              )}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400 text-[10px]">License Plate:</span>
                  <p className="font-bold text-white text-sm font-mono">{selectedViolation.plate_number}</p>
                </div>
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400 text-[10px]">Violation Type:</span>
                  <p className="font-bold text-cyan-300 text-xs mt-0.5">{selectedViolation.violation_type}</p>
                </div>
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400 text-[10px]">Legal Fine:</span>
                  <p className="font-bold text-emerald-400 text-sm">₹{selectedViolation.fine_amount}</p>
                </div>
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400 text-[10px]">Enforcement Status:</span>
                  <span className={`inline-block mt-0.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                    selectedViolation.status === 'Paid' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'
                  }`}>
                    {selectedViolation.status}
                  </span>
                </div>
              </div>

              {selectedViolation.notes && (
                <div className="p-3 rounded-xl bg-gray-950/70 border border-gray-800 text-[11px] text-gray-300">
                  <span className="font-semibold text-gray-400">Telemetry & Notes: </span>
                  {selectedViolation.notes}
                </div>
              )}

              <div className="pt-2 flex justify-end gap-3">
                <a
                  href={`/check-fine?plate=${selectedViolation.plate_number}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-md shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
                >
                  <span>Open in Citizen Challan Portal &rarr;</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
