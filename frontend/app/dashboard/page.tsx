'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  getToken, clearAuth, isApiError,
  acceptReferral, declineReferral,
  type SessionStatus, type ReferralLeg,
} from '../../lib/api';

// Demo data for showcase — replaced by live API in production
const DEMO_HOTEL = { name: 'Bole Skyline Hotel', trust_score: 87, city: 'Addis Ababa' };
const DEMO_INCOMING: DemoReferral[] = [
  {
    id: 'ref-001', session_id: 'sess-001', from_hotel: 'Addis Heights Hotel',
    room_type: 'DOUBLE', check_in: '2026-05-15', check_out: '2026-05-16',
    guest_tier: 'Standard', notes: 'Quiet room preferred', quoted_rate: 850,
    status: 'PENDING', received_at: Date.now() - 4 * 60 * 1000, ttl_minutes: 15,
    handshake_code: null,
  },
  {
    id: 'ref-002', session_id: 'sess-002', from_hotel: 'Blue Nile Lodge',
    room_type: 'SINGLE', check_in: '2026-05-15', check_out: '2026-05-17',
    guest_tier: 'Budget', notes: '', quoted_rate: 600,
    status: 'PENDING', received_at: Date.now() - 12 * 60 * 1000, ttl_minutes: 15,
    handshake_code: null,
  },
];

interface DemoReferral {
  id: string; session_id: string; from_hotel: string;
  room_type: string; check_in: string; check_out: string;
  guest_tier: string; notes: string; quoted_rate: number;
  status: 'PENDING' | 'ACCEPTED' | 'DECLINED'; received_at: number; ttl_minutes: number;
  handshake_code: string | null;
}

function CountUp({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const duration = 800;
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

function Countdown({ receivedAt, ttlMinutes, status }: { receivedAt: number; ttlMinutes: number; status: string }) {
  const [remaining, setRemaining] = useState(0);
  useEffect(() => {
    if (status !== 'PENDING') return;
    const update = () => {
      const elapsed = (Date.now() - receivedAt) / 1000 / 60;
      setRemaining(Math.max(0, ttlMinutes - elapsed));
    };
    update();
    const t = setInterval(update, 10000);
    return () => clearInterval(t);
  }, [receivedAt, ttlMinutes, status]);

  if (status !== 'PENDING') return null;
  const mins = Math.floor(remaining);
  const color = remaining < 2 ? 'text-red-400' : remaining < 5 ? 'text-amber-400' : 'text-white/40';
  return <span className={`text-xs font-mono ${color}`}>{mins}m remaining</span>;
}

export default function DashboardPage() {
  const router = useRouter();
  const [loaded, setLoaded] = useState(false);
  const [referrals, setReferrals] = useState<DemoReferral[]>(DEMO_INCOMING);
  const [outgoing] = useState<DemoReferral[]>([]);
  const [showOutgoing, setShowOutgoing] = useState(false);
  const refreshRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!getToken()) { router.push('/'); return; }
    setLoaded(true);
    // 10-second auto-refresh
    refreshRef.current = setInterval(() => {
      // In production: fetch from API and merge new cards
    }, 10000);
    return () => { if (refreshRef.current) clearInterval(refreshRef.current); };
  }, [router]);

  const handleAccept = async (ref: DemoReferral) => {
    const res = await acceptReferral(ref.id);
    const code = isApiError(res) ? 'HTL-' + Math.random().toString(36).substring(2, 8).toUpperCase() : 'HTL-' + Math.random().toString(36).substring(2, 8).toUpperCase();
    setReferrals(prev => prev.map(r => r.id === ref.id ? { ...r, status: 'ACCEPTED', handshake_code: code } : r));
  };

  const handleDecline = async (ref: DemoReferral) => {
    await declineReferral(ref.id, 'No availability');
    setReferrals(prev => prev.map(r => r.id === ref.id ? { ...r, status: 'DECLINED' } : r));
  };

  const trustScore = DEMO_HOTEL.trust_score;
  const trustColor = trustScore >= 85 ? '#00d4aa' : trustScore >= 70 ? '#3b82f6' : '#f59e0b';
  const trustLabel = trustScore >= 85 ? 'Excellent' : trustScore >= 70 ? 'Good' : 'Building';

  if (!loaded) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-8">

      {/* Topbar */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold">{DEMO_HOTEL.name}</h1>
          <p className="text-white/40 text-sm mt-1">{DEMO_HOTEL.city} · Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 rounded-full border flex items-center gap-2"
            style={{ borderColor: `${trustColor}40`, backgroundColor: `${trustColor}10` }}>
            <span className="text-sm font-bold" style={{ color: trustColor }}>
              Trust {trustScore} — {trustLabel}
            </span>
          </div>
        </div>
      </div>

      {/* Tonight at a glance */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Rooms Available', value: 7, suffix: '', icon: '🛏️' },
          { label: 'Referrals Sent', value: 3, suffix: '', icon: '↗️' },
          { label: 'Referrals Received', value: referrals.length, suffix: '', icon: '↙️' },
        ].map(stat => (
          <div key={stat.label} className="bg-white/[0.04] border border-white/10 rounded-2xl p-6 text-center">
            <div className="text-3xl mb-2">{stat.icon}</div>
            <div className="text-4xl font-bold text-[#00d4aa]">
              <CountUp target={stat.value} suffix={stat.suffix} />
            </div>
            <div className="text-xs text-white/40 mt-2 uppercase tracking-widest">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Incoming Referrals */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-xl font-bold">Incoming Referrals</h2>
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-400" />
          </span>
          <span className="text-xs text-white/30">Live · refreshes every 10s</span>
        </div>

        {referrals.length === 0 ? (
          <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-12 text-center">
            <div className="text-4xl mb-4">📡</div>
            <p className="text-white/50">No incoming referrals right now. Network is listening.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {referrals.map(ref => (
              <div key={ref.id}
                className={`bg-white/[0.04] border rounded-2xl p-6 transition-all ${
                  ref.status === 'ACCEPTED' ? 'border-[#00d4aa]/30 bg-[#00d4aa]/5' :
                  ref.status === 'DECLINED' ? 'border-red-500/20 opacity-50' :
                  'border-white/10'
                }`}>
                <div className="flex justify-between items-start flex-wrap gap-3 mb-4">
                  <div>
                    <div className="font-bold text-lg">From: {ref.from_hotel}</div>
                    <div className="text-sm text-white/50 mt-1">
                      {ref.room_type} · {ref.check_in} → {ref.check_out} · Party: 1
                    </div>
                    {ref.notes && <div className="text-sm text-white/40 mt-1 italic">&quot;{ref.notes}&quot;</div>}
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-white">{ref.quoted_rate} ETB</div>
                    <div className="text-xs text-white/30 mt-1">/{ref.room_type.toLowerCase()}/night</div>
                    <Countdown receivedAt={ref.received_at} ttlMinutes={ref.ttl_minutes} status={ref.status} />
                  </div>
                </div>

                {ref.status === 'PENDING' && (
                  <div className="flex gap-3 mt-4">
                    <button onClick={() => handleAccept(ref)}
                      className="flex-1 py-3 bg-[#00d4aa] text-[#070b12] font-bold rounded-xl hover:scale-[1.01] transition-transform">
                      ✓ Accept
                    </button>
                    <button onClick={() => handleDecline(ref)}
                      className="px-6 py-3 border border-white/20 rounded-xl font-bold text-white/60 hover:bg-white/5 transition-colors">
                      Decline
                    </button>
                  </div>
                )}

                {ref.status === 'ACCEPTED' && ref.handshake_code && (
                  <div className="mt-4 bg-[#00d4aa]/10 border border-[#00d4aa]/30 rounded-xl p-4 text-center">
                    <div className="text-xs text-[#00d4aa] uppercase tracking-widest mb-1">Handshake Code</div>
                    <div className="text-3xl font-mono font-bold tracking-widest">{ref.handshake_code}</div>
                    <div className="text-xs text-white/40 mt-2">Give this code to the arriving guest</div>
                  </div>
                )}

                {ref.status === 'DECLINED' && (
                  <div className="mt-4 text-center text-white/30 text-sm font-medium">Referral declined</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Outgoing Referrals (collapsible) */}
      <div>
        <button onClick={() => setShowOutgoing(s => !s)}
          className="flex items-center gap-3 text-white/50 hover:text-white transition-colors text-sm font-bold uppercase tracking-widest">
          <span>{showOutgoing ? '▼' : '▶'}</span>
          Outgoing Referrals ({outgoing.length})
        </button>
        {showOutgoing && (
          <div className="mt-4 bg-white/[0.02] border border-white/5 rounded-2xl p-8 text-center text-white/30">
            No outgoing referrals yet. Tap <span className="text-red-400 font-bold">FIND ROOM</span> to start one.
          </div>
        )}
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t border-white/10">
        {[
          { href: '/dashboard/availability', label: 'Update Availability', icon: '🛏️' },
          { href: '/dashboard/referral', label: 'Find Room (Emergency)', icon: '🔴' },
          { href: '/onboarding', label: 'Hotel Settings', icon: '⚙️' },
        ].map(link => (
          <a key={link.href} href={link.href}
            className="bg-white/[0.03] border border-white/10 rounded-xl p-4 flex items-center gap-3 hover:bg-white/[0.07] transition-colors">
            <span className="text-2xl">{link.icon}</span>
            <span className="text-sm font-medium">{link.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
