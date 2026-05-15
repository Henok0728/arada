'use client';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

import QueryProvider from '../../components/QueryProvider';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  return (
    <QueryProvider>
    <div className="min-h-screen bg-[#070b12] text-white flex flex-col">
      {/* Dashboard Nav */}
      <nav className="border-b border-white/10 px-6 py-4 flex justify-between items-center bg-white/5 backdrop-blur-md sticky top-0 z-50">
        <Link href="/dashboard" className="text-xl font-bold tracking-tight">
          Lodge<span className="text-[#00d4aa]">-Link</span>
        </Link>
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-full bg-[#00d4aa]/20 border border-[#00d4aa]/40 flex items-center justify-center text-[#00d4aa] font-bold text-xs">
            H
          </div>
          <button 
            onClick={() => {
              localStorage.removeItem('ll_token');
              router.push('/');
            }}
            className="text-sm text-white/50 hover:text-white transition-colors"
          >
            Logout
          </button>
        </div>
      </nav>

      <main className="flex-grow p-6 pb-32">
        {children}
      </main>

      {/* Persistent FIND ROOM FAB */}
      <button 
        onClick={() => router.push('/dashboard/referral')}
        className="fixed bottom-8 right-8 z-[60] bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-4 rounded-full shadow-[0_0_30px_rgba(220,38,38,0.4)] transition-all hover:scale-105 active:scale-95 flex items-center gap-3 group"
      >
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
        </span>
        FIND ROOM
        <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
      </button>
    </div>
    </QueryProvider>
  );
}
