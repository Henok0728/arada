'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AdminDashboard() {
  const [hotels, setHotels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchHotels = async () => {
    try {
      const res = await fetch('https://arada-production.up.railway.app/v1/admin/hotels');
      if (!res.ok) throw new Error('Failed to fetch hotels');
      const data = await res.json();
      setHotels(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHotels();
  }, []);

  const verifyHotel = async (id: string, approve: boolean) => {
    try {
      const res = await fetch(`https://arada-production.up.railway.app/v1/admin/hotels/${id}/verify?approve=${approve}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Failed to update status');
      fetchHotels();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div className="min-h-screen bg-[#070b12] text-white p-20 text-center font-black">ACCESSING SYSTEM RECORDS...</div>;

  return (
    <div className="min-h-screen bg-[#070b12] text-white p-8 md:p-20">
      <div className="max-w-6xl mx-auto">
        <div className="mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/30 text-red-500 text-[10px] font-black uppercase tracking-widest mb-4">
            System Admin Terminal
          </div>
          <h1 className="text-5xl font-black tracking-tighter mb-4 italic">Network Oversight</h1>
          <p className="text-white/40 text-lg">Process incoming hotel verification requests and manage node status.</p>
        </div>

        <div className="grid gap-6">
          {hotels.map(hotel => (
            <div key={hotel.id} className="bg-white/[0.03] border border-white/5 rounded-[2.5rem] p-10 backdrop-blur-xl flex flex-col md:flex-row justify-between items-center gap-8">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-2">
                  <h2 className="text-2xl font-black tracking-tight">{hotel.name}</h2>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest ${
                    hotel.status === 'ACTIVE' ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 
                    hotel.status === 'PENDING_KYC' ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500'
                  }`}>
                    {hotel.status}
                  </span>
                </div>
                <div className="text-white/40 text-sm font-bold uppercase tracking-widest">{hotel.city} · {hotel.email}</div>
                <div className="mt-6 flex gap-4">
                  <div className="p-4 bg-black/20 rounded-2xl border border-white/5">
                    <div className="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">TIN CERTIFICATE</div>
                    <div className="text-xs text-[#00d4aa] font-bold">✓ ATTACHED</div>
                  </div>
                  <div className="p-4 bg-black/20 rounded-2xl border border-white/5">
                    <div className="text-[8px] font-black text-white/20 uppercase tracking-widest mb-1">LICENSE</div>
                    <div className="text-xs text-[#00d4aa] font-bold">✓ ATTACHED</div>
                  </div>
                </div>
              </div>

              <div className="flex gap-4 w-full md:w-auto">
                <button 
                  onClick={() => verifyHotel(hotel.id, true)}
                  className="flex-1 md:flex-none px-12 py-5 bg-[#00d4aa] text-[#070b12] font-black text-xs uppercase tracking-widest rounded-2xl hover:scale-105 transition-all"
                >
                  Approve Node
                </button>
                <button 
                  onClick={() => verifyHotel(hotel.id, false)}
                  className="flex-1 md:flex-none px-12 py-5 bg-white/5 border border-white/10 text-white font-black text-xs uppercase tracking-widest rounded-2xl hover:bg-white/10 transition-all"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
