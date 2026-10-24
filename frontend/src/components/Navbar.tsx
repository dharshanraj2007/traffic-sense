import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShieldCheck, Search, Lock, Activity } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-gray-800/80 px-4 lg:px-8 py-3.5 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-gray-950 rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-white font-['Outfit']">TRAFFIC<span className="text-cyan-400">SENSE</span></span>
              <span className="px-1.5 py-0.5 text-[10px] font-semibold tracking-wider uppercase bg-indigo-900/60 text-indigo-300 rounded border border-indigo-700/50">AI</span>
            </div>
            <p className="text-[11px] text-gray-400 leading-none">Automated Traffic Enforcement</p>
          </div>
        </Link>

        {/* Center Navigation Links */}
        <div className="hidden md:flex items-center gap-1 bg-gray-900/80 p-1 rounded-xl border border-gray-800">
          <Link
            to="/"
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              isActive('/') ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Overview
          </Link>
          <a
            href="#how-it-works"
            className="px-3.5 py-1.5 text-xs font-medium text-gray-400 hover:text-gray-200 transition-colors"
          >
            How It Works
          </a>
          <a
            href="#features"
            className="px-3.5 py-1.5 text-xs font-medium text-gray-400 hover:text-gray-200 transition-colors"
          >
            Features
          </a>
          <a
            href="#sdg11"
            className="px-3.5 py-1.5 text-xs font-medium text-gray-400 hover:text-gray-200 transition-colors"
          >
            SDG 11
          </a>
          <Link
            to="/check-fine"
            className={`px-3.5 py-1.5 text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors ${
              isActive('/check-fine') ? 'bg-indigo-600 text-white' : 'text-cyan-400 hover:text-cyan-300'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            Check My Fine
          </Link>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <Link
            to="/check-fine"
            className="md:hidden p-2 rounded-lg bg-gray-900 border border-gray-800 text-cyan-400 hover:bg-gray-800 transition-colors"
            title="Check Fine"
          >
            <Search className="w-4 h-4" />
          </Link>
          <Link
            to="/login"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-md shadow-indigo-600/30 transition-all hover:shadow-indigo-600/50"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Admin Portal</span>
          </Link>
        </div>
      </div>
    </nav>
  );
};
