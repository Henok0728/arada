'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginHotel, isApiError } from '@/lib/api';

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await loginHotel(email, password);
      if (isApiError(res)) {
        setError(res.error);
      } else {
        if (res.is_platform_admin) {
          router.push('/admin');
        } else {
          setError('Access denied. Not a platform administrator.');
        }
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-teal-400 italic tracking-tighter">Lodge-Link Admin</h1>
          <p className="text-slate-400 text-sm mt-2">Secure Gateway Authorization</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-900/30 border border-rose-500/50 text-rose-400 text-sm rounded-xl animate-shake">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Internal Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:border-teal-500 transition-all text-slate-200"
              placeholder="admin@lodge-link.et"
              required
            />
          </div>
          <div>
            <label className="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Access Cipher</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:border-teal-500 transition-all text-slate-200"
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-teal-500 hover:bg-teal-400 text-slate-950 font-black text-xs uppercase tracking-[0.2em] py-4 rounded-xl transition-all active:scale-95 disabled:opacity-50"
          >
            {loading ? 'Authorizing...' : 'Decrypt & Enter'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-slate-800 text-center">
          <a href="/" className="text-xs text-slate-500 hover:text-slate-300 transition-colors tracking-widest uppercase">
            Return to Public Access
          </a>
        </div>
      </div>
    </div>
  );
}
