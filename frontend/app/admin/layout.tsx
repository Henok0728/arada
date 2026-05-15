'use client';

import { ReactNode, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { getToken } from '@/lib/api';

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const token = getToken();
    const isAdmin = localStorage.getItem('ll_is_admin') === 'true';

    if (!token || !isAdmin) {
      if (pathname !== '/admin/login') {
        router.push('/admin/login');
      }
    } else {
      setIsAuthorized(true);
    }
  }, [pathname, router]);

  if (!isAuthorized && pathname !== '/admin/login') {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500 tracking-widest uppercase text-[10px]">Authorizing...</div>;
  }

  // Hide sidebar/header on login page
  if (pathname === '/admin/login') {
    return <>{children}</>;
  }

  const navItems = [
    { name: 'Overview', href: '/admin' },
    { name: 'KYC Queue', href: '/admin/kyc' },
    { name: 'Hotels', href: '/admin/hotels' },
    { name: 'Plans', href: '/admin/plans' },
    { name: 'API Keys', href: '/admin/keys' },
    { name: 'Audit Log', href: '/admin/audit' },
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 flex overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-xl font-bold text-teal-400 italic tracking-tighter">Lodge-Link Admin</h1>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-4 py-2 rounded-lg transition-all ${
                pathname === item.href
                  ? 'bg-teal-500/10 text-teal-400 font-bold border border-teal-500/20 shadow-[0_0_15px_-5px_rgba(20,184,166,0.3)]'
                  : 'text-slate-500 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <span className="text-sm tracking-tight">{item.name}</span>
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-800">
          <Link href="/dashboard" className="text-[10px] font-bold text-slate-600 hover:text-slate-400 transition-colors uppercase tracking-widest">
            ← Switch to Hotel Context
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-md sticky top-0 z-20">
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-[0.2em]">
            {navItems.find((item) => item.href === pathname)?.name || 'Platform Control'}
          </h2>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 px-3 py-1 bg-teal-500/10 border border-teal-500/20 text-teal-500 rounded-full text-[10px] font-black uppercase tracking-widest">
              <span className="w-1 h-1 bg-teal-500 rounded-full animate-pulse" />
              admin:platform
            </div>
            <button 
              onClick={() => {
                localStorage.removeItem('ll_token');
                localStorage.removeItem('ll_is_admin');
                router.push('/admin/login');
              }}
              className="text-[10px] font-black text-slate-500 hover:text-rose-400 transition-colors uppercase tracking-widest"
            >
              Sign Out
            </button>
          </div>
        </header>
        <div className="p-8 flex-1 overflow-auto bg-[radial-gradient(circle_at_50%_0%,rgba(15,23,42,1)_0%,rgba(2,6,23,1)_100%)]">
          {children}
        </div>
      </main>
    </div>
  );
}
