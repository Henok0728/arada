'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

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
    roomType: '',
    duration: ''
  });
  const [results, setResults] = useState<HotelResult[]>([]);
  const [handshakeCode, setHandshakeCode] = useState('');
  const [selectedHotel, setSelectedHotel] = useState<HotelResult | null>(null);

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
    // Simulated API call delay
    setTimeout(() => {
      const mockResults: HotelResult[] = [
        { 
          id: '1', 
          display_name: 'Blue Nile Lodge', 
          display_name_am: 'ብሉ ናይል ሎጅ', 
          distance_km: 0.3, 
          trust_score: 94, 
          room_type: selection.roomType || 'Double', 
          price_etb: 850 
        },
        { 
          id: '2', 
          display_name: 'Addis Heights Hotel', 
          display_name_am: 'አዲስ ሃይትስ ሆቴል', 
          distance_km: 0.8, 
          trust_score: 81, 
          room_type: selection.roomType || 'Double', 
          price_etb: 720 
        },
        { 
          id: '3', 
          display_name: 'Panorama Guesthouse', 
          display_name_am: 'ፓኖራማ ጌስትሀውስ', 
          distance_km: 1.2, 
          trust_score: 73, 
          room_type: selection.roomType || 'Double', 
          price_etb: 590 
        }
      ];
      setResults(mockResults);
      setStep('results');
    }, 1500);
  };

  const handleRefer = async (hotel: HotelResult) => {
    setStep('loading');
    setSelectedHotel(hotel);
    
    // Simulate POST /v1/referrals
    setTimeout(() => {
      setHandshakeCode('HTL-' + Math.random().toString(36).substring(2, 8).toUpperCase());
      setStep('confirmation');
    }, 1000);
  };

  return (
    <div className="max-w-2xl mx-auto pt-8">
      {/* HEADER */}
      <div className="mb-12">
        <h1 className="text-3xl font-bold mb-2">Emergency Referral</h1>
        <p className="text-white/50">Find a room for your guest in seconds.</p>
      </div>

      {/* STEP 1: ROOM TYPE */}
      {step === 'room_type' && (
        <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-300">
          <label className="text-sm font-bold text-[#00d4aa] uppercase tracking-widest">Select Room Type</label>
          <div className="flex flex-col gap-4">
            {['Single', 'Double', 'Suite'].map(type => (
              <button
                key={type}
                onClick={() => handleRoomType(type)}
                className="w-full py-6 glass-card hover:border-[#00d4aa] text-xl font-bold transition-all active:scale-[0.98]"
              >
                {type}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* STEP 2: DURATION */}
      {step === 'duration' && (
        <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-300">
          <label className="text-sm font-bold text-[#00d4aa] uppercase tracking-widest">For How Long?</label>
          <div className="flex flex-col gap-4">
            {['Tonight', '2 nights', '3 nights'].map(dur => (
              <button
                key={dur}
                onClick={() => handleDuration(dur)}
                className="w-full py-6 glass-card hover:border-[#00d4aa] text-xl font-bold transition-all active:scale-[0.98]"
              >
                {dur}
              </button>
            ))}
          </div>
          <button onClick={() => setStep('room_type')} className="text-white/30 text-sm mt-4 hover:text-white transition-colors">← Back</button>
        </div>
      )}

      {/* LOADING STATE */}
      {step === 'loading' && (
        <div className="space-y-6">
          <p className="text-center text-white/50 animate-pulse">Checking nearby hotels...</p>
          {[1, 2, 3].map(i => (
            <div key={i} className="glass-card p-6 flex flex-col gap-4">
              <div className="h-6 w-1/3 skeleton" />
              <div className="h-4 w-1/4 skeleton" />
              <div className="h-10 w-full skeleton mt-2" />
            </div>
          ))}
        </div>
      )}

      {/* RESULTS LIST */}
      {step === 'results' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-white/60 uppercase tracking-widest text-xs">{results.length} Hotels Found</h3>
            <button onClick={() => setStep('room_type')} className="text-[#00d4aa] text-xs font-bold uppercase">Change Search</button>
          </div>
          {results.map((hotel, i) => (
            <div 
              key={hotel.id}
              className="glass-card p-6 animate-in slide-in-from-bottom-8 duration-500 fill-mode-both"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="text-xl font-bold">{hotel.display_name}</h4>
                  <p className="amharic text-white/50 text-sm">{hotel.display_name_am}</p>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-bold ${
                  hotel.trust_score >= 85 ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                  hotel.trust_score >= 70 ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                  'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}>
                  Trust: {hotel.trust_score}
                </div>
              </div>
              <div className="flex gap-4 text-sm text-white/60 mb-6">
                <span>📍 {hotel.distance_km} km away</span>
                <span>🛏️ {hotel.room_type}</span>
                <span className="font-bold text-white">{hotel.price_etb} ETB</span>
              </div>
              <button 
                onClick={() => handleRefer(hotel)}
                className="w-full py-4 bg-[#00d4aa] text-[#070b12] font-bold rounded-lg hover:scale-[1.01] transition-transform active:scale-[0.99]"
              >
                REFER GUEST →
              </button>
            </div>
          ))}
        </div>
      )}

      {/* CONFIRMATION SCREEN */}
      {step === 'confirmation' && selectedHotel && (
        <div className="fixed inset-0 z-[100] bg-[#070b12] flex items-center justify-center p-6 text-center animate-in fade-in duration-500">
          <div className="max-w-md w-full glass-card p-10 relative overflow-hidden border-white/20">
            <div className="absolute top-0 left-0 w-full h-1 bg-[#00d4aa]" />
            
            <div className="mb-8 flex justify-center">
              <svg className="w-20 h-20 text-[#00d4aa]" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="283" strokeDashoffset="283" className="animate-[draw-stroke_0.8s_ease-out_forwards]" />
                <path d="M30 50 L45 65 L70 35" fill="none" stroke="currentColor" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="100" strokeDashoffset="100" className="animate-[draw-stroke_0.5s_0.8s_ease-out_forwards]" />
              </svg>
            </div>

            <h2 className="text-2xl font-bold mb-2">Referral Accepted!</h2>
            <p className="text-white/50 mb-8">{selectedHotel.display_name} is expecting your guest.</p>

            <div className="bg-white/5 p-6 rounded-xl border border-white/10 mb-8">
              <p className="text-xs font-bold text-[#00d4aa] uppercase tracking-[0.2em] mb-2">Handshake Code</p>
              <div className="text-4xl font-mono font-bold tracking-widest text-white">
                {handshakeCode}
              </div>
            </div>

            <div className="space-y-3 mb-8">
              <p className="text-sm font-medium">Give this code to your guest.</p>
              <p className="amharic text-white/50">ይህንን ኮድ ለእንግዳው ይስጡ።</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button className="py-3 bg-white/10 rounded-lg font-bold hover:bg-white/20 transition-colors">Print Code</button>
              <button className="py-3 bg-white/10 rounded-lg font-bold hover:bg-white/20 transition-colors">Send SMS</button>
            </div>

            <p className="text-[10px] text-white/30 mt-8 uppercase tracking-widest">
              Works offline — code is cryptographically signed
            </p>

            <button 
              onClick={() => router.push('/dashboard')}
              className="mt-8 text-white/30 text-sm hover:text-white transition-colors"
            >
              Done, go to Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
