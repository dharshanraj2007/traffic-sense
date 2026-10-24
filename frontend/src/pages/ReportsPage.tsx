import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
  FileText, Download, Calendar, Filter, BarChart3,
  CheckCircle2, Clock, AlertTriangle, ShieldCheck, RefreshCw
} from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('All');
  const [sourceFilter, setSourceFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/reports/summary');
      setSummary(res.data);
    } catch (err) {
      console.error("Failed to load summary", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleExport = async (format: 'csv' | 'pdf') => {
    setDownloadingFormat(format);
    try {
      const params = new URLSearchParams();
      params.append('format', format);
      if (statusFilter !== 'All') params.append('status', statusFilter);
      if (sourceFilter !== 'All') params.append('source', sourceFilter);
      if (search.trim()) params.append('search', search.trim());
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const res = await api.get(`/api/reports/export?${params.toString()}`, {
        responseType: 'blob'
      });

      // Trigger browser download
      const blob = new Blob([res.data], {
        type: format === 'csv' ? 'text/csv' : 'application/pdf'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `traffic_enforcement_report_${Date.now()}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Failed to export ${format.toUpperCase()} report.`);
    } finally {
      setDownloadingFormat(null);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-['Outfit'] text-white">Reports & Audit Exports</h1>
          <p className="text-xs text-gray-400 mt-0.5">Generate formal enforcement summaries, CSV logs, and official printable PDF reports</p>
        </div>
        <button
          onClick={fetchSummary}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-gray-800">
          <span className="text-xs text-gray-400">Total Issued Fines</span>
          <p className="text-2xl font-bold font-['Outfit'] text-white mt-1">
            {summary?.total_violations || 0}
          </p>
          <p className="text-[11px] text-gray-500 mt-0.5">Total registered cases</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800">
          <span className="text-xs text-gray-400">Total Fines Assessed</span>
          <p className="text-2xl font-bold font-['Outfit'] text-cyan-400 mt-1">
            ₹{(summary?.total_amount || 0).toLocaleString()}
          </p>
          <p className="text-[11px] text-gray-500 mt-0.5">Cumulative fine value</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800">
          <span className="text-xs text-gray-400">Revenue Realized</span>
          <p className="text-2xl font-bold font-['Outfit'] text-emerald-400 mt-1">
            ₹{(summary?.collected_amount || 0).toLocaleString()}
          </p>
          <p className="text-[11px] text-gray-500 mt-0.5">{summary?.paid_count || 0} settled violations</p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800">
          <span className="text-xs text-gray-400">Pending Receivables</span>
          <p className="text-2xl font-bold font-['Outfit'] text-amber-400 mt-1">
            ₹{(summary?.pending_amount || 0).toLocaleString()}
          </p>
          <p className="text-[11px] text-gray-500 mt-0.5">{summary?.pending_count || 0} unpaid notices</p>
        </div>
      </div>

      {/* Export Configuration Card */}
      <div className="glass-panel p-6 rounded-3xl border border-gray-800 space-y-5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Download className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Generate Filtered Export</h2>
            <p className="text-[11px] text-gray-400">Select parameters to download custom CSV spreadsheets or legal PDF dossiers</p>
          </div>
        </div>

        {/* Filter controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-gray-400 mb-1 font-semibold">Plate or Ref Filter</label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="e.g. DL01 or FN-2026"
              className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-white uppercase focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-gray-400 mb-1 font-semibold">Status Filter</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="All">All Statuses</option>
              <option value="Pending">Pending Only</option>
              <option value="Paid">Paid Only</option>
              <option value="Cancelled">Cancelled Only</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-400 mb-1 font-semibold">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-white focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-gray-400 mb-1 font-semibold">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-white focus:outline-none"
            />
          </div>
        </div>

        {/* Export Buttons */}
        <div className="pt-3 border-t border-gray-800/80 flex flex-wrap items-center justify-end gap-3">
          <button
            onClick={() => handleExport('csv')}
            disabled={downloadingFormat === 'csv'}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-gray-900 hover:bg-gray-800 text-gray-200 border border-gray-700 transition-colors disabled:opacity-50"
          >
            {downloadingFormat === 'csv' ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
            )}
            <span>Export Filtered CSV</span>
          </button>

          <button
            onClick={() => handleExport('pdf')}
            disabled={downloadingFormat === 'pdf'}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-md shadow-indigo-600/30 transition-all disabled:opacity-50"
          >
            {downloadingFormat === 'pdf' ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            ) : (
              <Download className="w-3.5 h-3.5 text-white" />
            )}
            <span>Export Official Enforcement PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};
