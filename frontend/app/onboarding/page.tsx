'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { loginHotel, isApiError, getToken } from '../../lib/api';

type Step = 1 | 2 | 3 | 4;

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  
  // Step 1
  const [hotelName, setHotelName] = useState('');
  const [city, setCity] = useState('Addis Ababa');
  
  // Step 2
  const [tinFile, setTinFile] = useState<File | null>(null);
  const [licenseFile, setLicenseFile] = useState<File | null>(null);
  
  // Step 3
  const [tier, setTier] = useState<'STARTER' | 'NETWORK' | 'ENTERPRISE'>('NETWORK');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'tin' | 'license') => {
    if (e.target.files && e.target.files[0]) {
      if (type === 'tin') setTinFile(e.target.files[0]);
      else setLicenseFile(e.target.files[0]);
    }
  };

  const completeOnboarding = async () => {
    setLoading(true);
    // Simulate real KYC ingestion & Sandbox key generation
    await new Promise(r => setTimeout(r, 1500));
    setApiKey('sk_test_lodge_' + Math.random().toString(36).substr(2, 9));
    setStep(4);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-white flex flex-col items-center py-16 px-4">
      <div className="w-full max-w-2xl relative z-10">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#3b82f6]/20 border border-[#3b82f6]/30 text-[#3b82f6] text-[10px] font-black uppercase tracking-widest mb-4">
            Network Enrollment
          </div>
          <h1 className="text-5xl font-black tracking-tighter mb-4 italic">Start Your Integration</h1>
          <p className="text-white/40 text-lg">Follow the protocol to secure your Sandbox access.</p>
        </div>

        <div className="relative">
          <div className="absolute left-6 top-10 bottom-10 w-0.5 bg-white/5 z-0 hidden sm:block" />

          {/* STEP 1: IDENTITY */}
          <div className={`relative z-10 flex gap-8 mb-12 transition-all duration-500 ${step >= 1 ? 'opacity-100 scale-100' : 'opacity-20 scale-95 pointer-events-none'}`}>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-lg shrink-0 border-2 transition-colors ${step > 1 ? 'bg-[#00d4aa] border-[#00d4aa] text-[#070b12]' : step === 1 ? 'border-[#00d4aa] text-[#00d4aa] shadow-[0_0_20px_rgba(0,212,170,0.3)]' : 'border-white/10 text-white/20'}`}>
              {step > 1 ? '✓' : '01'}
            </div>
            <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-[2.5rem] p-10 backdrop-blur-xl">
              <h2 className="text-2xl font-black tracking-tight mb-8 italic">Hotel Identity</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-[10px] font-black text-white/30 mb-2 uppercase tracking-[0.3em]">Full Legal Name</label>
                  <input value={hotelName} onChange={e => setHotelName(e.target.value)} className="w-full bg-black/20 border border-white/10 rounded-2xl px-6 py-4 focus:outline-none focus:border-[#00d4aa] transition-all" placeholder="e.g. Skyline International Addis" />
                </div>
                <div>
                  <label className="block text-[10px] font-black text-white/30 mb-2 uppercase tracking-[0.3em]">Primary Operation City</label>
                  <input value={city} onChange={e => setCity(e.target.value)} className="w-full bg-black/20 border border-white/10 rounded-2xl px-6 py-4 focus:outline-none focus:border-[#00d4aa] transition-all" placeholder="Addis Ababa" />
                </div>
                {step === 1 && (
                  <button onClick={() => hotelName && setStep(2)} disabled={!hotelName} className="w-full mt-4 bg-white text-[#070b12] font-black text-xs uppercase tracking-widest py-5 rounded-2xl hover:scale-[1.02] active:scale-95 transition-all">
                    Continue to Verification
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* STEP 2: DOCUMENTS */}
          <div className={`relative z-10 flex gap-8 mb-12 transition-all duration-500 ${step >= 2 ? 'opacity-100 scale-100' : 'opacity-20 scale-95 pointer-events-none'}`}>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-lg shrink-0 border-2 transition-colors ${step > 2 ? 'bg-[#00d4aa] border-[#00d4aa] text-[#070b12]' : step === 2 ? 'border-[#00d4aa] text-[#00d4aa] shadow-[0_0_20px_rgba(0,212,170,0.3)]' : 'border-white/10 text-white/20'}`}>
              {step > 2 ? '✓' : '02'}
            </div>
            <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-[2.5rem] p-10 backdrop-blur-xl">
              <h2 className="text-2xl font-black tracking-tight mb-8 italic">KYC Verification</h2>
              <p className="text-white/40 text-sm mb-8 leading-relaxed">Please upload your digital certificates for automated verification.</p>
              
              <div className="grid sm:grid-cols-2 gap-6">
                <div>
                  <label className="block text-[10px] font-black text-[#00d4aa] uppercase tracking-[0.2em] mb-4">TIN Certificate</label>
                  <div className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all ${tinFile ? 'border-[#00d4aa] bg-[#00d4aa]/10' : 'border-white/10 hover:border-white/30 bg-black/20'}`}>
                    <input type="file" onChange={e => handleFileChange(e, 'tin')} className="absolute inset-0 opacity-0 cursor-pointer" />
                    <div className="text-3xl mb-2">{tinFile ? '📄' : '📁'}</div>
                    <div className="text-[10px] font-black uppercase text-white/60">{tinFile ? tinFile.name : 'Select File'}</div>
                  </div>
                </div>
                <div>
                  <label className="block text-[10px] font-black text-[#00d4aa] uppercase tracking-[0.2em] mb-4">Business License</label>
                  <div className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all ${licenseFile ? 'border-[#00d4aa] bg-[#00d4aa]/10' : 'border-white/10 hover:border-white/30 bg-black/20'}`}>
                    <input type="file" onChange={e => handleFileChange(e, 'license')} className="absolute inset-0 opacity-0 cursor-pointer" />
                    <div className="text-3xl mb-2">{licenseFile ? '📄' : '📁'}</div>
                    <div className="text-[10px] font-black uppercase text-white/60">{licenseFile ? licenseFile.name : 'Select File'}</div>
                  </div>
                </div>
              </div>

              {step === 2 && (
                <button onClick={() => tinFile && licenseFile && setStep(3)} disabled={!tinFile || !licenseFile} className="w-full mt-8 bg-white text-[#070b12] font-black text-xs uppercase tracking-widest py-5 rounded-2xl hover:scale-[1.02] active:scale-95 transition-all">
                  Upload & Verify
                </button>
              )}
            </div>
          </div>

          {/* STEP 3: TIER */}
          <div className={`relative z-10 flex gap-8 mb-12 transition-all duration-500 ${step >= 3 ? 'opacity-100 scale-100' : 'opacity-20 scale-95 pointer-events-none'}`}>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black text-lg shrink-0 border-2 transition-colors ${step > 3 ? 'bg-[#00d4aa] border-[#00d4aa] text-[#070b12]' : step === 3 ? 'border-[#00d4aa] text-[#00d4aa] shadow-[0_0_20px_rgba(0,212,170,0.3)]' : 'border-white/10 text-white/20'}`}>
              03
            </div>
            <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-[2.5rem] p-10 backdrop-blur-xl">
              <h2 className="text-2xl font-black tracking-tight mb-8 italic">Network Scaling</h2>
              <div className="space-y-4">
                {[
                  { id: 'STARTER', icon: '🌱', name: 'Starter', desc: 'Free testing & first 50 refs' },
                  { id: 'NETWORK', icon: '⚡', name: 'Network', desc: 'Production access - 2% fee' },
                  { id: 'ENTERPRISE', icon: '🏢', name: 'Enterprise', desc: 'Custom PMS node' }
                ].map(t => (
                  <button key={t.id} onClick={() => setTier(t.id as any)} className={`w-full flex items-center p-6 rounded-3xl border text-left transition-all ${tier === t.id ? 'border-[#00d4aa] bg-[#00d4aa]/10' : 'border-white/5 hover:border-white/20 bg-black/20'}`}>
                    <div className="text-3xl mr-6 grayscale group-hover:grayscale-0">{t.icon}</div>
                    <div>
                      <div className="font-bold text-lg">{t.name}</div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mt-1">{t.desc}</div>
                    </div>
                    {tier === t.id && <div className="ml-auto text-[#00d4aa] text-xl font-black">✓</div>}
                  </button>
                ))}
              </div>
              {step === 3 && (
                <button onClick={completeOnboarding} disabled={loading} className="w-full mt-10 bg-gradient-to-r from-[#00d4aa] to-[#3b82f6] text-[#070b12] font-black text-sm uppercase tracking-[0.2em] py-6 rounded-[2rem] shadow-[0_20px_40px_rgba(0,212,170,0.25)] hover:scale-[1.02] active:scale-95 transition-all">
                  {loading ? 'Initializing Protocol...' : 'Finalize Sandbox Setup'}
                </button>
              )}
            </div>
          </div>

          {/* STEP 4: SUCCESS */}
          {step === 4 && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#070b12]/95 backdrop-blur-2xl p-4 animate-fade-in">
              <div className="bg-white/[0.05] border border-white/10 rounded-[3.5rem] p-12 max-w-lg w-full text-center relative shadow-2xl">
                <div className="w-24 h-24 bg-gradient-to-tr from-[#00d4aa] to-[#3b82f6] rounded-full mx-auto mb-8 flex items-center justify-center text-5xl">🎉</div>
                <h2 className="text-4xl font-black tracking-tighter mb-4 italic">Protocol Initiated</h2>
                <p className="text-white/50 mb-10 leading-relaxed">Welcome, <span className="text-white font-bold">{hotelName}</span>. Your sandbox environment is live. Use the key below for your initial PMS integration.</p>
                
                <div className="bg-black/50 border border-white/10 rounded-3xl p-8 mb-10 group cursor-pointer hover:border-[#00d4aa]/40 transition-colors">
                  <div className="text-[10px] font-black text-[#00d4aa] uppercase tracking-[0.4em] mb-4">Sandbox API Key</div>
                  <code className="text-xl font-mono text-white break-all tracking-tighter">{apiKey}</code>
                  <div className="text-[10px] text-white/20 mt-4 uppercase tracking-widest group-hover:text-[#00d4aa] transition-colors">Click to copy token</div>
                </div>
                
                <div className="flex flex-col gap-4">
                  <button onClick={() => router.push('/dashboard')} className="w-full bg-white text-[#070b12] font-black text-xs uppercase tracking-widest py-5 rounded-2xl hover:scale-105 transition-all">
                    Access Dashboard
                  </button>
                  <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.2em]">Live production key granted after first referral</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      <style jsx global>{`
        @keyframes fade-in {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fade-in {
          animation: fade-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .amharic {
          font-size: 85%;
        }
      `}</style>
    </div>
  );
}
