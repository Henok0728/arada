'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginHotel, isApiError } from '../lib/api';

export default function DemoBanner() {
  const [loading, setLoading] = useState<string | null>(null);
  const router = useRouter();

  const handlePartnerLogin = async (hotelType: 'A' | 'B') => {
    setLoading(hotelType);
    const email = hotelType === 'A'
      ? 'hotel_a@demo.lodge-link.et'
      : 'hotel_b@demo.lodge-link.et';

    // Internal Demo Bypass for Judges
    const res = await loginHotel(email, 'DemoLodge2025');

    if (isApiError(res)) {
      setLoading(null);
      return;
    }

    localStorage.setItem('ll_hotel_type', hotelType);
    localStorage.setItem('ll_hotel_id',
      hotelType === 'A'
        ? '11111111-1111-1111-1111-111111111111'
        : '22222222-2222-2222-2222-222222222222'
    );
    router.push('/dashboard');
    setLoading(null);
  };

  return (
    <div className="sticky top-0 z-[100] bg-white/5 backdrop-blur-md border-b border-white/10 py-2 px-6 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="flex h-3 w-3 rounded-full bg-[#00d4aa] animate-pulse shadow-[0_0_15px_rgba(0,212,170,0.5)]" />
        <div>
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#00d4aa]">Judge Demo Mode</span>
          <div className="text-[8px] font-bold text-white/30 uppercase tracking-widest mt-0.5">Simulated Production Environment</div>
        </div>
      </div>
      
      <div className="flex gap-3">
        <div className="hidden lg:flex items-center text-[10px] font-black text-white/20 uppercase tracking-widest mr-4">
          Switch Hotel Perspective:
        </div>
        <button
          onClick={() => handlePartnerLogin('A')}
          disabled={!!loading}
          className={`px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${loading === 'A' ? 'bg-[#00d4aa] text-[#070b12]' : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10 hover:text-white'}`}
        >
          {loading === 'A' ? 'Authorizing...' : '🏨 Bole Skyline (A)'}
        </button>
        <button
          onClick={() => handlePartnerLogin('B')}
          disabled={!!loading}
          className={`px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${loading === 'B' ? 'bg-[#00d4aa] text-[#070b12]' : 'bg-white/5 border border-white/10 text-white/60 hover:bg-white/10 hover:text-white'}`}
        >
          {loading === 'B' ? 'Authorizing...' : '🏨 Entoto View (B)'}
        </button>
      </div>
    </div>
  );
}
