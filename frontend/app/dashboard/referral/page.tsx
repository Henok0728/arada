'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createReferral, isApiError, getToken } from '../../../lib/api';

type Step = 'room_type' | 'duration' | 'loading' | 'results' | 'confirmation';

interface HotelResult {
  id: string;
  display_name: string;
  display_name_am: string;
  distance_km: number;
  trust_score: number;
  room_type: string;
  price_etb: number;
}

export default function EmergencyReferralPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('room_type');
  const [selection, setSelection] = useState({
    roomType: 'DOUBLE',
    duration: '1'
  });
  const [results, setResults] = useState<HotelResult[]>([]);
  const [handshakeCode, setHandshakeCode] = useState('');
  const [selectedHotel, setSelectedHotel] = useState<HotelResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!getToken()) { router.push('/'); }
  }, [router]);

  const handleRoomType = (type: string) => {
    setSelection(prev => ({ ...prev, roomType: type }));
    setStep('duration');
  };

  const handleDuration = (duration: string) => {
    setSelection(prev => ({ ...prev, duration: duration }));
    setStep('loading');
    startSearch();
  };

  const startSearch = async () => {
    // Simulated search for partners in range
    setTimeout(() => {
      const mockResults: HotelResult[] = [
        { 
          id: '22222222-2222-2222-2222-222222222222', 
          display_name: 'Entoto View Lodge', 
          display_name_am: 'የእንጦጦ ቪው ሎጅ', 
          distance_km: 0.3, 
          trust_score: 92, 
          room_type: selection.roomType, 
          price_etb: 1250 
        },
        { 
          id: '44444444-4444-4444-4444-444444444444', 
          display_name: 'Kazanchis Business Hotel', 
          display_name_am: 'ካዛንቺስ ቢዝነስ ሆቴል', 
          distance_km: 1.1, 
          trust_score: 81, 
          room_type: selection.roomType, 
          price_etb: 850 
        },
        { 
          id: '55555555-5555-5555-5555-555555555555', 
          display_name: 'Megenagna Grand Hotel', 
          display_name_am: 'መገናኛ ግራንድ ሆቴል', 
          distance_km: 2.4, 
          trust_score: 95, 
          room_type: selection.roomType, 
          price_etb: 1400 
        }
      ];
      setResults(mockResults);
      setStep('results');
    }, 1200);
  };

  const handleRefer = async (hotel: HotelResult) => {
    setStep('loading');
    setSelectedHotel(hotel);
    setError('');

    const originHotelId = localStorage.getItem('ll_hotel_id');
    
    if (!originHotelId) {
      setError('Auth error: No origin hotel ID found.');
      setStep('results');
      return;
    }

    // REAL BACKEND CALL to trigger the referral session
    const res = await createReferral({
      origin_hotel_id: originHotelId,
      guest_name: 'Demo Guest',
      guest_phone: '+251911223344',
      room_type: selection.roomType,
      party_size: 1,
      check_in_date: new Date().toISOString().split('T')[0],
      check_out_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
      origin_longitude: 38.7578,
      origin_latitude: 9.0192,
      radius_metres: 5000,
      // We target the specific hotel in the demo for 100% success
      special_requests: `AUTO_TARGET:${hotel.id}` 
    });

    if (isApiError(res)) {
      setError(res.error);
      setStep('results');
      return;
    }

    // The backend should return a session, but for the "Handshake Code" 
    // we show a confirmation. In a real fan-out, we'd wait for accept.
    // Since this is a demo, we'll assume the session was initiated.
    setHandshakeCode('LX-' + Math.random().toString(36).substring(2, 6).toUpperCase());
    setStep('confirmation');
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-white flex flex-col items-center pt-12 px-6 pb-20">
      <div className="fixed inset-0 z-0 pointer-events-none opacity-10">
        <div className="absolute top-[20%] right-[10%] w-[40%] h-[40%] bg-[#00d4aa] rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-2xl relative z-10">
        <div className="mb-12">
          <h1 className="text-4xl font-black tracking-tighter mb-2 italic">Emergency Referral</h1>
          <p className="text-white/40 text-sm tracking-widest uppercase font-bold">Protocol v1.2 · Instant Placement</p>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-500 p-4 rounded-2xl mb-8 text-sm font-bold">
            ⚠️ {error}
          </div>
        )}

        {/* STEP 1: ROOM TYPE */}
        {step === 'room_type' && (
          <div className="space-y-6 animate-fade-up">
            <label className="text-xs font-black text-[#00d4aa] uppercase tracking-[0.3em]">Step 01 / Select Inventory</label>
            <div className="grid grid-cols-1 gap-4">
              {[
                { id: 'SINGLE', name: 'Single Room', icon: '👤' },
                { id: 'DOUBLE', name: 'Double Room', icon: '👥' },
                { id: 'SUITE', name: 'Executive Suite', icon: '👑' }
              ].map(t => (
                <button
                  key={t.id}
                  onClick={() => handleRoomType(t.id)}
                  className="group w-full p-8 bg-white/5 border border-white/10 rounded-3xl hover:border-[#00d4aa] hover:bg-white/10 transition-all text-left flex items-center justify-between"
                >
                  <div className="flex items-center gap-6">
                    <span className="text-3xl grayscale group-hover:grayscale-0 transition-all">{t.icon}</span>
                    <div>
                      <div className="text-xl font-bold tracking-tight">{t.name}</div>
                      <div className="text-xs text-white/30 uppercase tracking-widest font-bold mt-1">Guaranteed Availability</div>
                    </div>
                  </div>
                  <div className="h-10 w-10 rounded-full border border-white/10 flex items-center justify-center group-hover:border-[#00d4aa] group-hover:text-[#00d4aa] transition-colors">
                    →
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* STEP 2: DURATION */}
        {step === 'duration' && (
          <div className="space-y-6 animate-fade-up">
            <label className="text-xs font-black text-[#00d4aa] uppercase tracking-[0.3em]">Step 02 / Stay Duration</label>
            <div className="grid grid-cols-1 gap-4">
              {[
                { id: '1', name: 'Tonight Only', desc: '1 Night stay' },
                { id: '2', name: 'Short Stay', desc: '2-3 Nights' },
                { id: '7', name: 'Extended', desc: '4+ Nights' }
              ].map(d => (
                <button
                  key={d.id}
                  onClick={() => handleDuration(d.id)}
                  className="w-full p-8 bg-white/5 border border-white/10 rounded-3xl hover:border-[#00d4aa] hover:bg-white/10 transition-all text-left flex items-center justify-between"
                >
                  <div>
                    <div className="text-xl font-bold tracking-tight">{d.name}</div>
                    <div className="text-xs text-white/30 uppercase tracking-widest font-bold mt-1">{d.desc}</div>
                  </div>
                  <div className="text-[#00d4aa] font-mono">[{d.id}]</div>
                </button>
              ))}
            </div>
            <button onClick={() => setStep('room_type')} className="text-white/20 text-xs font-black uppercase tracking-widest mt-8 hover:text-white transition-colors">← Back to inventory</button>
          </div>
        )}

        {/* LOADING STATE */}
        {step === 'loading' && (
          <div className="space-y-6">
            <div className="flex flex-col items-center py-12">
              <div className="w-16 h-16 border-4 border-[#00d4aa]/20 border-t-[#00d4aa] rounded-full animate-spin mb-6" />
              <p className="text-center text-sm font-black tracking-[0.2em] uppercase animate-pulse">Syncing with Trust Network...</p>
            </div>
          </div>
        )}

        {/* RESULTS LIST */}
        {step === 'results' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-xs font-black text-white/30 uppercase tracking-[0.3em]">{results.length} Verified Partners</h3>
              <button onClick={() => setStep('room_type')} className="text-[#00d4aa] text-xs font-black uppercase tracking-widest border-b border-[#00d4aa]/30">Reset Search</button>
            </div>
            {results.map((hotel, i) => (
              <div 
                key={hotel.id}
                className="group relative overflow-hidden bg-white/5 border border-white/10 rounded-[2.5rem] p-8 animate-fade-up transition-all hover:bg-white/10"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h4 className="text-2xl font-black tracking-tighter mb-1 italic">{hotel.display_name}</h4>
                    <p className="amharic text-[#00d4aa] font-bold text-sm tracking-normal">{hotel.display_name_am}</p>
                  </div>
                  <div className="flex flex-col items-end">
                    <div className="text-xs font-black text-white/30 uppercase tracking-widest mb-1">Trust Score</div>
                    <div className="text-2xl font-black text-[#00d4aa] tracking-tighter">{hotel.trust_score}</div>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-6 text-xs font-black uppercase tracking-widest text-white/40 mb-10">
                  <span className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full">📍 {hotel.distance_km} KM</span>
                  <span className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full">🛏️ {hotel.room_type}</span>
                </div>

                <div className="flex items-center justify-between pt-6 border-t border-white/5">
                  <div>
                    <div className="text-[10px] font-black text-white/20 uppercase tracking-widest mb-1">Quoted Rate</div>
                    <div className="text-2xl font-black text-white">{hotel.price_etb} <span className="text-xs text-white/30 ml-1">ETB</span></div>
                  </div>
                  <button 
                    onClick={() => handleRefer(hotel)}
                    className="bg-white text-[#070b12] text-xs font-black uppercase tracking-[0.2em] px-8 py-4 rounded-2xl hover:scale-105 active:scale-95 transition-all shadow-[0_10px_20px_rgba(255,255,255,0.05)]"
                  >
                    Send Referral →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* CONFIRMATION SCREEN */}
        {step === 'confirmation' && selectedHotel && (
          <div className="fixed inset-0 z-[100] bg-[#070b12]/95 backdrop-blur-xl flex items-center justify-center p-6 animate-fade-in">
            <div className="max-w-md w-full bg-white/[0.03] border border-white/10 rounded-[3rem] p-10 relative overflow-hidden shadow-2xl">
              <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-[#00d4aa] to-[#3b82f6]" />
              
              <div className="mb-10 flex justify-center">
                <div className="w-20 h-20 bg-[#00d4aa]/20 rounded-full flex items-center justify-center animate-pulse">
                  <div className="w-12 h-12 bg-[#00d4aa] rounded-full flex items-center justify-center text-[#070b12] text-2xl font-black">
                    ✓
                  </div>
                </div>
              </div>

              <h2 className="text-3xl font-black tracking-tighter mb-4 italic text-center">Referral Initiated</h2>
              <p className="text-white/40 text-center text-sm mb-10 leading-relaxed">
                Guest placement session started. {selectedHotel.display_name} has been notified via the Trust Network.
              </p>

              <div className="bg-black/50 p-8 rounded-3xl border border-white/10 mb-10 text-center">
                <p className="text-[10px] font-black text-[#00d4aa] uppercase tracking-[0.4em] mb-4">Tracking Code</p>
                <div className="text-5xl font-black tracking-[0.2em] text-white font-mono">
                  {handshakeCode}
                </div>
              </div>

              <button 
                onClick={() => router.push('/dashboard')}
                className="w-full bg-white text-[#070b12] text-xs font-black uppercase tracking-widest py-4 rounded-2xl mb-4"
              >
                Back to Dashboard
              </button>
              
              <p className="text-center text-[10px] text-white/20 uppercase tracking-widest">The partner will accept in ~10 seconds</p>
            </div>
          </div>
        )}
      </div>

      <style jsx global>{`
        @keyframes fade-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-up {
          animation: fade-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
