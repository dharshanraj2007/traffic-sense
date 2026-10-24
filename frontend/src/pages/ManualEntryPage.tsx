import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { FineRule } from '../types';
import {
  PlusCircle, ShieldCheck, Upload, AlertCircle,
  CheckCircle2, ArrowRight, IndianRupee, MapPin, Calendar
} from 'lucide-react';

export const ManualEntryPage: React.FC = () => {
  const [plateNumber, setPlateNumber] = useState('');
  const [violationType, setViolationType] = useState('Helmet Violation');
  const [location, setLocation] = useState('Sector 4 Junction, Smart City');
  const [occurredAt, setOccurredAt] = useState('');
  const [fineAmount, setFineAmount] = useState<number>(1000);
  const [notes, setNotes] = useState('');
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);

  const [fineRules, setFineRules] = useState<FineRule[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    // Set default occurredAt to current local datetime in ISO format for input
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    setOccurredAt(now.toISOString().slice(0, 16));

    // Fetch fine rules to auto-fill amounts
    const fetchRules = async () => {
      try {
        const res = await api.get('/api/fine-rules');
        setFineRules(res.data);
        const helmetRule = res.data.find((r: FineRule) => r.violation_type === 'Helmet Violation');
        if (helmetRule) setFineAmount(helmetRule.amount);
      } catch (err) {
        console.warn("Could not load fine rules", err);
      }
    };
    fetchRules();
  }, []);

  const handleTypeChange = (newType: string) => {
    setViolationType(newType);
    const matched = fineRules.find(r => r.violation_type === newType);
    if (matched) {
      setFineAmount(matched.amount);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!plateNumber.trim()) {
      setErrorMsg("Please enter a valid vehicle plate number.");
      return;
    }

    setSubmitting(true);

    const formData = new FormData();
    formData.append('plate_number', plateNumber.trim().toUpperCase());
    formData.append('violation_type', violationType);
    formData.append('location', location.trim());
    formData.append('fine_amount', fineAmount.toString());
    if (occurredAt) formData.append('occurred_at', new Date(occurredAt).toISOString());
    if (notes.trim()) formData.append('notes', notes.trim());
    if (evidenceFile) formData.append('evidence_file', evidenceFile);

    try {
      const res = await api.post('/api/violations', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setSuccessMsg(`Violation recorded successfully! Generated Reference: ${res.data.fine_ref}`);
      setTimeout(() => {
        navigate('/admin/fines');
      }, 1500);
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Failed to record violation. Please check fields.";
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-['Outfit'] text-white">Manual Violation Entry</h1>
        <p className="text-xs text-gray-400 mt-0.5">Register on-ground officer witnessed violations or manual camera citations</p>
      </div>

      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-gray-800 shadow-2xl">
        {errorMsg && (
          <div className="mb-5 p-3.5 rounded-xl bg-red-950/60 border border-red-800/60 flex items-start gap-2.5 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-5 p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-800/60 flex items-start gap-2.5 text-xs text-emerald-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* Plate Number */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">
                License Plate Number <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                required
                value={plateNumber}
                onChange={(e) => setPlateNumber(e.target.value.toUpperCase())}
                placeholder="e.g. DL01AB1234 or MH12DE4567"
                className="w-full px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm font-mono text-white placeholder-gray-500 uppercase tracking-wider focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Violation Type */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Violation Type</label>
              <select
                value={violationType}
                onChange={(e) => handleTypeChange(e.target.value)}
                className="w-full px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-xs sm:text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                {fineRules.map((r) => (
                  <option key={r.id} value={r.violation_type}>
                    {r.violation_type} (₹{r.amount})
                  </option>
                ))}
                {fineRules.length === 0 && (
                  <option value="Helmet Violation">Helmet Violation (₹1,000)</option>
                )}
              </select>
            </div>

            {/* Location */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Offense Location</label>
              <div className="relative">
                <MapPin className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Street / Junction / Landmark"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-xs sm:text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Date & Time */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Incident Date & Time</label>
              <div className="relative">
                <input
                  type="datetime-local"
                  required
                  value={occurredAt}
                  onChange={(e) => setOccurredAt(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-950 border border-gray-800 rounded-xl text-xs sm:text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Fine Amount */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Fine Amount (₹ INR)</label>
              <div className="relative">
                <IndianRupee className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="number"
                  min="0"
                  step="50"
                  required
                  value={fineAmount}
                  onChange={(e) => setFineAmount(parseFloat(e.target.value) || 0)}
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-xs sm:text-sm text-emerald-400 font-bold focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Evidence Image Upload */}
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">Attach Photo Evidence (Optional)</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setEvidenceFile(e.target.files ? e.target.files[0] : null)}
                className="w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-gray-800 file:text-gray-200 hover:file:bg-gray-700"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1.5">Officer Observation / Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Provide any additional details or witness observations..."
              rows={3}
              className="w-full px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Submit */}
          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-6 py-3 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50"
            >
              {submitting ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <PlusCircle className="w-4 h-4" />
                  <span>Generate Citation & Issue Fine</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
