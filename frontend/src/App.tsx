import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { GlobeView } from './components/GlobeView';
import { BookmarksTray } from './components/BookmarksTray';
import { TelemetryPanel } from './components/TelemetryPanel';
import { AnomalyConsole } from './components/AnomalyConsole';
import { MacroAssistant } from './components/MacroAssistant';
import { api } from './services/api';
import { authService } from './services/auth';
import {
  AnomalyScore,
  Bookmark,
  CameraPose,
  MacroCandidate,
  MLBenchmarkResponse,
  SpatialEntity,
  UserProfile,
  WorkflowMacro,
} from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [entities, setEntities] = useState<SpatialEntity[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<SpatialEntity | null>(null);
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyScore[]>([]);
  const [benchmark, setBenchmark] = useState<MLBenchmarkResponse | null>(null);
  const [candidates, setCandidates] = useState<MacroCandidate[]>([]);
  const [macros, setMacros] = useState<WorkflowMacro[]>([]);
  const [activeLayers, setActiveLayers] = useState<string[]>(['satellites', 'aircraft', 'rf_stations', 'cameras']);
  const [camera, setCamera] = useState<CameraPose>({ latitude: 25.0, longitude: 10.0, altitude: 1200.0, heading: 0.0, pitch: -45.0 });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setIsLoading(true);
        await authService.loginDemo('analyst');
        setUser(authService.getCurrentUser());
        await loadData();
      } catch (err: any) {
        setErrorMessage(err.message || 'Initialization error');
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [ents, bms, mcs, bench] = await Promise.all([
        api.getEntities({ layers: activeLayers }),
        api.getBookmarks(),
        api.getMacros(),
        api.getMLBenchmark(),
      ]);
      setEntities(ents);
      setBookmarks(bms);
      setMacros(mcs);
      setBenchmark(bench);
      const cands = await api.getMacroCandidates(1).catch(() => []);
      setCandidates(cands);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to refresh telemetry');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRoleChange = async (role: 'viewer' | 'analyst' | 'admin') => {
    try {
      await authService.loginDemo(role);
      setUser(authService.getCurrentUser());
      await loadData();
    } catch (err: any) {
      setErrorMessage(err.message || 'Role change failed');
    }
  };

  const handleToggleLayer = (layer: string) => {
    const updated = activeLayers.includes(layer) ? activeLayers.filter((l) => l !== layer) : [...activeLayers, layer];
    setActiveLayers(updated);
    api.recordActionReceipt({ session_id: 'session-main', context_fingerprint: 'viewport-layers', action_name: 'toggle_layer', args: { layer }, result_status: 'success', duration_ms: 12.0 }).catch(() => {});
  };

  const handleSaveBookmark = async (name: string) => {
    const nb = await api.createBookmark({ name, latitude: camera.latitude, longitude: camera.longitude, altitude: camera.altitude, heading: camera.heading, pitch: camera.pitch, active_layers: activeLayers });
    setBookmarks([nb, ...bookmarks]);
    api.recordActionReceipt({ session_id: 'session-main', context_fingerprint: 'favourite-bookmarks', action_name: 'fly_to_bookmark', args: { bookmark_id: nb.id, name }, result_status: 'success', duration_ms: 25.0 }).catch(() => {});
  };

  const handleSelectBookmark = (b: Bookmark) => {
    setCamera({ latitude: b.latitude, longitude: b.longitude, altitude: b.altitude, heading: b.heading, pitch: b.pitch });
    if (b.active_layers?.length) setActiveLayers(b.active_layers);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300 font-mono">
        <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-sm">INITIALIZING AXIOM SPATIAL ENGINE...</p>
      </div>
    );
  }

  const canEdit = authService.hasRole('analyst') || authService.hasRole('admin');

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col text-slate-100 font-sans">
      <Header user={user} onRoleChange={handleRoleChange} onRefresh={loadData} isRefreshing={isRefreshing} />
      {errorMessage && (
        <div className="bg-rose-950 border-b border-rose-800 text-rose-200 px-6 py-2 text-xs font-mono flex justify-between">
          <span>SYSTEM ERROR: {errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="underline text-xs">Dismiss</button>
        </div>
      )}
      <main className="flex-1 p-4 grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-7 flex flex-col gap-4">
          <div className="flex-1 min-h-[460px] h-full">
            <GlobeView entities={entities} selectedEntity={selectedEntity} onSelectEntity={setSelectedEntity} camera={camera} onCameraChange={setCamera} activeLayers={activeLayers} onToggleLayer={handleToggleLayer} />
          </div>
          <BookmarksTray bookmarks={bookmarks} onSelectBookmark={handleSelectBookmark} onSaveBookmark={handleSaveBookmark} onDeleteBookmark={async (id) => { await api.deleteBookmark(id); setBookmarks(bookmarks.filter((b) => b.id !== id)); }} canSave={canEdit} />
        </div>
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="min-h-[220px]">
            <TelemetryPanel entity={selectedEntity} onClose={() => setSelectedEntity(null)} onFocusEntity={(e) => setCamera({ ...camera, latitude: e.latitude, longitude: e.longitude, altitude: Math.min(camera.altitude, 1500) })} />
          </div>
          <div className="min-h-[240px]">
            <AnomalyConsole anomalies={anomalies} benchmark={benchmark} onRunScan={async () => { setIsScanning(true); try { setAnomalies(await api.detectAnomalies(0.65)); } finally { setIsScanning(false); } }} onRunBenchmark={async () => setBenchmark(await api.getMLBenchmark(0.65))} isScanning={isScanning} canScan={canEdit} />
          </div>
          <div className="min-h-[240px]">
            <MacroAssistant candidates={candidates} macros={macros} onConfirmMacro={async (c) => { const m = await api.confirmMacro(c.suggested_name, 'Compiled shortcut', c.context_fingerprint, c.actions); setMacros([m, ...macros]); setCandidates(candidates.filter((x) => x.suggested_name !== c.suggested_name)); }} onExecuteMacro={async (id) => { const res = await api.executeMacro(id); if (!res.success && res.demoted) setMacros(await api.getMacros()); }} onAskAdvisory={(q) => api.requestAdvisory(q)} canManage={canEdit} />
          </div>
        </div>
      </main>
    </div>
  );
};
