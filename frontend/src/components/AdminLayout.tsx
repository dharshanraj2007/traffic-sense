import React, { useState, useEffect } from 'react';
import { Link, NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  LayoutDashboard, Video, FileText, PlusCircle,
  BarChart3, Settings, LogOut, ShieldCheck,
  ExternalLink, Bell, Cpu, Menu, X
} from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { admin, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{ status: string; models_loaded: boolean } | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.get('/api/health');
        setHealthStatus(res.data);
      } catch (err) {
        setHealthStatus({ status: 'error', models_loaded: false });
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0B0F19] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          <p className="text-sm text-gray-400">Authenticating session...</p>
        </div>
      </div>
    );
  }

  const navItems = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
    { name: 'Video Analysis', path: '/admin/analyze', icon: Video, badge: 'AI' },
    { name: 'Fine Management', path: '/admin/fines', icon: FileText },
    { name: 'Manual Entry', path: '/admin/manual-entry', icon: PlusCircle },
    { name: 'Reports & Audits', path: '/admin/reports', icon: BarChart3 },
    { name: 'Settings & Rules', path: '/admin/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F19] flex flex-col md:flex-row text-gray-200">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex w-64 bg-[#0e1322] border-r border-gray-800/80 flex-col shrink-0">
        {/* Sidebar Header */}
        <div className="p-5 border-b border-gray-800/80 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 p-0.5 shadow-md shadow-indigo-500/20">
              <div className="w-full h-full bg-gray-950 rounded-[10px] flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white font-['Outfit']">TRAFFIC<span className="text-cyan-400">SENSE</span></span>
              <p className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold">Command Console</p>
            </div>
          </Link>
        </div>

        {/* AI Engine Status Pill */}
        <div className="px-5 py-3 border-b border-gray-800/60 bg-gray-900/40">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-gray-400">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              AI Core Status
            </span>
            <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              {healthStatus?.models_loaded ? 'Ready' : 'Online'}
            </span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-3.5 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  active
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white shadow-md shadow-indigo-600/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-gray-400'}`} />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 text-[9px] font-bold bg-cyan-500/20 text-cyan-300 rounded border border-cyan-500/30">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User profile & Logout */}
        <div className="p-4 border-t border-gray-800/80 bg-gray-950/40">
          <div className="flex items-center justify-between mb-3">
            <div className="truncate mr-2">
              <p className="text-xs font-semibold text-white truncate">{admin?.email}</p>
              <p className="text-[10px] text-gray-400">Traffic Authority Admin</p>
            </div>
            <Link to="/" target="_blank" className="text-gray-400 hover:text-cyan-400 p-1" title="View Public Portal">
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-medium rounded-lg bg-gray-900 hover:bg-red-950/50 text-gray-300 hover:text-red-400 border border-gray-800 hover:border-red-800/40 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-4 bg-[#0e1322] border-b border-gray-800">
        <Link to="/" className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-cyan-400" />
          <span className="font-bold text-base text-white">TRAFFIC<span className="text-cyan-400">SENSE</span></span>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 text-gray-400 hover:text-white"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-gray-900 border-b border-gray-800 p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-lg"
            >
              <item.icon className="w-4 h-4 text-indigo-400" />
              <span>{item.name}</span>
            </Link>
          ))}
          <button
            onClick={() => { logout(); setMobileMenuOpen(false); }}
            className="w-full mt-2 flex items-center justify-center gap-2 py-2 text-xs font-medium text-red-400 bg-red-950/30 rounded-lg border border-red-800/40"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
};
