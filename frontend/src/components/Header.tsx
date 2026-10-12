import React, { useEffect, useState } from 'react';
import { Globe, Shield, User, RefreshCw } from 'lucide-react';
import { UserProfile } from '../types';

interface HeaderProps {
  user: UserProfile | null;
  onRoleChange: (role: 'viewer' | 'analyst' | 'admin') => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onRoleChange,
  onRefresh,
  isRefreshing,
}) => {
  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().slice(17, 25) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between text-slate-100 select-none">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-sky-500/10 border border-sky-500/30 rounded-lg text-sky-400">
          <Globe className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-wider text-sky-300">AXIOM STUDIO</span>
            <span className="text-xs px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-400 font-mono">
              v1.0.0
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Photorealistic Spatial Intelligence & Trajectory Anomaly ML Engine
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden md:flex items-center space-x-2 px-3 py-1 bg-slate-950 border border-slate-800 rounded font-mono text-xs text-slate-300">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span>LIVE TRACK: {utcTime}</span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition flex items-center space-x-1 text-xs"
          title="Refresh spatial telemetry"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Sync</span>
        </button>

        {user && (
          <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
            <Shield className="w-4 h-4 text-sky-400" />
            <div className="text-xs">
              <span className="text-slate-400">Role: </span>
              <select
                value={user.roles[0] || 'viewer'}
                onChange={(e) => onRoleChange(e.target.value as any)}
                className="bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-xs text-sky-300 font-medium focus:outline-none"
              >
                <option value="viewer">Viewer (Read-only)</option>
                <option value="analyst">Analyst (Operator)</option>
                <option value="admin">Admin (Full Control)</option>
              </select>
            </div>
            <div className="flex items-center space-x-1 pl-2 border-l border-slate-700 text-xs text-slate-300">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span>{user.username}</span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
