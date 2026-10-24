import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Violation, ViolationListResponse } from '../types';
import {
  Search, Filter, CheckCircle2, XCircle, Eye,
  Edit2, Trash2, Calendar, FileText, ChevronLeft,
  ChevronRight, RefreshCw, AlertTriangle, ShieldCheck
} from 'lucide-react';

export const FinesPage: React.FC = () => {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [sourceFilter, setSourceFilter] = useState('All');
  const [needsReviewOnly, setNeedsReviewOnly] = useState(false);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Modals state
  const [selectedViolation, setSelectedViolation] = useState<Violation | null>(null);
  const [editPlateViolation, setEditPlateViolation] = useState<Violation | null>(null);
  const [newPlateText, setNewPlateText] = useState('');
  const [statusUpdateViolation, setStatusUpdateViolation] = useState<Violation | null>(null);
  const [targetStatus, setTargetStatus] = useState<'Paid' | 'Cancelled'>('Paid');
  const [paymentRefInput, setPaymentRefInput] = useState('');
  const [statusNotes, setStatusNotes] = useState('');

  const fetchViolations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      if (search.trim()) params.append('search', search.trim());
      if (statusFilter !== 'All') params.append('status', statusFilter);
      if (sourceFilter !== 'All') params.append('source', sourceFilter);
      if (needsReviewOnly) params.append('needs_review', 'true');
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const res = await api.get(`/api/violations?${params.toString()}`);
      const data: ViolationListResponse = res.data;
      setViolations(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Failed to fetch violations", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchViolations();
  }, [page, statusFilter, sourceFilter, needsReviewOnly, startDate, endDate]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchViolations();
  };

  const handleUpdateStatus = async () => {
    if (!statusUpdateViolation) return;
    try {
      await api.patch(`/api/violations/${statusUpdateViolation.id}/status`, {
        status: targetStatus,
        payment_ref: paymentRefInput.trim() || undefined,
        notes: statusNotes.trim() || undefined
      });
      setStatusUpdateViolation(null);
      setPaymentRefInput('');
      setStatusNotes('');
      fetchViolations();
    } catch (err) {
      alert("Failed to update status. Please try again.");
    }
  };

  const handleSaveEditPlate = async () => {
    if (!editPlateViolation) return;
    try {
      await api.put(`/api/violations/${editPlateViolation.id}`, {
        plate_number: newPlateText.trim().toUpperCase(),
        needs_review: false,
      });
      setEditPlateViolation(null);
      fetchViolations();
    } catch (err) {
      alert("Failed to update plate number.");
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this violation record? This cannot be undone.")) {
      try {
        await api.delete(`/api/violations/${id}`);
        fetchViolations();
      } catch (err) {
        alert("Failed to delete record.");
      }
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-['Outfit'] text-white">Fine & Violation Management</h1>
          <p className="text-xs text-gray-400 mt-0.5">Search, review, audit, and update status for all recorded traffic offenses</p>
        </div>
        <button
          onClick={fetchViolations}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-gray-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="md:col-span-2 relative">
            <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Plate (e.g. MH12) or Fine Ref (FN-...)"
              className="w-full pl-10 pr-4 py-2 bg-gray-950/70 border border-gray-800 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 uppercase font-mono"
            />
          </form>

          {/* Status Dropdown */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 bg-gray-950/70 border border-gray-800 rounded-xl text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="All">All Statuses</option>
              <option value="Pending">Pending Only</option>
              <option value="Paid">Paid Only</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>

          {/* Source Dropdown */}
          <div>
            <select
              value={sourceFilter}
              onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 bg-gray-950/70 border border-gray-800 rounded-xl text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="All">All Sources</option>
              <option value="AI">AI Automated Only</option>
              <option value="Manual">Manual Entry Only</option>
            </select>
          </div>
        </div>

        {/* Date Filter & Needs Review Toggle */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-gray-800/60 text-xs">
          <div className="flex items-center gap-2">
            <Calendar className="w-3.5 h-3.5 text-gray-400" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
              className="px-2.5 py-1 bg-gray-950/70 border border-gray-800 rounded-lg text-xs text-gray-300 focus:outline-none"
            />
            <span className="text-gray-500">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
              className="px-2.5 py-1 bg-gray-950/70 border border-gray-800 rounded-lg text-xs text-gray-300 focus:outline-none"
            />
            {(startDate || endDate) && (
              <button
                onClick={() => { setStartDate(''); setEndDate(''); }}
                className="text-[11px] text-gray-400 hover:text-white underline ml-1"
              >
                Clear
              </button>
            )}
          </div>

          <label className="flex items-center gap-2 cursor-pointer text-gray-300 hover:text-white">
            <input
              type="checkbox"
              checked={needsReviewOnly}
              onChange={(e) => { setNeedsReviewOnly(e.target.checked); setPage(1); }}
              className="rounded bg-gray-900 border-gray-700 text-indigo-600 focus:ring-0"
            />
            <span className="text-purple-400 font-semibold flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Needs Review Only
            </span>
          </label>
        </div>
      </div>

      {/* Main Table */}
      <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-950/70 text-gray-400 border-b border-gray-800">
              <tr>
                <th className="p-3.5 font-semibold">Evidence</th>
                <th className="p-3.5 font-semibold">Fine Ref</th>
                <th className="p-3.5 font-semibold">Plate Number</th>
                <th className="p-3.5 font-semibold">Violation</th>
                <th className="p-3.5 font-semibold">Date & Location</th>
                <th className="p-3.5 font-semibold">Fine</th>
                <th className="p-3.5 font-semibold">Status</th>
                <th className="p-3.5 font-semibold">Source</th>
                <th className="p-3.5 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {violations.map((v) => {
                const isPaid = v.status === 'Paid';
                const isPending = v.status === 'Pending';
                return (
                  <tr key={v.id} className="hover:bg-gray-800/20 transition-colors">
                    {/* Thumbnail */}
                    <td className="p-3.5">
                      {v.evidence_url ? (
                        <img
                          src={v.evidence_url}
                          alt="Thumbnail"
                          onClick={() => setSelectedViolation(v)}
                          className="w-12 h-8 rounded object-cover cursor-pointer hover:opacity-80 transition-opacity border border-gray-700 bg-gray-900"
                        />
                      ) : (
                        <div className="w-12 h-8 rounded bg-gray-900 border border-gray-800 flex items-center justify-center text-[10px] text-gray-600">
                          N/A
                        </div>
                      )}
                    </td>

                    {/* Fine Ref */}
                    <td className="p-3.5 font-mono text-gray-300 font-medium whitespace-nowrap">
                      {v.fine_ref}
                    </td>

                    {/* Plate */}
                    <td className="p-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono font-bold text-white bg-gray-950 px-2 py-0.5 rounded border border-gray-800">
                          {v.plate_number}
                        </span>
                        {v.needs_review && (
                          <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase bg-purple-950 text-purple-300 rounded border border-purple-800/40">
                            Review
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Violation Type */}
                    <td className="p-3.5 text-gray-300 font-medium whitespace-nowrap">
                      {v.violation_type}
                    </td>

                    {/* Date & Location */}
                    <td className="p-3.5 text-gray-400">
                      <div>{new Date(v.occurred_at).toLocaleDateString()} {new Date(v.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                      <div className="text-[11px] text-gray-500 truncate max-w-xs">{v.location}</div>
                    </td>

                    {/* Fine Amount */}
                    <td className="p-3.5 font-bold text-white whitespace-nowrap">
                      ₹{v.fine_amount.toLocaleString()}
                    </td>

                    {/* Status Badge */}
                    <td className="p-3.5 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        isPaid ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50' :
                        isPending ? 'bg-amber-950/80 text-amber-400 border border-amber-800/50' :
                        'bg-red-950/80 text-red-400 border border-red-800/50'
                      }`}>
                        {v.status}
                      </span>
                    </td>

                    {/* Source */}
                    <td className="p-3.5 text-gray-400 whitespace-nowrap">
                      <span className="px-1.5 py-0.5 text-[10px] bg-gray-900 rounded">
                        {v.source}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="p-3.5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1">
                        {/* View detail */}
                        <button
                          onClick={() => setSelectedViolation(v)}
                          className="p-1.5 text-gray-400 hover:text-cyan-400 hover:bg-gray-800 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>

                        {/* Edit Plate */}
                        <button
                          onClick={() => { setEditPlateViolation(v); setNewPlateText(v.plate_number); }}
                          className="p-1.5 text-gray-400 hover:text-indigo-400 hover:bg-gray-800 rounded-lg transition-colors"
                          title="Edit Plate Number"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>

                        {/* Mark Paid */}
                        {isPending && (
                          <button
                            onClick={() => { setStatusUpdateViolation(v); setTargetStatus('Paid'); }}
                            className="p-1.5 text-gray-400 hover:text-emerald-400 hover:bg-gray-800 rounded-lg transition-colors"
                            title="Mark as Paid"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          </button>
                        )}

                        {/* Cancel */}
                        {isPending && (
                          <button
                            onClick={() => { setStatusUpdateViolation(v); setTargetStatus('Cancelled'); }}
                            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors"
                            title="Cancel Violation"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                          </button>
                        )}

                        {/* Delete */}
                        <button
                          onClick={() => handleDelete(v.id)}
                          className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors"
                          title="Delete Record"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {violations.length === 0 && !loading && (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-gray-500">
                    No violations found matching the criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400">
          <span>Showing {violations.length} of {total} records (Page {page} of {totalPages})</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1.5 rounded-lg bg-gray-900 border border-gray-800 hover:bg-gray-800 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-white px-2">{page}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1.5 rounded-lg bg-gray-900 border border-gray-800 hover:bg-gray-800 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* View Detail Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-2xl rounded-3xl border border-gray-700 shadow-2xl p-6 overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between pb-4 border-b border-gray-800">
              <div>
                <h3 className="text-base font-bold text-white font-['Outfit']">Violation Details: {selectedViolation.fine_ref}</h3>
                <p className="text-xs text-gray-400">Surveillance frame snapshot and status logs</p>
              </div>
              <button onClick={() => setSelectedViolation(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              {/* Evidence Frame */}
              {selectedViolation.evidence_url && (
                <div>
                  <label className="block text-gray-400 mb-1 font-semibold">Surveillance Frame Snapshot</label>
                  <img
                    src={selectedViolation.evidence_url}
                    alt="Evidence Frame"
                    className="w-full rounded-xl border border-gray-800 max-h-72 object-contain bg-black"
                  />
                </div>
              )}

              {/* Number Plate Crop */}
              {selectedViolation.plate_crop_url && (
                <div>
                  <label className="block text-gray-400 mb-1 font-semibold">Extracted License Plate</label>
                  <img
                    src={selectedViolation.plate_crop_url}
                    alt="Plate Crop"
                    className="h-16 rounded border border-gray-700 bg-white object-contain"
                  />
                </div>
              )}

              {/* Grid info */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400">Plate Number:</span>
                  <p className="font-mono font-bold text-white text-sm">{selectedViolation.plate_number}</p>
                </div>
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400">Violation Type:</span>
                  <p className="font-semibold text-white text-sm">{selectedViolation.violation_type}</p>
                </div>
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400">Fine Amount:</span>
                  <p className="font-bold text-emerald-400 text-sm">₹{selectedViolation.fine_amount}</p>
                </div>
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400">Status:</span>
                  <p className="font-bold text-white text-sm">{selectedViolation.status}</p>
                </div>
              </div>

              {selectedViolation.notes && (
                <div className="p-3 bg-gray-950 rounded-xl border border-gray-800">
                  <span className="text-gray-400 font-semibold">Notes:</span>
                  <p className="text-gray-300 mt-1 whitespace-pre-line">{selectedViolation.notes}</p>
                </div>
              )}

              {/* Status History Logs */}
              {selectedViolation.status_logs && selectedViolation.status_logs.length > 0 && (
                <div className="pt-2">
                  <label className="block text-gray-400 mb-2 font-semibold">Audit Status History</label>
                  <div className="space-y-1.5">
                    {selectedViolation.status_logs.map((log) => (
                      <div key={log.id} className="p-2 rounded bg-gray-950 border border-gray-800 text-[11px] flex justify-between">
                        <span>{log.old_status} &rarr; <strong className="text-cyan-400">{log.new_status}</strong> {log.notes && `(${log.notes})`}</span>
                        <span className="text-gray-500">{new Date(log.changed_at).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setSelectedViolation(null)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-semibold"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Plate Modal */}
      {editPlateViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-md rounded-3xl border border-gray-700 shadow-2xl p-6">
            <h3 className="text-base font-bold text-white mb-2">Edit Plate Number</h3>
            <p className="text-xs text-gray-400 mb-4">
              Correct OCR reading for fine <code className="text-cyan-400">{editPlateViolation.fine_ref}</code>
            </p>
            <input
              type="text"
              value={newPlateText}
              onChange={(e) => setNewPlateText(e.target.value.toUpperCase())}
              placeholder="e.g. DL01AB1234"
              className="w-full px-4 py-2.5 bg-gray-950 border border-gray-800 rounded-xl text-sm font-mono text-white uppercase focus:outline-none focus:border-indigo-500 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setEditPlateViolation(null)}
                className="px-4 py-2 bg-gray-800 text-gray-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEditPlate}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold"
              >
                Save Plate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status Update Modal (Mark Paid / Cancel) */}
      {statusUpdateViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-md rounded-3xl border border-gray-700 shadow-2xl p-6">
            <h3 className="text-base font-bold text-white mb-1">
              Mark Violation as <span className={targetStatus === 'Paid' ? 'text-emerald-400' : 'text-red-400'}>{targetStatus}</span>
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Fine Reference: <code className="text-cyan-400">{statusUpdateViolation.fine_ref}</code> ({statusUpdateViolation.plate_number})
            </p>

            {targetStatus === 'Paid' && (
              <div className="mb-3">
                <label className="block text-xs font-semibold text-gray-300 mb-1">Payment Reference (Optional)</label>
                <input
                  type="text"
                  value={paymentRefInput}
                  onChange={(e) => setPaymentRefInput(e.target.value)}
                  placeholder="e.g. UPI-TXN-987654"
                  className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            )}

            <div className="mb-4">
              <label className="block text-xs font-semibold text-gray-300 mb-1">Action Note / Justification</label>
              <textarea
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
                placeholder="Reason for status change..."
                rows={2}
                className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setStatusUpdateViolation(null)}
                className="px-4 py-2 bg-gray-800 text-gray-300 rounded-xl text-xs font-semibold"
              >
                Dismiss
              </button>
              <button
                onClick={handleUpdateStatus}
                className={`px-4 py-2 rounded-xl text-xs font-semibold text-white ${
                  targetStatus === 'Paid' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-red-600 hover:bg-red-500'
                }`}
              >
                Confirm {targetStatus}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
