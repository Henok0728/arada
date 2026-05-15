'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginHotel, isApiError, setToken } from '../lib/api';

export default function DemoBanner() {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleDemoLogin = async (hotelType: 'A' | 'B') => {
    setLoading(hotelType);
    setError('');
    const email = hotelType === 'A'
      ? 'hotel_a@demo.lodge-link.et'
      : 'hotel_b@demo.lodge-link.et';

    const res = await loginHotel(email, 'DemoLodge2025');

    if (isApiError(res)) {
      setError(res.error);
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
    <div className="sticky top-0 z-[100] bg-[#00d4aa] text-[#070b12] py-2 px-4 flex flex-wrap items-center justify-between gap-4 shadow-lg border-b border-white/20">
      <div className="flex items-center gap-2 font-bold text-sm md:text-base">
        <span className="bg-[#070b12] text-white px-2 py-0.5 rounded text-xs">DEMO</span>
        <span>Password: <code className="bg-white/20 px-1 rounded">DemoLodge2025</code></span>
        {error && <span className="text-red-800 text-xs ml-2">{error}</span>}
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => handleDemoLogin('A')}
          disabled={!!loading}
          className="bg-[#070b12] text-white px-3 py-1 rounded text-sm font-bold hover:bg-[#1a2433] transition-colors disabled:opacity-50"
        >
          {loading === 'A' ? 'Logging in...' : '🏨 Hotel A Login'}
        </button>
        <button
          onClick={() => handleDemoLogin('B')}
          disabled={!!loading}
          className="bg-white text-[#070b12] px-3 py-1 rounded text-sm font-bold hover:bg-gray-100 transition-colors disabled:opacity-50"
        >
          {loading === 'B' ? 'Logging in...' : '🏨 Hotel B Login'}
        </button>
      </div>
    </div>
  );
}
