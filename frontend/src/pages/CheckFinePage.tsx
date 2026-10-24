import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { api } from '../api/client';
import { PublicFineResult, Violation } from '../types';
import {
  Search, ShieldCheck, AlertCircle, CheckCircle2,
  Calendar, MapPin, IndianRupee, Eye, CreditCard,
  ArrowRight, ShieldAlert, Lock
} from 'lucide-react';

export const CheckFinePage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialPlate = searchParams.get('plate') || '';

  const [plate, setPlate] = useState(initialPlate);
  const [result, setResult] = useState<PublicFineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Simulated Payment Modal
  const [payingViolation, setPayingViolation] = useState<Violation | null>(null);
  const [paymentSuccess, setPaymentSuccess] = useState<string | null>(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  const performSearch = async (plateQuery: string) => {
    if (!plateQuery.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setSearched(true);
    setPaymentSuccess(null);

    try {
      const res = await api.get(`/api/public/fine/${encodeURIComponent(plateQuery.trim().toUpperCase())}`);
      setResult(res.data);
    } catch (err: any) {
      setErrorMsg("Failed to query vehicle registration records. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialPlate) {
      setPlate(initialPlate);
      performSearch(initialPlate);
    }
  }, [initialPlate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(plate);
  };

  const handleSimulatePayment = async () => {
    if (!payingViolation) return;
    setIsProcessingPayment(true);

    try {
      const res = await api.post(`/api/public/pay/${payingViolation.fine_ref}`);
      setPaymentSuccess(`Challan ${payingViolation.fine_ref} for ₹${payingViolation.fine_amount} successfully settled! Payment Ref: ${res.data.payment_ref}`);
      setPayingViolation(null);
      // Refresh lookup
      performSearch(plate);
    } catch (err: any) {
      alert("Payment settlement encountered an error. Please try again.");
    } finally {
      setIsProcessingPayment(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col">
      <Navbar />

      <div className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-10 space-y-8">
        {/* Header */}
        <div className="text-center max-w-xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 text-cyan-400 border border-cyan-800/40 text-xs font-semibold mb-3">
            <Search className="w-3.5 h-3.5" />
            Citizen Digital Portal
          </div>
          <h1 className="text-3xl font-extrabold font-['Outfit'] text-white">
            Vehicle E-Challan & Fine Inquiry
          </h1>
          <p className="text-xs text-gray-400 mt-2">
            Verify automated camera citations, review high-definition photographic evidence, and securely settle outstanding traffic fines
          </p>
        </div>

        {/* Search Input Card */}
        <div className="max-w-xl mx-auto glass-panel p-3 rounded-2xl border border-gray-800 shadow-2xl">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                value={plate}
                onChange={(e) => setPlate(e.target.value.toUpperCase())}
                placeholder="Enter Plate Number (e.g. DL01AB1234)"
                className="w-full pl-10 pr-4 py-3 bg-gray-950 border border-gray-800 rounded-xl text-sm font-mono text-white placeholder-gray-500 uppercase tracking-widest focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-xs font-semibold rounded-xl flex items-center gap-2 transition-all disabled:opacity-50 shrink-0"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <span>Lookup</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Payment Confirmation Banner */}
        {paymentSuccess && (
          <div className="max-w-xl mx-auto p-4 rounded-2xl bg-emerald-950/70 border border-emerald-800/60 flex items-center gap-3 text-xs text-emerald-300">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <span>{paymentSuccess}</span>
          </div>
        )}

        {/* Error */}
        {errorMsg && (
          <div className="max-w-xl mx-auto p-4 rounded-2xl bg-red-950/70 border border-red-800/60 flex items-center gap-3 text-xs text-red-300">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Results Area */}
        {searched && result && (
          <div className="space-y-6">
            {/* Overview Banner */}
            <div className="glass-panel p-6 rounded-3xl border border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gray-950 border border-gray-700 flex items-center justify-center font-mono font-extrabold text-white text-lg px-2">
                  IND
                </div>
                <div>
                  <span className="text-xs text-gray-400">Registered Vehicle</span>
                  <h2 className="text-2xl font-black font-mono text-white tracking-wider">{result.plate_number}</h2>
                </div>
              </div>

              <div className="flex items-center gap-6 text-center sm:text-right">
                <div>
                  <span className="text-[11px] text-gray-400">Total Offenses</span>
                  <p className="text-xl font-bold font-['Outfit'] text-white">{result.total_violations}</p>
                </div>
                <div>
                  <span className="text-[11px] text-gray-400">Pending Challans</span>
                  <p className="text-xl font-bold font-['Outfit'] text-amber-400">{result.pending_violations}</p>
                </div>
                <div>
                  <span className="text-[11px] text-gray-400">Total Due Amount</span>
                  <p className="text-xl font-bold font-['Outfit'] text-emerald-400">₹{result.total_pending_amount.toLocaleString()}</p>
                </div>
              </div>
            </div>

            {/* Violations List */}
            {result.violations.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white">Recorded Violation Notices ({result.violations.length})</h3>

                <div className="grid grid-cols-1 gap-4">
                  {result.violations.map((v) => {
                    const isPaid = v.status === 'Paid';
                    const isPending = v.status === 'Pending';
                    return (
                      <div
                        key={v.id}
                        className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                      >
                        <div className="flex items-start gap-4">
                          {/* Evidence Thumbnail */}
                          {v.evidence_url ? (
                            <img
                              src={v.evidence_url}
                              alt="Evidence"
                              className="w-24 h-16 rounded-xl object-cover border border-gray-700 bg-gray-950 shrink-0"
                            />
                          ) : (
                            <div className="w-24 h-16 rounded-xl bg-gray-950 border border-gray-800 flex items-center justify-center text-[10px] text-gray-600 shrink-0">
                              No image
                            </div>
                          )}

                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono text-xs text-cyan-400 font-semibold">{v.fine_ref}</span>
                              <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                                isPaid ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40' :
                                isPending ? 'bg-amber-950 text-amber-400 border border-amber-800/40' :
                                'bg-red-950 text-red-400'
                              }`}>
                                {v.status}
                              </span>
                            </div>
                            <h4 className="text-sm font-bold text-white">{v.violation_type}</h4>
                            <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3 text-gray-500" />
                                {new Date(v.occurred_at).toLocaleDateString()} {new Date(v.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                              <span className="flex items-center gap-1">
                                <MapPin className="w-3 h-3 text-gray-500" />
                                {v.location}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Amount & Pay CTA */}
                        <div className="flex items-center justify-between md:justify-end gap-4 w-full md:w-auto pt-3 md:pt-0 border-t md:border-0 border-gray-800">
                          <div className="text-right">
                            <span className="text-[10px] text-gray-400">Penalty Amount</span>
                            <p className="text-lg font-bold text-emerald-400">₹{v.fine_amount.toLocaleString()}</p>
                          </div>

                          {isPending && (
                            <button
                              onClick={() => setPayingViolation(v)}
                              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20 transition-all shrink-0"
                            >
                              <CreditCard className="w-3.5 h-3.5" />
                              <span>Settle Fine</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="glass-panel p-12 rounded-3xl border border-gray-800 text-center">
                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3 opacity-90" />
                <h3 className="text-base font-bold text-white">No Traffic Violations Found!</h3>
                <p className="text-xs text-gray-400 max-w-sm mx-auto mt-1">
                  Vehicle <strong>{result.plate_number}</strong> has a completely clean enforcement record with zero outstanding fines.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Payment Simulation Modal */}
        {payingViolation && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="glass-panel w-full max-w-md rounded-3xl border border-gray-700 shadow-2xl p-6">
              <div className="flex items-center justify-between pb-3 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-base font-bold text-white">Digital Challan Settlement</h3>
                </div>
                <button onClick={() => setPayingViolation(null)} className="text-gray-400 hover:text-white">✕</button>
              </div>

              <div className="my-5 space-y-3 text-xs">
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <div className="flex justify-between text-gray-400 mb-1">
                    <span>Notice Number:</span>
                    <span className="font-mono text-white">{payingViolation.fine_ref}</span>
                  </div>
                  <div className="flex justify-between text-gray-400 mb-1">
                    <span>Vehicle Plate:</span>
                    <span className="font-mono font-bold text-cyan-400">{payingViolation.plate_number}</span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>Violation:</span>
                    <span className="text-white">{payingViolation.violation_type}</span>
                  </div>
                </div>

                <div className="p-4 bg-emerald-950/40 rounded-xl border border-emerald-800/40 flex items-center justify-between">
                  <span className="text-gray-300 font-medium">Payable Amount:</span>
                  <span className="text-xl font-black text-emerald-400">₹{payingViolation.fine_amount.toLocaleString()}</span>
                </div>

                <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800 text-gray-400 text-[11px] flex items-center gap-2">
                  <Lock className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>Simulated Payment Gateway (UPI / NetBanking / Debit Card demonstration)</span>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setPayingViolation(null)}
                  className="px-4 py-2 bg-gray-800 text-gray-300 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSimulatePayment}
                  disabled={isProcessingPayment}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
                >
                  {isProcessingPayment ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  ) : (
                    <>
                      <span>Authorize Payment</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
