'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { loginHotel } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const res = await loginHotel(email, password);
    if ('error' in res) {
      setError(res.error);
      setLoading(false);
    } else {
      router.push('/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-white flex flex-col items-center justify-center py-16 px-4">
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-10">
          <div className="text-2xl font-black tracking-tighter mb-4 cursor-pointer" onClick={() => router.push('/')}>
            Lodge<span className="text-[#00d4aa]">Link</span>
          </div>
          <h1 className="text-4xl font-black tracking-tighter mb-2 italic">{t('login_title')}</h1>
          <p className="text-white/40 text-sm">{t('login_subtitle')}</p>
        </div>

        <div className="bg-white/[0.03] border border-white/5 rounded-[2.5rem] p-10 backdrop-blur-xl shadow-2xl">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-[10px] font-black text-white/30 mb-2 uppercase tracking-[0.3em]">{t('login_email')}</label>
              <input 
                type="email" 
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                className="w-full bg-black/20 border border-white/10 rounded-2xl px-6 py-4 focus:outline-none focus:border-[#00d4aa] transition-all" 
                placeholder="admin@hotel.com" 
                required
              />
            </div>
            <div>
              <label className="block text-[10px] font-black text-white/30 mb-2 uppercase tracking-[0.3em]">{t('login_password')}</label>
              <input 
                type="password" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                className="w-full bg-black/20 border border-white/10 rounded-2xl px-6 py-4 focus:outline-none focus:border-[#00d4aa] transition-all" 
                placeholder="••••••••" 
                required
              />
            </div>
            
            {error && (
              <div className="text-red-500 text-sm font-bold text-center bg-red-500/10 p-3 rounded-xl border border-red-500/20">
                {error}
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading} 
              className="w-full mt-4 bg-gradient-to-r from-[#00d4aa] to-[#3b82f6] text-[#070b12] font-black text-sm uppercase tracking-widest py-5 rounded-2xl hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
            >
              {loading ? t('login_loading') : t('login_button')}
            </button>
          </form>
          
          <div className="mt-8 text-center">
            <button 
              onClick={() => router.push('/onboarding')}
              className="text-[10px] font-black text-white/40 uppercase tracking-widest hover:text-[#00d4aa] transition-colors"
            >
              {t('login_register_prompt')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
