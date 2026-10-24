import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import {
  ShieldCheck, AlertTriangle, Eye, FileText, CheckCircle2,
  ArrowRight, Search, Cpu, Globe, Users, Award, ShieldAlert,
  Zap, Camera, Server, Database, Sparkles
} from 'lucide-react';

export const HomePage: React.FC = () => {
  const [quickPlate, setQuickPlate] = useState('');
  const navigate = useNavigate();

  const handleQuickLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickPlate.trim()) {
      navigate(`/check-fine?plate=${encodeURIComponent(quickPlate.trim().toUpperCase())}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col">
      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-12 pb-20 px-4 lg:px-8 overflow-hidden">
        {/* Ambient Lighting Gradients */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-600/20 via-cyan-500/15 to-transparent blur-3xl pointer-events-none rounded-full"></div>

        <div className="max-w-6xl mx-auto text-center relative z-10">
          {/* Top Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-950/70 border border-indigo-700/50 text-indigo-300 text-xs font-medium mb-6 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI-Driven Intelligent Traffic Enforcement</span>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight font-['Outfit'] leading-tight mb-6 text-white">
            Smart Traffic Violation Detection <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-300 to-indigo-500">
              & Automated Fine Management
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-lg text-gray-400 mb-9 leading-relaxed">
            Eliminating road fatalities through cutting-edge computer vision. Automatically detects motorcycle riders without helmets, recognizes Indian vehicle registration plates, and generates instant e-challans with photographic evidence.
          </p>

          {/* Call to Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-14">
            <Link
              to="/login"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-xl shadow-indigo-600/30 transition-all hover:scale-[1.02]"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Launch Admin Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/check-fine"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl font-semibold text-sm bg-gray-900/90 hover:bg-gray-800 text-gray-200 border border-gray-700/80 transition-all hover:scale-[1.02]"
            >
              <Search className="w-4 h-4 text-cyan-400" />
              <span>Citizen Challan Lookup</span>
            </Link>
          </div>

          {/* Quick License Plate Search Widget */}
          <div className="max-w-lg mx-auto p-2 glass-panel rounded-2xl border border-gray-800 shadow-2xl">
            <form onSubmit={handleQuickLookup} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={quickPlate}
                  onChange={(e) => setQuickPlate(e.target.value.toUpperCase())}
                  placeholder="Enter Vehicle Plate (e.g. DL01AB1234)"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-950/80 border border-gray-800 rounded-xl text-xs sm:text-sm font-mono text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 uppercase tracking-wider"
                />
              </div>
              <button
                type="submit"
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-colors shrink-0"
              >
                Search
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* Problem Statement Section */}
      <section className="py-16 px-4 lg:px-8 border-y border-gray-800/80 bg-gray-950/40 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-950/50 text-red-400 border border-red-800/40 text-xs font-medium mb-3">
              <ShieldAlert className="w-3.5 h-3.5" />
              The Problem We Solve
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold font-['Outfit'] text-white">
              Two-Wheeler Fatality Crisis on Modern Roads
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">High Helmetless Casualties</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Over 44% of fatal road accident victims in India are two-wheeler riders. Over 70% of these riders were not wearing safety helmets at the time of collision.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-4">
                <Eye className="w-5 h-5 text-amber-400" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">Manual Police Bottlenecks</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Physical police checkpoints create traffic congestion, risk officer safety, and capture less than 5% of ongoing violations due to human fatigue and limited field of view.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4">
                <FileText className="w-5 h-5 text-cyan-400" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">Challan Dispute Disputes</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Without timestamped, high-definition visual evidence and automated plate matching, manual fines face rampant legal disputes and non-payment rates above 60%.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works (4 Steps) */}
      <section id="how-it-works" className="py-20 px-4 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-widest">End-to-End Automation</span>
            <h2 className="text-2xl sm:text-3xl font-bold font-['Outfit'] text-white mt-1">
              How Traffic Sense Works in 4 Steps
            </h2>
            <p className="text-sm text-gray-400 mt-2">
              From raw CCTV camera feed ingestion to automated fine collection and audit reports.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Step 1 */}
            <div className="glass-panel glass-panel-hover p-5 rounded-2xl border border-gray-800 relative group">
              <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/50 text-indigo-300 font-bold text-xs flex items-center justify-center mb-4">
                01
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Camera className="w-4 h-4 text-cyan-400" />
                <h3 className="font-semibold text-sm text-white">Video Ingestion</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Traffic video files (MP4, AVI, MOV) are uploaded securely by the enforcement officer and dispatched to the asynchronous background queue.
              </p>
            </div>

            {/* Step 2 */}
            <div className="glass-panel glass-panel-hover p-5 rounded-2xl border border-gray-800 relative group">
              <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 text-cyan-300 font-bold text-xs flex items-center justify-center mb-4">
                02
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-cyan-400" />
                <h3 className="font-semibold text-sm text-white">YOLOv8 & Tracking</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                COCO-pretrained YOLOv8 tracks vehicles and riders frame-by-frame with ByteTrack, assigning unique track IDs to prevent duplicate penalization.
              </p>
            </div>

            {/* Step 3 */}
            <div className="glass-panel glass-panel-hover p-5 rounded-2xl border border-gray-800 relative group">
              <div className="w-8 h-8 rounded-full bg-amber-600/30 border border-amber-500/50 text-amber-300 font-bold text-xs flex items-center justify-center mb-4">
                03
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Eye className="w-4 h-4 text-amber-400" />
                <h3 className="font-semibold text-sm text-white">Helmet & Plate OCR</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Head region is verified for helmet compliance across 3+ frames. High-confidence EasyOCR extracts the vehicle's registration plate with regex normalization.
              </p>
            </div>

            {/* Step 4 */}
            <div className="glass-panel glass-panel-hover p-5 rounded-2xl border border-gray-800 relative group">
              <div className="w-8 h-8 rounded-full bg-emerald-600/30 border border-emerald-500/50 text-emerald-300 font-bold text-xs flex items-center justify-center mb-4">
                04
              </div>
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <h3 className="font-semibold text-sm text-white">E-Challan & Evidence</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                System creates a verified violation with reference ID, stores annotated snapshot evidence, calculates fine according to rules, and updates live reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features List */}
      <section id="features" className="py-16 px-4 lg:px-8 bg-gray-950/40 border-y border-gray-800/80">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-widest">Platform Capabilities</span>
            <h2 className="text-2xl sm:text-3xl font-bold font-['Outfit'] text-white mt-1">
              Engineered for Real-World Road Surveillance
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <Cpu className="w-6 h-6 text-indigo-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">Zero Model Training Required</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Operates entirely on robust pretrained neural weights with CPU optimization. Deployable instantly without expensive GPU clusters.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <Globe className="w-6 h-6 text-cyan-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">Indian Number Plate Format Heuristics</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Features positional character substitution (0/O, 1/I, 5/S, 8/B) and strict standard regex validation (<code className="text-cyan-300 text-[10px]">^[A-Z]{'{2}'}[0-9]{'{2}'}...</code>).
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <ShieldCheck className="w-6 h-6 text-emerald-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">Manual Review Fallback Workflow</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Unreadable or low-confidence plates are highlighted with a "Needs Review" flag, allowing officers to audit, correct, or cancel fines with full transparency.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <FileText className="w-6 h-6 text-purple-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">Official PDF & CSV Audit Exports</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Generate formatted legal enforcement PDF reports with ReportLab and download filtered CSV audits for municipal records.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <Database className="w-6 h-6 text-blue-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">Abstract Storage Service</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Configurable storage layer supporting local filesystem disk for development and Cloudinary / Supabase object storage for cloud production.
              </p>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-gray-800">
              <Users className="w-6 h-6 text-amber-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-2">Citizen Fine Transparency</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Public search portal allowing citizens to look up challans by vehicle plate number, review photo evidence, and settle payments.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SDG 11 Section */}
      <section id="sdg11" className="py-16 px-4 lg:px-8">
        <div className="max-w-5xl mx-auto glass-panel p-8 sm:p-10 rounded-3xl border border-indigo-900/40 relative overflow-hidden">
          <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none"></div>

          <div className="flex flex-col md:flex-row items-center gap-8">
            {/* SDG 11 Official Icon Representation */}
            <div className="w-32 h-32 rounded-2xl bg-amber-600 flex flex-col items-center justify-center p-3 text-white text-center shrink-0 shadow-xl shadow-amber-600/20">
              <span className="text-2xl font-black">11</span>
              <span className="text-[10px] font-bold uppercase tracking-wider leading-tight mt-1">SUSTAINABLE CITIES & COMMUNITIES</span>
            </div>

            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-950/60 text-amber-300 border border-amber-800/40 text-xs font-semibold mb-3">
                <Award className="w-3.5 h-3.5 text-amber-400" />
                United Nations SDG Alignment
              </div>
              <h3 className="text-xl sm:text-2xl font-bold font-['Outfit'] text-white mb-3">
                Advancing UN Sustainable Development Goal 11: Target 11.2
              </h3>
              <p className="text-xs sm:text-sm text-gray-300 leading-relaxed mb-4">
                Target 11.2 aims to <em>"provide access to safe, affordable, accessible and sustainable transport systems for all, improving road safety, notably by expanding public transport, with special attention to the needs of those in vulnerable situations."</em>
              </p>
              <p className="text-xs text-gray-400 leading-relaxed">
                Traffic Sense accelerates smart city adoption by replacing hazardous manual roadside operations with fair, continuous, automated monitoring—substantially reducing head-injury fatalities.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack Banner */}
      <section className="py-12 px-4 lg:px-8 border-t border-gray-800/60 bg-gray-950/60">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-6">Built With Modern Core Technologies</p>
          <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs font-medium text-gray-300">
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gray-900 border border-gray-800">
              <Zap className="w-3.5 h-3.5 text-cyan-400" /> Ultralytics YOLOv8
            </span>
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gray-900 border border-gray-800">
              <Eye className="w-3.5 h-3.5 text-indigo-400" /> EasyOCR English
            </span>
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gray-900 border border-gray-800">
              <Cpu className="w-3.5 h-3.5 text-purple-400" /> PyTorch (CPU-Only)
            </span>
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gray-900 border border-gray-800">
              <Server className="w-3.5 h-3.5 text-emerald-400" /> FastAPI + Uvicorn
            </span>
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gray-900 border border-gray-800">
              <Database className="w-3.5 h-3.5 text-blue-400" /> SQLAlchemy ORM
            </span>
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-gray-900 border border-gray-800">
              <ShieldCheck className="w-3.5 h-3.5 text-yellow-400" /> React 19 + Tailwind CSS
            </span>
          </div>
        </div>
      </section>

      {/* Footer & Team Credits */}
      <footer className="mt-auto py-10 px-4 lg:px-8 border-t border-gray-800/80 bg-gray-950">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-gray-400">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
            <div>
              <p className="font-bold text-white font-['Outfit']">TRAFFIC SENSE</p>
              <p className="text-[11px] text-gray-500">Smart Traffic Violation Detection & Fine Management System</p>
            </div>
          </div>

          {/* Explicit Team Names as specified in PRD requirement F1 */}
          <div className="flex items-center gap-2 bg-gray-900/80 px-4 py-2 rounded-xl border border-gray-800">
            <Users className="w-4 h-4 text-cyan-400" />
            <span className="text-gray-300">Project Developed by:</span>
            <span className="font-semibold text-white">Chitra S</span>
            <span className="text-gray-600">&bull;</span>
            <span className="font-semibold text-white">Linsha LJ</span>
          </div>

          <div className="text-center sm:text-right text-[11px] text-gray-500">
            &copy; 2026 Traffic Sense Enforcement. All Rights Reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};
