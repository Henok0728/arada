'use client';
import { useEffect, useRef, useState } from 'react';
import DemoBanner from '../components/DemoBanner';
import Link from 'next/link';

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);
  const observerRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    setMounted(true);
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    observerRefs.current.forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, []);

  const addToRefs = (el: HTMLElement | null) => {
    if (el && !observerRefs.current.includes(el)) {
      observerRefs.current.push(el);
    }
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen flex flex-col selection:bg-[#00d4aa]/30">
      <DemoBanner />

      {/* HERO SECTION */}
      <section className="relative min-h-[90vh] flex flex-col items-center justify-center px-6 overflow-hidden">
        {/* Radial Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#00d4aa]/5 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="relative z-10 text-center max-w-4xl mx-auto">
          <h1 className="hero-letter-spacing text-4xl md:text-6xl lg:text-7xl font-bold leading-[1.1] mb-4">
            You&apos;re Full Tonight.<br />
            <span className="text-[#00d4aa]">Your Guest Doesn&apos;t Have to Leave.</span>
          </h1>
          <h2 className="amharic text-xl md:text-2xl text-white/70 mb-8 font-medium">
            ሆቴልዎ ሞልቷል። እንግዳዎ መሄድ አያስፈልጋቸውም።
          </h2>
          <p className="text-lg md:text-xl text-white/60 mb-10 max-w-2xl mx-auto leading-relaxed">
            Lodge-Link connects Addis Ababa hotels into a real-time referral network. 
            One tap. Trusted partners. No guest left behind.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <button className="shimmer-btn btn-primary w-full sm:w-auto min-w-[200px]">
              Login as Hotel A →
            </button>
            <button className="btn-outline w-full sm:w-auto min-w-[200px]">
              Login as Hotel B →
            </button>
          </div>

          <div className="flex items-center justify-center gap-2">
            <div className="px-3 py-1 glass-card border-white/20 text-xs font-bold text-[#00d4aa] uppercase tracking-wider">
              ✦ 5 hotels live in Addis Ababa
            </div>
          </div>
        </div>

        {/* Scroll Chevron */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-[bounce-slow_3s_infinite] opacity-50">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-24 px-6 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: 1, icon: '🏨', title: 'Hotel A is Full', desc: 'Receptionist taps FIND ROOM in the dashboard.' },
              { step: 2, icon: '⚡', title: 'Instant Scan', desc: 'Lodge-Link checks 5 nearby hotels in 340ms.' },
              { step: 3, icon: '🤝', title: 'Handshake', desc: 'Guest walks to Hotel B with a 6-character code.' }
            ].map((item, i) => (
              <div 
                key={item.step} 
                ref={addToRefs}
                className="reveal glass-card p-8 group hover:bg-white/[0.08] transition-colors"
                style={{ transitionDelay: `${i * 150}ms` }}
              >
                <div className="text-4xl font-bold text-white/10 mb-4 group-hover:text-[#00d4aa]/20 transition-colors">0{item.step}</div>
                <div className="text-4xl mb-4">{item.icon}</div>
                <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                <p className="text-white/50">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TRUST SCORE STRIP */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="max-w-4xl mx-auto text-center">
          <h2 ref={addToRefs} className="reveal text-3xl md:text-4xl font-bold mb-16">
            Every referral builds trust.<br />
            <span className="text-[#00d4aa]">Trust drives the network.</span>
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {[
              { label: 'Fulfillment Rate', value: '94%', color: '#00d4aa' },
              { label: 'Price Honesty', value: '96%', color: '#3b82f6' },
              { label: 'Guest Feedback', value: '4.8/5', color: '#ffb800' }
            ].map((stat, i) => (
              <div key={stat.label} ref={addToRefs} className="reveal flex flex-col items-center">
                <div className="text-4xl font-bold mb-4">{stat.value}</div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden mb-4">
                  <div 
                    className="h-full rounded-full transition-all duration-[1.5s] ease-out delay-500"
                    style={{ 
                      width: stat.label.includes('/') ? '96%' : stat.value, 
                      backgroundColor: stat.color,
                      transform: 'translateX(-100%)' // Initially hidden
                    }}
                    // Note: We'll use a CSS trick to animate this when .visible is added
                  />
                </div>
                <div className="text-sm font-medium text-white/50 uppercase tracking-widest">{stat.label}</div>
              </div>
            ))}
          </div>
          
          <style jsx>{`
            .reveal.visible .h-full {
              transform: translateX(0) !important;
            }
          `}</style>
        </div>
      </section>

      {/* ETHIOPIAN CONTEXT STRIP */}
      <section className="py-24 px-6 bg-[#00d4aa]/5">
        <div className="max-w-4xl mx-auto">
          <h2 ref={addToRefs} className="reveal text-center text-3xl font-bold mb-12">
            Built for Addis. Ready for East Africa.
          </h2>
          
          <div className="grid grid-cols-2 gap-4">
            {[
              '📅 Timkat & Meskel demand alerts',
              '📱 Offline handshake codes',
              '💬 SMS via AfricasTalking',
              '🌍 ETB-native · Telebirr-ready'
            ].map((text, i) => (
              <div 
                key={text} 
                ref={addToRefs}
                className="reveal glass-card p-6 flex items-center justify-center text-center font-medium hover:-translate-y-1 transition-transform border-white/5"
                style={{ transitionDelay: `${i * 100}ms` }}
              >
                {text}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="mt-auto border-t border-white/10 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div>
            <div className="text-2xl font-bold mb-2">Lodge-Link</div>
            <div className="amharic text-white/50 text-sm">ሆቴሎችን የሚያገናኝ ዘመናዊ ኔትወርክ</div>
            <div className="text-white/30 text-sm mt-4 italic">
              Phase 1 MVP — Built with FastAPI, PostgreSQL, Redis, Next.js
            </div>
          </div>
          
          <div className="flex gap-6">
            <Link href="https://github.com/eyob2one/arada" className="text-white/40 hover:text-white transition-colors">
              GitHub Repository
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
