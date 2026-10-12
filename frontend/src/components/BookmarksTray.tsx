import React, { useState } from 'react';
import { Bookmark } from '../types';
import { Bookmark as BookmarkIcon, Plus, Trash2, MapPin } from 'lucide-react';

interface BookmarksTrayProps {
  bookmarks: Bookmark[];
  onSelectBookmark: (bookmark: Bookmark) => void;
  onSaveBookmark: (name: string) => Promise<void>;
  onDeleteBookmark: (id: string) => Promise<void>;
  canSave: boolean;
}

export const BookmarksTray: React.FC<BookmarksTrayProps> = ({
  bookmarks,
  onSelectBookmark,
  onSaveBookmark,
  onDeleteBookmark,
  canSave,
}) => {
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [newBookmarkName, setNewBookmarkName] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBookmarkName.trim()) return;
    setErrorMsg(null);
    try {
      await onSaveBookmark(newBookmarkName.trim());
      setNewBookmarkName('');
      setIsSaving(false);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save favourite location');
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-3 shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 text-slate-200">
          <BookmarkIcon className="w-4 h-4 text-sky-400" />
          <h2 className="text-sm font-semibold tracking-wide">FAVOURITE LOCATIONS (ISSUE #335)</h2>
        </div>
        {canSave && !isSaving && (
          <button
            onClick={() => setIsSaving(true)}
            className="flex items-center space-x-1 px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-medium transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Bookmark View</span>
          </button>
        )}
      </div>

      {isSaving && (
        <form onSubmit={handleSave} className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex flex-col gap-2">
          <label className="text-xs text-slate-400">Save current camera position as favourite:</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newBookmarkName}
              onChange={(e) => setNewBookmarkName(e.target.value)}
              placeholder="e.g. Austin Downtown Hub, Brenner Corridor"
              className="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-100 focus:outline-none focus:border-sky-500 font-mono"
              autoFocus
            />
            <button
              type="submit"
              disabled={!newBookmarkName.trim()}
              className="px-3 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded text-xs font-medium transition"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => {
                setIsSaving(false);
                setErrorMsg(null);
              }}
              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition"
            >
              Cancel
            </button>
          </div>
          {errorMsg && <p className="text-xs text-rose-400 font-mono">{errorMsg}</p>}
        </form>
      )}

      {/* Bookmarks pills list */}
      <div className="flex flex-wrap gap-2">
        {bookmarks.length === 0 ? (
          <div className="w-full py-3 text-center text-xs text-slate-500 font-mono">
            No saved favourite locations yet. Position the globe and click 'Bookmark View'.
          </div>
        ) : (
          bookmarks.map((b) => (
            <div
              key={b.id}
              className="group flex items-center space-x-1 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 rounded-lg text-xs transition shadow-sm"
            >
              <button
                onClick={() => onSelectBookmark(b)}
                className="flex items-center space-x-1.5 text-slate-200 hover:text-sky-300"
                title={`Fly to ${b.name} (${b.latitude.toFixed(2)}°, ${b.longitude.toFixed(2)}°)`}
              >
                <MapPin className="w-3.5 h-3.5 text-sky-400" />
                <span className="font-medium">{b.name}</span>
                <span className="text-slate-500 font-mono text-[10px]">
                  ({b.latitude.toFixed(1)}°, {b.longitude.toFixed(1)}°)
                </span>
              </button>

              {canSave && (
                <button
                  onClick={() => onDeleteBookmark(b.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition"
                  title="Delete bookmark"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
