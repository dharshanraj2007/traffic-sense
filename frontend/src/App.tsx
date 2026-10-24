import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { HomePage } from './pages/HomePage';
import { CheckFinePage } from './pages/CheckFinePage';
import { LoginPage } from './pages/LoginPage';
import { AdminLayout } from './components/AdminLayout';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyzeVideoPage } from './pages/AnalyzeVideoPage';
import { FinesPage } from './pages/FinesPage';
import { ManualEntryPage } from './pages/ManualEntryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Citizen Pages */}
          <Route path="/" element={<HomePage />} />
          <Route path="/check-fine" element={<CheckFinePage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Admin Console */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="analyze" element={<AnalyzeVideoPage />} />
            <Route path="fines" element={<FinesPage />} />
            <Route path="manual-entry" element={<ManualEntryPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
