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
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">Authenticating...</div>;
  }

  const navItems = [
    { name: 'Dashboard', href: '/admin' },
    { name: 'KYC Queue', href: '/admin/kyc' },
    { name: 'Hotels', href: '/admin/hotels' },
    { name: 'Plans', href: '/admin/plans' },
    { name: 'API Keys', href: '/admin/keys' },
    { name: 'Audit Log', href: '/admin/audit' },
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-xl font-bold text-teal-400">Lodge-Link Admin</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-4 py-2 rounded-lg transition-colors ${
                pathname === item.href
                  ? 'bg-teal-900/50 text-teal-400 font-medium'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              {item.name}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-800">
          <Link href="/dashboard" className="text-sm text-slate-500 hover:text-slate-300 transition-colors">
            ← Back to Hotel View
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
          <h2 className="text-lg font-medium text-slate-300">
            {navItems.find((item) => item.href === pathname)?.name || 'Admin'}
          </h2>
          <div className="flex items-center gap-4">
            <div className="px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-500 rounded-full text-xs font-mono">
              admin:platform
            </div>
          </div>
        </header>
        <div className="p-8 flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
