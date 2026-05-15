'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  getToken, clearAuth, isApiError,
  acceptReferral, declineReferral,
  getIncomingReferrals
} from '../../lib/api';

function playNotificationSound() {
  try {
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); 
    oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.1);
    
    gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.5, audioCtx.currentTime + 0.05);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
    
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.start(audioCtx.currentTime);
    oscillator.stop(audioCtx.currentTime + 0.3);
  } catch (e) {}
}

function CountUp({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const duration = 800;
    if (target === 0) { setVal(0); return; }
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setVal(target); clearInterval(timer); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [target]);
  return <>{val}{suffix}</>;
}

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [loaded, setLoaded] = useState(false);
  const [activeTab, setActiveTab] = useState<'reception' | 'admin' | 'developer'>('reception');
  const prevReferralsCountRef = useRef(0);
  const [flashingCardId, setFlashingCardId] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) { router.push('/'); return; }
    setLoaded(true);
  }, [router]);

  const { data: referrals = [], isLoading } = useQuery('incoming-referrals', async () => {
    const res = await getIncomingReferrals();
    if (isApiError(res)) return [];
    return res;
  }, {
    refetchInterval: 10000, 
    enabled: loaded,
    onSuccess: (data) => {
      const pendingCount = data.filter(r => r.status === 'PENDING').length;
      if (pendingCount > prevReferralsCountRef.current) {
        playNotificationSound();
        const newest = data.find(r => r.status === 'PENDING');
        if (newest) {
          setFlashingCardId(newest.referral_id);
          setTimeout(() => setFlashingCardId(null), 3000);
        }
      }
      prevReferralsCountRef.current = pendingCount;
    }
  });

  const acceptMutation = useMutation((id: string) => acceptReferral(id), {
    onSuccess: () => queryClient.invalidateQueries('incoming-referrals')
  });

  const declineMutation = useMutation((id: string) => declineReferral(id, 'No availability'), {
    onSuccess: () => queryClient.invalidateQueries('incoming-referrals')
  });

  if (!loaded) return null;

  const hotelName = typeof window !== 'undefined' && localStorage.getItem('ll_hotel_type') === 'B' 
    ? 'Entoto View Lodge' : 'Bole Skyline Hotel';

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-4xl font-black tracking-tighter">{hotelName}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="px-2 py-0.5 rounded bg-[#00d4aa]/20 text-[#00d4aa] text-[10px] font-black uppercase tracking-widest">Active Partner</span>
            <span className="text-white/40 text-xs font-bold uppercase tracking-widest">Addis Ababa Cluster</span>
          </div>
        </div>
        <div className="flex gap-2 bg-white/5 p-1 rounded-2xl border border-white/10">
          {[
            { id: 'reception', label: 'Reception', icon: '🛎️' },
            { id: 'admin', label: 'Admin', icon: '📊' },
            { id: 'developer', label: 'Developer', icon: '👨‍💻' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeTab === tab.id ? 'bg-white text-[#070b12] shadow-xl' : 'text-white/40 hover:text-white'}`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'reception' && (
        <div className="space-y-8">
          {/* Tonight's Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'Available Inventory', value: 7, color: '#00d4aa' },
              { label: 'Network Sent', value: 12, color: '#3b82f6' },
              { label: 'Network Received', value: referrals.length, color: '#ffb800' }
            ].map(s => (
              <div key={s.label} className="bg-white/5 border border-white/5 rounded-3xl p-8 hover:bg-white/[0.08] transition-all">
                <div className="text-xs font-black text-white/30 uppercase tracking-[0.2em] mb-4">{s.label}</div>
                <div className="text-5xl font-black tracking-tighter" style={{ color: s.color }}>
                  <CountUp target={s.value} />
                </div>
              </div>
            ))}
          </div>

          {/* Referrals List */}
          <div>
            <div className="flex items-center gap-4 mb-6">
              <h2 className="text-2xl font-black tracking-tight">Incoming Protocol Requests</h2>
              <div className="h-2 w-2 rounded-full bg-[#00d4aa] animate-ping" />
            </div>

            {isLoading ? (
              <div className="space-y-4">
                {[1,2,3].map(i => <div key={i} className="h-40 bg-white/5 rounded-3xl animate-pulse" />)}
              </div>
            ) : referrals.length === 0 ? (
              <div className="bg-white/5 border border-dashed border-white/10 rounded-[3rem] p-20 text-center">
                <div className="text-4xl mb-6 grayscale opacity-50">📡</div>
                <h3 className="text-xl font-bold mb-2">No active requests</h3>
                <p className="text-white/40 text-sm max-w-xs mx-auto">The Trust Network is currently monitoring for nearby availability signals.</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {referrals.map((ref: any) => (
                  <div 
                    key={ref.referral_id}
                    className={`group relative overflow-hidden bg-white/5 border rounded-[2.5rem] p-8 transition-all duration-500 ${
                      flashingCardId === ref.referral_id ? 'border-[#00d4aa] bg-[#00d4aa]/10 scale-[1.01]' : 'border-white/5 hover:border-white/20'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-8">
                      <div>
                        <div className="text-[10px] font-black text-[#00d4aa] uppercase tracking-[0.3em] mb-2">Incoming Referral</div>
                        <div className="text-2xl font-black tracking-tighter italic">Guest: {ref.guest_name || 'Protocol Guest'}</div>
                        <div className="text-sm text-white/40 font-bold uppercase tracking-widest mt-2">{ref.room_type} · 1 Night · Guaranteed Trust</div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-black tracking-tighter">850 <span className="text-xs text-white/30 ml-1">ETB</span></div>
                        <div className="text-[10px] font-black text-white/20 uppercase tracking-widest mt-1">Direct Settlement</div>
                      </div>
                    </div>

                    {ref.status === 'PENDING' ? (
                      <div className="flex gap-4">
                        <button 
                          onClick={() => acceptMutation.mutate(ref.referral_id)}
                          disabled={acceptMutation.isLoading}
                          className="flex-1 py-5 bg-white text-[#070b12] font-black text-xs uppercase tracking-widest rounded-2xl hover:scale-105 transition-all disabled:opacity-50"
                        >
                          {acceptMutation.isLoading ? '...' : 'Accept Referral'}
                        </button>
                        <button 
                          onClick={() => declineMutation.mutate(ref.referral_id)}
                          disabled={declineMutation.isLoading}
                          className="px-10 py-5 bg-white/5 border border-white/10 text-white font-black text-xs uppercase tracking-widest rounded-2xl hover:bg-white/10 transition-all disabled:opacity-50"
                        >
                          Decline
                        </button>
                      </div>
                    ) : (
                      <div className={`py-4 rounded-2xl text-center text-xs font-black uppercase tracking-widest ${ref.status === 'ACCEPTED' ? 'bg-[#00d4aa]/20 text-[#00d4aa]' : 'bg-red-500/20 text-red-500'}`}>
                        {ref.status === 'ACCEPTED' ? '✓ Handshake Active — Expecting Guest' : 'Referral Declined'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'admin' && (
        <div className="space-y-8 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white/5 border border-white/5 rounded-[3rem] p-10">
              <h3 className="text-xl font-bold mb-8">Revenue Performance</h3>
              <div className="space-y-6">
                {[
                  { label: 'Referral Earnings', val: '42,500 ETB', p: '85%' },
                  { label: 'Network Commissions', val: '8,400 ETB', p: '15%' }
                ].map(item => (
                  <div key={item.label}>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-bold text-white/50">{item.label}</span>
                      <span className="text-sm font-black">{item.val}</span>
                    </div>
                    <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-[#00d4aa]" style={{ width: item.p }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white/5 border border-white/5 rounded-[3rem] p-10">
              <h3 className="text-xl font-bold mb-8">Trust Dynamics</h3>
              <div className="flex items-center justify-center py-10">
                <div className="relative h-40 w-40 flex items-center justify-center">
                  <svg className="absolute inset-0 h-full w-full -rotate-90">
                    <circle cx="80" cy="80" r="70" fill="none" stroke="currentColor" strokeWidth="12" className="text-white/5" />
                    <circle cx="80" cy="80" r="70" fill="none" stroke="currentColor" strokeWidth="12" strokeDasharray="440" strokeDashoffset="44" className="text-[#00d4aa]" />
                  </svg>
                  <div className="text-center">
                    <div className="text-4xl font-black tracking-tighter">92</div>
                    <div className="text-[10px] font-black text-white/30 uppercase tracking-widest mt-1">Trust Score</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'developer' && (
        <div className="max-w-2xl mx-auto animate-fade-in">
          <div className="bg-white/5 border border-white/10 rounded-[3rem] p-10">
            <div className="text-center mb-10">
              <div className="h-16 w-16 bg-[#3b82f6]/20 rounded-full flex items-center justify-center mx-auto mb-6 text-2xl">🔑</div>
              <h3 className="text-2xl font-black tracking-tighter">API Infrastructure</h3>
              <p className="text-white/40 text-sm mt-2">Manage your production and sandbox keys.</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="text-[10px] font-black text-white/30 uppercase tracking-widest mb-2 block">Production Access Token</label>
                <div className="flex gap-2">
                  <input readOnly value="sk_live_lodge_7319x821..." className="flex-1 bg-black/20 border border-white/10 rounded-xl px-4 py-3 font-mono text-sm" />
                  <button className="bg-white text-[#070b12] px-6 rounded-xl font-bold text-xs uppercase tracking-widest">Copy</button>
                </div>
              </div>
              <div className="p-6 bg-[#3b82f6]/10 border border-[#3b82f6]/20 rounded-2xl">
                <div className="flex gap-4 items-start">
                  <div className="text-xl">ℹ️</div>
                  <div>
                    <div className="text-sm font-bold text-[#3b82f6]">Sandbox Mode Active</div>
                    <p className="text-xs text-[#3b82f6]/60 mt-1 leading-relaxed">You are currently using a sandbox key. Your production access will be granted after the final KYC audit (usually 24h).</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx global>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.4s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
