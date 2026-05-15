'use client';
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  loginHotel, isApiError, getToken,
  type TokenResponse,
} from '../../lib/api';

type Step = 1 | 2 | 3 | 4;

interface FormData {
  hotel_name: string;
  hotel_slug: string;
  city: string;
  address: string;
  phone_number: string;
  admin_email: string;
  admin_full_name: string;
  admin_password: string;
  confirm_password: string;
  room_count: string;
  tier: 'BUDGET' | 'STANDARD' | 'PREMIUM';
  integration: 'api' | 'webhook' | 'dashboard';
  docs: { [key: string]: boolean };
}

const CITIES = ['Addis Ababa', 'Lalibela', 'Bahir Dar', 'Gondar', 'Hawassa', 'Other'];
const DOCS = [
  { key: 'registration', label: 'Business Registration Certificate (Ministry of Trade)', am: 'የንግድ ምዝገባ ሰርተፊኬት' },
  { key: 'tin', label: 'Tax Identification Number (TIN)', am: 'የግብር መለያ ቁጥር' },
  { key: 'eto', label: 'ETO Operating License', am: 'የETO ፈቃድ' },
  { key: 'id', label: "Manager's National ID", am: 'የሥራ አስኪያጅ ዘወትር መታወቂያ' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>(1);
  const [direction, setDirection] = useState<'forward' | 'back'>('forward');
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState(false);

  const [form, setForm] = useState<FormData>({
    hotel_name: '', hotel_slug: '', city: 'Addis Ababa', address: '',
    phone_number: '+251', admin_email: '', admin_full_name: '',
    admin_password: '', confirm_password: '',
    room_count: '', tier: 'STANDARD', integration: 'dashboard',
    docs: { registration: false, tin: false, eto: false, id: false },
  });

  useEffect(() => {
    if (getToken()) router.push('/dashboard');
  }, [router]);

  const set = (k: keyof FormData, v: string | boolean) =>
    setForm(prev => ({ ...prev, [k]: v }));

  const slugify = (name: string) => name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

  const validateStep1 = () => {
    const errs: Record<string, string> = {};
    if (!form.hotel_name.trim()) errs.hotel_name = 'Hotel name required';
    if (!form.hotel_slug.match(/^[a-z0-9-]+$/)) errs.hotel_slug = 'Slug must be lowercase letters, numbers, hyphens only';
    if (!form.admin_email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) errs.admin_email = 'Valid email required';
    if (!form.admin_full_name.trim()) errs.admin_full_name = 'Full name required';
    if (form.admin_password.length < 8) errs.admin_password = 'Min 8 characters';
    if (form.admin_password !== form.confirm_password) errs.confirm_password = 'Passwords do not match';
    if (!form.phone_number.match(/^\+\d{7,15}$/)) errs.phone_number = 'E.164 format e.g. +251911234567';
    if (!form.address.trim()) errs.address = 'Address required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const goNext = async () => {
    if (step === 1) {
      if (!validateStep1()) return;
      setLoading(true);
      const { registerHotel } = await import('../../lib/api');
      const res = await registerHotel({
        hotel_name: form.hotel_name, hotel_slug: form.hotel_slug,
        city: form.city, address: form.address,
        phone_number: form.phone_number, admin_email: form.admin_email,
        admin_full_name: form.admin_full_name, admin_password: form.admin_password,
      });
      setLoading(false);
      if (isApiError(res)) { setErrors({ _api: res.error }); return; }
      setApiKey(res.api_key);
    }
    setDirection('forward');
    setStep(s => (s < 4 ? (s + 1) as Step : s));
  };

  const goBack = () => { setDirection('back'); setStep(s => (s > 1 ? (s - 1) as Step : s)); };

  const slideClass = direction === 'forward' ? 'animate-slide-in-right' : 'animate-slide-in-left';

  return (
    <div className="min-h-screen bg-[#070b12] flex flex-col items-center justify-center px-4 py-12">
      <style jsx global>{`
        @keyframes slide-in-right { from { opacity:0; transform:translateX(40px); } to { opacity:1; transform:translateX(0); } }
        @keyframes slide-in-left  { from { opacity:0; transform:translateX(-40px); } to { opacity:1; transform:translateX(0); } }
        .animate-slide-in-right { animation: slide-in-right 250ms ease-in-out both; }
        .animate-slide-in-left  { animation: slide-in-left 250ms ease-in-out both; }
        @keyframes draw-check { to { stroke-dashoffset: 0; } }
        .draw-check { animation: draw-check 0.6s ease-out 0.4s both; }
      `}</style>

      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-2xl font-bold">Lodge<span className="text-[#00d4aa]">-Link</span></div>
          <p className="text-white/50 text-sm mt-1">Hotel Partner Registration</p>
        </div>

        {/* Progress bar */}
        <div className="flex gap-1 mb-8">
          {[1,2,3,4].map(s => (
            <div key={s} className="h-1 flex-1 rounded-full transition-all duration-500"
              style={{ backgroundColor: s <= step ? '#00d4aa' : 'rgba(255,255,255,0.1)' }} />
          ))}
        </div>
        <div className="text-xs text-white/30 text-center mb-8">Step {step} of 4</div>

        <div className={`bg-white/[0.04] border border-white/10 rounded-2xl p-8 ${slideClass}`} key={step}>

          {/* STEP 1: Hotel basics */}
          {step === 1 && (
            <div className="space-y-5">
              <h2 className="text-2xl font-bold mb-6">Your hotel details</h2>
              {errors._api && <div className="bg-red-500/20 border border-red-500/30 text-red-400 text-sm px-4 py-3 rounded-lg">{errors._api}</div>}
              <Field label="Hotel Display Name" error={errors.hotel_name}>
                <input value={form.hotel_name} onChange={e => { set('hotel_name', e.target.value); set('hotel_slug', slugify(e.target.value)); }}
                  className="input-field" placeholder="Blue Nile Lodge" />
              </Field>
              <Field label="URL Slug" error={errors.hotel_slug}>
                <input value={form.hotel_slug} onChange={e => set('hotel_slug', slugify(e.target.value))}
                  className="input-field" placeholder="blue-nile-lodge" />
              </Field>
              <Field label="City">
                <select value={form.city} onChange={e => set('city', e.target.value)} className="input-field">
                  {CITIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </Field>
              <Field label="Address" error={errors.address}>
                <input value={form.address} onChange={e => set('address', e.target.value)} className="input-field" placeholder="Bole Road, Near Airport" />
              </Field>
              <Field label="Phone (E.164)" error={errors.phone_number}>
                <input value={form.phone_number} onChange={e => set('phone_number', e.target.value)} className="input-field" placeholder="+251911234567" />
              </Field>
              <Field label="Admin Email" error={errors.admin_email}>
                <input type="email" value={form.admin_email} onChange={e => set('admin_email', e.target.value)} className="input-field" placeholder="manager@hotel.et" />
              </Field>
              <Field label="Full Name" error={errors.admin_full_name}>
                <input value={form.admin_full_name} onChange={e => set('admin_full_name', e.target.value)} className="input-field" placeholder="Abebe Kebede" />
              </Field>
              <Field label="Password" error={errors.admin_password}>
                <input type="password" value={form.admin_password} onChange={e => set('admin_password', e.target.value)} className="input-field" placeholder="Min 8 characters" />
              </Field>
              <Field label="Confirm Password" error={errors.confirm_password}>
                <input type="password" value={form.confirm_password} onChange={e => set('confirm_password', e.target.value)} className="input-field" />
              </Field>
            </div>
          )}

          {/* STEP 2: Hotel info */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-6">About your hotel</h2>
              <Field label="Number of rooms">
                <input type="number" min="1" value={form.room_count} onChange={e => set('room_count', e.target.value)} className="input-field" placeholder="e.g. 45" />
              </Field>
              <div>
                <label className="label-text">Tier</label>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  {(['BUDGET','STANDARD','PREMIUM'] as const).map(t => (
                    <button key={t} onClick={() => set('tier', t)}
                      className={`py-3 rounded-xl border text-sm font-bold transition-all ${form.tier === t ? 'border-[#00d4aa] bg-[#00d4aa]/10 text-[#00d4aa]' : 'border-white/10 text-white/50 hover:border-white/30'}`}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="label-text">Integration Level</label>
                <div className="space-y-3 mt-2">
                  {[
                    { key: 'api', label: 'API-First', en: 'For hotels with a PMS system', am: 'ለPMS ሥርዓት ያላቸው' },
                    { key: 'webhook', label: 'Webhook-Lite', en: 'For hotels with basic software', am: 'ለቀላል ሶፍትዌር ያላቸው' },
                    { key: 'dashboard', label: 'Dashboard', en: 'No system needed — web only', am: 'ምንም ሥርዓት አያስፈልግም' },
                  ].map(opt => (
                    <button key={opt.key} onClick={() => set('integration', opt.key as typeof form.integration)}
                      className={`w-full p-4 rounded-xl border text-left transition-all ${form.integration === opt.key ? 'border-[#00d4aa] bg-[#00d4aa]/10' : 'border-white/10 hover:border-white/30'}`}>
                      <div className="font-bold">{opt.label}</div>
                      <div className="text-sm text-white/50">{opt.en}</div>
                      <div className="amharic text-xs text-white/30 mt-1">{opt.am}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: KYC Documents */}
          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold mb-2">KYC Documents</h2>
              <p className="text-white/50 text-sm">Required for live key issuance. Reviewed within 3 business days.</p>
              <div className="space-y-4">
                {DOCS.map(doc => (
                  <label key={doc.key} className="flex items-start gap-4 p-4 border border-white/10 rounded-xl cursor-pointer hover:border-white/20 transition-colors">
                    <input type="file" accept="image/*,application/pdf" className="hidden"
                      onChange={() => setForm(p => ({ ...p, docs: { ...p.docs, [doc.key]: true } }))} />
                    <div className={`w-6 h-6 rounded flex-shrink-0 flex items-center justify-center mt-0.5 border transition-colors ${form.docs[doc.key] ? 'bg-[#00d4aa] border-[#00d4aa]' : 'border-white/20'}`}>
                      {form.docs[doc.key] && <span className="text-[#070b12] text-xs">✓</span>}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{doc.label}</div>
                      <div className="amharic text-xs text-white/40 mt-0.5">{doc.am}</div>
                    </div>
                  </label>
                ))}
              </div>
              <div className="bg-[#00d4aa]/10 border border-[#00d4aa]/20 rounded-lg p-4 text-sm text-white/70">
                <span className="text-[#00d4aa] font-bold">Note:</span> Your sandbox key is already active. Live key issued after document review.
              </div>
            </div>
          )}

          {/* STEP 4: Sandbox activated */}
          {step === 4 && (
            <div className="text-center space-y-6">
              <div className="flex justify-center mb-4">
                <svg className="w-24 h-24 text-[#00d4aa]" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2"
                    strokeDasharray="283" strokeDashoffset="283" className="draw-check" />
                  <path d="M30 50 L45 65 L70 35" fill="none" stroke="currentColor" strokeWidth="6"
                    strokeLinecap="round" strokeLinejoin="round" strokeDasharray="100" strokeDashoffset="100" className="draw-check" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold">Your sandbox account is ready.</h2>
              <p className="text-white/50">Live key will be issued after document review (3 business days).</p>

              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-300 font-bold">
                ⚠ This key is shown once. Save it now.
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-4 text-left">
                <div className="text-xs text-[#00d4aa] uppercase tracking-widest mb-2">Sandbox API Key</div>
                <div className="font-mono text-sm break-all text-white/80">{apiKey || 'll_test_demo_key_shown_once'}</div>
                <button onClick={() => { navigator.clipboard.writeText(apiKey); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
                  className="mt-3 text-xs font-bold text-[#00d4aa] hover:text-white transition-colors">
                  {copied ? '✓ Copied!' : 'Copy to clipboard'}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4">
                <button onClick={() => router.push('/dashboard')}
                  className="py-4 bg-[#00d4aa] text-[#070b12] font-bold rounded-xl hover:scale-[1.02] transition-transform">
                  Open Dashboard →
                </button>
                <a href="/api/docs" target="_blank"
                  className="py-4 border border-white/20 text-white font-bold rounded-xl hover:bg-white/5 transition-colors flex items-center justify-center">
                  View API Docs
                </a>
              </div>
            </div>
          )}

          {/* Navigation */}
          {step < 4 && (
            <div className="flex gap-4 mt-8">
              {step > 1 && (
                <button onClick={goBack} className="flex-1 py-4 border border-white/20 rounded-xl font-bold hover:bg-white/5 transition-colors">
                  ← Back
                </button>
              )}
              <button onClick={goNext} disabled={loading}
                className="flex-1 py-4 bg-[#00d4aa] text-[#070b12] font-bold rounded-xl hover:scale-[1.02] transition-transform disabled:opacity-50">
                {loading ? 'Creating account...' : step === 3 ? 'Activate Sandbox →' : 'Continue →'}
              </button>
            </div>
          )}
        </div>

        <p className="text-center text-white/30 text-sm mt-6">
          Already have an account? <a href="/" className="text-[#00d4aa] hover:underline">Return to home</a>
        </p>
      </div>

      <style jsx>{`
        .input-field {
          width: 100%;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 10px;
          padding: 12px 16px;
          color: white;
          outline: none;
          transition: border-color 150ms;
          font-size: 14px;
        }
        .input-field:focus { border-color: #00d4aa; }
        .input-field option { background: #0f1827; }
        .label-text { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 0.08em; }
      `}</style>
    </div>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-semibold text-white/50 uppercase tracking-widest">{label}</label>
      {children}
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  );
}
