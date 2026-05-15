'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  getHotelAvailability, updateAvailability, getToken, isApiError,
  type RoomAvailability,
} from '../../../lib/api';

const ROOM_TYPES = ['SINGLE', 'DOUBLE', 'TWIN', 'SUITE', 'FAMILY'] as const;

interface RoomTile {
  id: string;
  type: typeof ROOM_TYPES[number];
  available: boolean;
  syncing: boolean;
}

const DATE_LABELS = ['Today', 'Tomorrow', 'Day After'];

export default function AvailabilityPage() {
  const router = useRouter();
  const [selectedDate, setSelectedDate] = useState(0);
  const [rooms, setRooms] = useState<RoomTile[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [toast, setToast] = useState('');
  const hotelId = typeof window !== 'undefined' ? localStorage.getItem('ll_hotel_id') : '';

  const getDemoRooms = useCallback((): RoomTile[] => {
    const types: typeof ROOM_TYPES[number][] = ['SINGLE','SINGLE','SINGLE','SINGLE','DOUBLE','DOUBLE','DOUBLE','SUITE','SUITE','FAMILY'];
    return types.map((t, i) => ({
      id: `room-${i+1}`,
      type: t,
      available: Math.random() > 0.4,
      syncing: false,
    }));
  }, []);

  useEffect(() => {
    if (!getToken()) { router.push('/'); return; }
    setLoading(true);
    // Populate with demo rooms — real implementation would use hotel_id from JWT
    setTimeout(() => { setRooms(getDemoRooms()); setLoading(false); }, 400);
  }, [selectedDate, getDemoRooms, router]);

  const toggleRoom = async (id: string) => {
    setRooms(prev => prev.map(r => r.id === id ? { ...r, syncing: true } : r));
    await new Promise(r => setTimeout(r, 400));
    setRooms(prev => prev.map(r => r.id === id ? { ...r, available: !r.available, syncing: false } : r));
  };

  const syncAll = async () => {
    setSaving(true);
    const avail: RoomAvailability[] = ROOM_TYPES.map(t => ({
      room_type: t,
      available_count: rooms.filter(r => r.type === t && r.available).length,
    }));
    if (hotelId) {
      const res = await updateAvailability(hotelId, avail);
      if (isApiError(res)) { setToast('Sync failed — ' + res.error); setTimeout(() => setToast(''), 3000); }
      else { setSaved(true); setTimeout(() => setSaved(false), 2500); }
    } else {
      setSaved(true); setTimeout(() => setSaved(false), 2500);
    }
    setSaving(false);
  };

  const available = rooms.filter(r => r.available).length;
  const occupied = rooms.length - available;

  const getDateLabel = (offset: number) => {
    const d = new Date(); d.setDate(d.getDate() + offset);
    return d.toLocaleDateString('en-ET', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-1">Room Availability</h1>
        <p className="text-white/50">Tap a room to toggle available / occupied. Sync when done.</p>
      </div>

      {/* Date strip */}
      <div className="flex gap-3 mb-8">
        {DATE_LABELS.map((label, i) => (
          <button key={i} onClick={() => setSelectedDate(i)}
            className={`px-4 py-2 rounded-full text-sm font-bold border transition-all ${selectedDate === i ? 'bg-[#00d4aa] text-[#070b12] border-[#00d4aa]' : 'border-white/20 text-white/60 hover:border-white/40'}`}>
            {label}
            <span className="block text-[10px] font-normal opacity-70">{getDateLabel(i)}</span>
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))' }}>
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="h-20 skeleton rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-3 mb-8" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))' }}>
          {rooms.map(room => (
            <button key={room.id} onClick={() => toggleRoom(room.id)}
              disabled={room.syncing}
              className={`relative h-20 rounded-xl border-2 flex flex-col items-center justify-center gap-1 transition-all hover:scale-[1.03] active:scale-[0.97] ${
                room.available
                  ? 'border-[#00d4aa] bg-[#00d4aa]/10 text-[#00d4aa]'
                  : 'border-red-500/50 bg-red-500/10 text-red-400/60'
              }`}>
              {room.syncing && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-xl">
                  <div className="w-4 h-4 border-2 border-[#00d4aa] border-t-transparent rounded-full animate-spin" />
                </div>
              )}
              <span className="text-lg font-bold">{room.id.split('-')[1]}</span>
              <span className="text-[10px] uppercase tracking-wider">{room.type.substring(0, 3)}</span>
            </button>
          ))}
        </div>
      )}

      {/* Rate section */}
      <div className="bg-white/[0.03] border border-white/10 rounded-xl p-6 mb-6">
        <h3 className="text-sm font-bold text-white/50 uppercase tracking-widest mb-4">Room Rates</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { type: 'SINGLE', rate: '650' },
            { type: 'DOUBLE', rate: '850' },
            { type: 'SUITE', rate: '1,800' },
          ].map(item => (
            <div key={item.type} className="space-y-1">
              <label className="text-xs text-white/40 uppercase">{item.type}</label>
              <div className="flex items-center gap-2">
                <span className="amharic text-[#00d4aa] text-sm">ብር</span>
                <input type="text" defaultValue={item.rate}
                  className="bg-transparent border-b border-white/20 text-white w-24 text-lg font-bold outline-none focus:border-[#00d4aa] pb-1" />
                <span className="text-white/30 text-sm">/night</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary bar */}
      <div className="flex items-center justify-between bg-white/[0.03] border border-white/10 rounded-xl px-6 py-4 mb-6">
        <div className="flex gap-8">
          <div><span className="text-2xl font-bold text-[#00d4aa]">{available}</span><span className="text-white/40 text-sm ml-2">available</span></div>
          <div><span className="text-2xl font-bold text-red-400">{occupied}</span><span className="text-white/40 text-sm ml-2">occupied</span></div>
          <div><span className="text-2xl font-bold">850</span><span className="text-white/40 text-sm ml-1">ETB avg</span></div>
        </div>
        <button onClick={syncAll} disabled={saving}
          className="px-6 py-3 bg-[#00d4aa] text-[#070b12] font-bold rounded-lg hover:scale-[1.02] transition-transform disabled:opacity-50 flex items-center gap-2">
          {saving ? (
            <><div className="w-4 h-4 border-2 border-[#070b12] border-t-transparent rounded-full animate-spin" /> Syncing...</>
          ) : saved ? '✓ Synced' : 'Sync Availability'}
        </button>
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 bg-red-600 text-white px-6 py-3 rounded-full text-sm font-bold shadow-xl z-50">
          {toast}
        </div>
      )}
    </div>
  );
}
