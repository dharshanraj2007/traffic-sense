import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { FineRule } from '../types';
import {
  Settings, CheckCircle2, ShieldCheck, Cpu,
  Database, RefreshCw, Save, Edit3, AlertCircle
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [rules, setRules] = useState<FineRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editAmount, setEditAmount] = useState<number>(0);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchRulesAndHealth = async () => {
    setLoading(true);
    try {
      const [rRes, hRes] = await Promise.all([
        api.get('/api/fine-rules'),
        api.get('/api/health')
      ]);
      setRules(rRes.data);
      setSystemHealth(hRes.data);
    } catch (err) {
      console.error("Failed to fetch settings", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRulesAndHealth();
  }, []);

  const handleStartEdit = (rule: FineRule) => {
    setEditingId(rule.id);
    setEditAmount(rule.amount);
  };

  const handleSaveRule = async (id: number) => {
    try {
      await api.put(`/api/fine-rules/${id}`, {
        amount: editAmount
      });
      setEditingId(null);
      setSuccessMsg("Fine rule amount updated successfully!");
      setTimeout(() => setSuccessMsg(null), 2500);
      fetchRulesAndHealth();
    } catch (err) {
      alert("Failed to update fine rule amount.");
    }
  };

  const handleToggleActive = async (rule: FineRule) => {
    try {
      await api.put(`/api/fine-rules/${rule.id}`, {
        active: !rule.active
      });
      fetchRulesAndHealth();
    } catch (err) {
      alert("Failed to update rule status.");
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold font-['Outfit'] text-white">Fine Rules & AI Engine Settings</h1>
        <p className="text-xs text-gray-400 mt-0.5">Configure statutory penalty amounts and inspect core neural weights status</p>
      </div>

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-800/60 flex items-center gap-2.5 text-xs text-emerald-300">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Fine Rules Table */}
      <div className="glass-panel p-6 rounded-3xl border border-gray-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Settings className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Statutory Violation Penalty Tariff</h2>
              <p className="text-[11px] text-gray-400">Baseline fines applied during automatic e-challan creation</p>
            </div>
          </div>
          <button
            onClick={fetchRulesAndHealth}
            className="p-1.5 rounded-lg bg-gray-900 text-gray-400 hover:text-white border border-gray-800"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-950 text-gray-400 border-b border-gray-800">
              <tr>
                <th className="p-3 font-semibold">Violation Type</th>
                <th className="p-3 font-semibold">Standard Fine (₹ INR)</th>
                <th className="p-3 font-semibold">Rule Status</th>
                <th className="p-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {rules.map((rule) => {
                const isEditing = editingId === rule.id;
                return (
                  <tr key={rule.id} className="hover:bg-gray-800/30">
                    <td className="p-3 font-semibold text-white">{rule.violation_type}</td>
                    <td className="p-3 font-mono">
                      {isEditing ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            value={editAmount}
                            onChange={(e) => setEditAmount(parseFloat(e.target.value) || 0)}
                            className="w-24 px-2 py-1 bg-gray-950 border border-indigo-500 rounded text-xs text-white"
                          />
                        </div>
                      ) : (
                        <span className="text-emerald-400 font-bold">₹{rule.amount.toLocaleString()}</span>
                      )}
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => handleToggleActive(rule)}
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold transition-colors ${
                          rule.active
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/50'
                            : 'bg-gray-900 text-gray-500 border border-gray-800'
                        }`}
                      >
                        {rule.active ? 'Active' : 'Disabled'}
                      </button>
                    </td>
                    <td className="p-3 text-right">
                      {isEditing ? (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleSaveRule(rule.id)}
                            className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-semibold flex items-center gap-1"
                          >
                            <Save className="w-3 h-3" /> Save
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded text-[11px]"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleStartEdit(rule)}
                          className="p-1.5 text-gray-400 hover:text-cyan-400 hover:bg-gray-800 rounded-lg transition-colors"
                          title="Edit Fine Amount"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Engine Status & Diagnostics */}
      <div className="glass-panel p-6 rounded-3xl border border-gray-800 space-y-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">AI Diagnostics & Engine Telemetry</h2>
            <p className="text-[11px] text-gray-400">Pretrained model weights loaded in memory</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-gray-950/80 border border-gray-800">
            <span className="text-gray-400">Vehicle Tracking Model</span>
            <p className="font-bold text-white text-sm mt-1">YOLOv8n (COCO)</p>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800/40">
              ByteTrack Enabled
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-gray-950/80 border border-gray-800">
            <span className="text-gray-400">Helmet Detection Model</span>
            <p className="font-bold text-white text-sm mt-1">safetyHelmet-YOLOv8</p>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800/40">
              Classes: With / Without
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-gray-950/80 border border-gray-800">
            <span className="text-gray-400">License Plate OCR</span>
            <p className="font-bold text-white text-sm mt-1">EasyOCR + Pretrained Plate</p>
            <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800/40">
              Indian RegEx Filtered
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
