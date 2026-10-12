import React, { useEffect, useRef, useState } from 'react';
import { CameraPose, SpatialEntity } from '../types';
import { Layers, ZoomIn, ZoomOut, RotateCw, Cpu } from 'lucide-react';

interface GlobeViewProps {
  entities: SpatialEntity[];
  selectedEntity: SpatialEntity | null;
  onSelectEntity: (entity: SpatialEntity) => void;
  camera: CameraPose;
  onCameraChange: (camera: CameraPose) => void;
  activeLayers: string[];
  onToggleLayer: (layer: string) => void;
}

export const GlobeView: React.FC<GlobeViewProps> = ({
  entities,
  selectedEntity,
  onSelectEntity,
  camera,
  onCameraChange,
  activeLayers,
  onToggleLayer,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [lowPowerMode, setLowPowerMode] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width, h = canvas.height;
    const radius = Math.min(w, h) * 0.42 * (1000.0 / Math.max(camera.altitude, 200.0));
    const cx = w / 2, cy = h / 2;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#030712';
    ctx.fillRect(0, 0, w, h);

    if (!lowPowerMode) {
      const glow = ctx.createRadialGradient(cx, cy, radius * 0.9, cx, cy, radius * 1.15);
      glow.addColorStop(0, 'rgba(56, 189, 248, 0.25)');
      glow.addColorStop(1, 'rgba(56, 189, 248, 0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.15, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.fillStyle = '#082f49';
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.strokeStyle = 'rgba(56, 189, 248, 0.15)';
    ctx.lineWidth = 1;
    for (let lat = -60; lat <= 60; lat += 30) {
      const y = cy - (lat / 90.0) * radius;
      const lr = Math.sqrt(Math.max(0, radius * radius - Math.pow((lat / 90.0) * radius, 2)));
      ctx.beginPath();
      ctx.ellipse(cx, y, lr, lr * 0.2, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    for (let lon = -180; lon < 180; lon += 45) {
      const rad = ((lon - camera.longitude) * Math.PI) / 180.0;
      if (Math.cos(rad) > 0) {
        ctx.beginPath();
        ctx.ellipse(cx, cy, Math.abs(Math.sin(rad) * radius), radius, 0, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    entities.forEach((ent) => {
      const lonR = ((ent.longitude - camera.longitude) * Math.PI) / 180.0;
      const latR = ((ent.latitude - camera.latitude) * Math.PI) / 180.0;
      if (Math.cos(lonR) * Math.cos(latR) <= 0 && camera.altitude < 5000) return;

      const px = cx + Math.sin(lonR) * Math.cos(ent.latitude * Math.PI / 180) * radius;
      const py = cy - Math.sin(latR) * radius;
      if (px < 0 || px > w || py < 0 || py > h) return;

      const isSel = selectedEntity?.id === ent.id;
      let color = '#38bdf8';
      if (ent.entity_type === 'aircraft') color = '#34d399';
      if (ent.entity_type === 'rf_station') color = '#a78bfa';
      if (ent.entity_type === 'camera') color = '#fb923c';
      if (isSel) color = '#facc15';

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(px, py, isSel ? 6 : 4, 0, Math.PI * 2);
      ctx.fill();

      if (ent.entity_type === 'aircraft' && ent.heading) {
        const hr = ((ent.heading - 90) * Math.PI) / 180.0;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(px + Math.cos(hr) * 10, py + Math.sin(hr) * 10);
        ctx.stroke();
      }

      ctx.font = '10px monospace';
      ctx.fillStyle = isSel ? '#facc15' : 'rgba(226, 232, 240, 0.8)';
      ctx.fillText(ent.callsign, px + 6, py - 3);
    });
  }, [entities, selectedEntity, camera, lowPowerMode]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const cx = ((e.clientX - rect.left) / rect.width) * canvas.width;
    const cy = ((e.clientY - rect.top) / rect.height) * canvas.height;
    const w = canvas.width, h = canvas.height;
    const radius = Math.min(w, h) * 0.42 * (1000.0 / Math.max(camera.altitude, 200.0));

    for (const ent of entities) {
      const lonR = ((ent.longitude - camera.longitude) * Math.PI) / 180.0;
      const px = w / 2 + Math.sin(lonR) * Math.cos(ent.latitude * Math.PI / 180) * radius;
      const py = h / 2 - Math.sin(((ent.latitude - camera.latitude) * Math.PI) / 180) * radius;
      if (Math.hypot(cx - px, cy - py) < 15) {
        onSelectEntity(ent);
        return;
      }
    }
  };

  const handleZoom = (inward: boolean) => {
    const factor = inward ? 0.75 : 1.35;
    onCameraChange({ ...camera, altitude: Math.max(100, Math.min(20000, camera.altitude * factor)) });
  };

  return (
    <div className="relative w-full h-full bg-slate-950 flex flex-col overflow-hidden border border-slate-800 rounded-xl">
      <div className="absolute top-3 left-3 z-10 flex flex-wrap gap-2 text-xs font-mono">
        <div className="bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
          <span>{camera.latitude.toFixed(2)}°N, {camera.longitude.toFixed(2)}°E | {camera.altitude.toFixed(0)}km</span>
        </div>
        <button
          onClick={() => setLowPowerMode(!lowPowerMode)}
          className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg border ${
            lowPowerMode ? 'bg-amber-950 border-amber-700 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-400'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>{lowPowerMode ? 'Low-Spec' : 'Hi-Fi'}</span>
        </button>
      </div>

      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1.5">
        <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800 text-xs">
          <div className="flex items-center space-x-1 text-slate-400 mb-1">
            <Layers className="w-3 h-3" /><span>Layers</span>
          </div>
          {['satellites', 'aircraft', 'rf_stations', 'cameras'].map((l) => (
            <button
              key={l}
              onClick={() => onToggleLayer(l)}
              className={`block w-full text-left px-2 py-0.5 rounded text-[11px] ${
                activeLayers.includes(l) ? 'text-sky-300 bg-slate-800' : 'text-slate-500'
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        <div className="bg-slate-900/90 p-1 rounded-lg border border-slate-800 flex flex-col gap-1">
          <button onClick={() => handleZoom(true)} className="p-1 text-slate-300"><ZoomIn className="w-4 h-4" /></button>
          <button onClick={() => handleZoom(false)} className="p-1 text-slate-300"><ZoomOut className="w-4 h-4" /></button>
          <button onClick={() => onCameraChange({ latitude: 20, longitude: 0, altitude: 1000, heading: 0, pitch: -45 })} className="p-1 text-slate-300"><RotateCw className="w-4 h-4" /></button>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        width={960}
        height={600}
        onClick={handleCanvasClick}
        onMouseDown={(e) => { setIsDragging(true); setDragStart({ x: e.clientX, y: e.clientY }); }}
        onMouseMove={(e) => {
          if (!isDragging) return;
          const dx = e.clientX - dragStart.x, dy = e.clientY - dragStart.y;
          setDragStart({ x: e.clientX, y: e.clientY });
          onCameraChange({
            ...camera,
            longitude: parseFloat((((camera.longitude - dx * 0.2 + 180) % 360) - 180).toFixed(4)),
            latitude: parseFloat(Math.max(-85, Math.min(85, camera.latitude + dy * 0.2)).toFixed(4)),
          });
        }}
        onMouseUp={() => setIsDragging(false)}
        className="w-full h-full cursor-grab active:cursor-grabbing block"
      />
    </div>
  );
};
