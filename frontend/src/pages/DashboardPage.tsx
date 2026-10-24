import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { DashboardStats, Violation } from '../types';
import {
  AlertTriangle, CheckCircle2, Clock, IndianRupee,
  ShieldAlert, TrendingUp, Video, ArrowRight,
  Eye, Filter, RefreshCw, FileText
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts';

const STATUS_COLORS: Record<string, string> = {
  Pending: '#EAB308', // Amber
  Paid: '#22C55E',    // Green
  Cancelled: '#EF4444' // Red
};

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/dashboard/stats');
      setStats(res.data);
    } catch (err) {
      console.error("Failed to load dashboard stats", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading && !stats) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          <p className="text-xs text-gray-400">Loading enforcement metrics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-['Outfit'] text-white">Traffic Enforcement Dashboard</h1>
          <p className="text-xs text-gray-400 mt-0.5">Real-time surveillance analytics, helmet violation counts, and revenue reconciliation</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchStats}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <Link
            to="/admin/analyze"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-md shadow-indigo-600/20 transition-all"
          >
            <Video className="w-3.5 h-3.5" />
            <span>Analyze Traffic Video</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Violations */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-400">Total Violations</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-indigo-400" />
            </div>
          </div>
          <div className="text-2xl font-bold font-['Outfit'] text-white">{stats?.total_violations || 0}</div>
          <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-1">
            <span>Enforcement database records</span>
          </div>
        </div>

        {/* Pending Fines */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-400">Pending Fines</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <Clock className="w-4 h-4 text-amber-400" />
            </div>
          </div>
          <div className="text-2xl font-bold font-['Outfit'] text-amber-400">{stats?.pending_fines || 0}</div>
          <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-1">
            <span>₹{(stats?.total_pending_amount || 0).toLocaleString()} uncollected</span>
          </div>
        </div>

        {/* Paid Fines */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-400">Paid Fines</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
          </div>
          <div className="text-2xl font-bold font-['Outfit'] text-emerald-400">{stats?.paid_fines || 0}</div>
          <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-1">
            <span>₹{(stats?.total_collected_amount || 0).toLocaleString()} collected</span>
          </div>
        </div>

        {/* Needs Review */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-400">Needs Review</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-purple-400" />
            </div>
          </div>
          <div className="text-2xl font-bold font-['Outfit'] text-purple-400">{stats?.needs_review_count || 0}</div>
          <div className="flex items-center gap-1 text-[11px] text-gray-500 mt-1">
            <span>Unreadable OCR or low conf.</span>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Violations Trend Area Chart */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Violations Trend (Past 7 Days)</h2>
              <p className="text-[11px] text-gray-400">Daily automated & manual violation incidents</p>
            </div>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats?.daily_stats || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={11} tickLine={false} />
                <YAxis stroke="#9ca3af" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                  itemStyle={{ color: '#818cf8' }}
                />
                <Area type="monotone" dataKey="count" name="Violations" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Violations by Status Donut Chart */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 flex flex-col">
          <div className="mb-2">
            <h2 className="text-sm font-semibold text-white">Fine Status Distribution</h2>
            <p className="text-[11px] text-gray-400">Pending vs Paid vs Cancelled fines</p>
          </div>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats?.status_distribution || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {(stats?.status_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || '#6366f1'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(val) => <span className="text-xs text-gray-300">{val}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Violations Table */}
      <div className="glass-panel p-5 rounded-2xl border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-white">Recent Violations Log</h2>
            <p className="text-[11px] text-gray-400">Latest recorded road safety violations with evidence</p>
          </div>
          <Link
            to="/admin/fines"
            className="flex items-center gap-1 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            <span>View All Fines</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-gray-400">
                <th className="pb-3 font-semibold">Fine Ref</th>
                <th className="pb-3 font-semibold">Plate Number</th>
                <th className="pb-3 font-semibold">Type</th>
                <th className="pb-3 font-semibold">Date & Time</th>
                <th className="pb-3 font-semibold">Fine</th>
                <th className="pb-3 font-semibold">Status</th>
                <th className="pb-3 font-semibold">Source</th>
                <th className="pb-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {(stats?.recent_violations || []).map((v) => {
                const isPaid = v.status === 'Paid';
                const isPending = v.status === 'Pending';
                return (
                  <tr key={v.id} className="hover:bg-gray-800/30 transition-colors">
                    <td className="py-3 font-mono text-gray-300 font-medium">{v.fine_ref}</td>
                    <td className="py-3">
                      <span className="font-mono font-bold text-white bg-gray-900 px-2 py-0.5 rounded border border-gray-800">
                        {v.plate_number}
                      </span>
                      {v.needs_review && (
                        <span className="ml-1.5 px-1.5 py-0.5 text-[10px] font-semibold bg-purple-950 text-purple-300 rounded border border-purple-800/40">
                          Review
                        </span>
                      )}
                    </td>
                    <td className="py-3 text-gray-300">{v.violation_type}</td>
                    <td className="py-3 text-gray-400">
                      {new Date(v.occurred_at).toLocaleDateString()} {new Date(v.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3 font-semibold text-white">₹{v.fine_amount.toLocaleString()}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        isPaid ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50' :
                        isPending ? 'bg-amber-950/80 text-amber-400 border border-amber-800/50' :
                        'bg-red-950/80 text-red-400 border border-red-800/50'
                      }`}>
                        {v.status}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-gray-900 text-gray-400 rounded">
                        {v.source}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => setSelectedViolation(v)}
                        className="p-1.5 text-gray-400 hover:text-cyan-400 hover:bg-gray-800 rounded-lg transition-colors"
                        title="View Evidence & Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Violation Detail Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-2xl rounded-3xl border border-gray-700 shadow-2xl p-6 overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between pb-4 border-b border-gray-800">
              <div>
                <h3 className="text-base font-bold text-white font-['Outfit']">Violation Details: {selectedViolation.fine_ref}</h3>
                <p className="text-xs text-gray-400">Incident photographic evidence and timestamp audit</p>
              </div>
              <button
                onClick={() => setSelectedViolation(null)}
                className="text-gray-400 hover:text-white p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="mt-5 space-y-5">
              {/* Evidence Snapshot */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2">Camera Surveillance Evidence</label>
                {selectedViolation.evidence_url ? (
                  <div className="rounded-xl overflow-hidden border border-gray-800 bg-gray-950">
                    <img
                      src={selectedViolation.evidence_url}
                      alt="Violation Evidence Frame"
                      className="w-full max-h-72 object-contain"
                    />
                  </div>
                ) : (
                  <div className="h-40 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-center text-xs text-gray-500">
                    No visual evidence attached
                  </div>
                )}
              </div>

              {/* Number Plate Crop */}
              {selectedViolation.plate_crop_url && (
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-2">Extracted Plate Crop</label>
                  <img
                    src={selectedViolation.plate_crop_url}
                    alt="License Plate Crop"
                    className="h-16 rounded-lg border border-gray-700 object-contain bg-white"
                  />
                </div>
              )}

              {/* Details grid */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800">
                  <span className="text-gray-400">License Plate:</span>
                  <p className="font-mono font-bold text-white text-sm mt-0.5">{selectedViolation.plate_number}</p>
                </div>
                <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800">
                  <span className="text-gray-400">Violation Type:</span>
                  <p className="font-semibold text-white text-sm mt-0.5">{selectedViolation.violation_type}</p>
                </div>
                <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800">
                  <span className="text-gray-400">Location:</span>
                  <p className="text-gray-300 mt-0.5">{selectedViolation.location}</p>
                </div>
                <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800">
                  <span className="text-gray-400">Fine Amount:</span>
                  <p className="font-bold text-emerald-400 text-sm mt-0.5">₹{selectedViolation.fine_amount.toLocaleString()}</p>
                </div>
              </div>

              <div className="flex justify-end pt-3">
                <button
                  onClick={() => setSelectedViolation(null)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white text-xs font-semibold rounded-xl"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
