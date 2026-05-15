'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DemoBanner() {
  const [loading, setLoading] = useState<string | null>(null);
  const router = useRouter();

  const handleDemoLogin = async (hotelType: 'A' | 'B') => {
    setLoading(hotelType);
    try {
      const hotelId = hotelType === 'A' 
        ? '00000000-0000-0000-0000-00000000000a' 
        : '00000000-0000-0000-0000-00000000000b';

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hotel_id: hotelId,
          password: 'DemoLodge2025'
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('ll_token', data.access_token);
        localStorage.setItem('ll_hotel_type', hotelType);
        router.push('/dashboard');
      } else {
        console.error('Demo login failed');
      }
    } catch (err) {
      console.error('Demo login error:', err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="sticky top-0 z-[100] bg-[#00d4aa] text-[#070b12] py-2 px-4 flex flex-wrap items-center justify-between gap-4 shadow-lg border-b border-white/20">
      <div className="flex items-center gap-2 font-bold text-sm md:text-base">
        <span className="bg-[#070b12] text-white px-2 py-0.5 rounded text-xs">DEMO</span>
        <span>Password: <code className="bg-white/20 px-1 rounded">DemoLodge2025</code></span>
      </div>
      <div className="flex gap-2">
        <button 
          onClick={() => handleDemoLogin('A')}
          disabled={!!loading}
          className="bg-[#070b12] text-white px-3 py-1 rounded text-sm font-bold hover:bg-[#1a2433] transition-colors disabled:opacity-50"
        >
          {loading === 'A' ? 'Logging in...' : 'Hotel A Login'}
        </button>
        <button 
          onClick={() => handleDemoLogin('B')}
          disabled={!!loading}
          className="bg-white text-[#070b12] px-3 py-1 rounded text-sm font-bold hover:bg-gray-100 transition-colors disabled:opacity-50"
        >
          {loading === 'B' ? 'Logging in...' : 'Hotel B Login'}
        </button>
      </div>
    </div>
  );
}
