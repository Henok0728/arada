'use client';
import { useRouter } from 'next/navigation';
import DemoBanner from '../components/DemoBanner';

export default function Home() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#070b12] text-white selection:bg-[#00d4aa] selection:text-[#070b12] overflow-x-hidden">
      <DemoBanner />

      {/* BACKGROUND MESH */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#00d4aa] rounded-full blur-[120px]" />
        <div className="absolute bottom-[10%] right-[-10%] w-[30%] h-[30%] bg-[#3b82f6] rounded-full blur-[100px]" />
      </div>

      {/* NAV BAR */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-[#070b12]/60 border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-12">
          <div className="text-2xl font-black tracking-tighter cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            Lodge<span className="text-[#00d4aa]">Link</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-xs font-black tracking-widest uppercase text-white/50">
            <a href="#network" className="hover:text-[#00d4aa] transition-colors">Network</a>
            <a href="#how-it-works" className="hover:text-[#00d4aa] transition-colors">How it works</a>
            <a href="#pricing" className="hover:text-[#00d4aa] transition-colors">Pricing</a>
            <a href="#docs" className="hover:text-[#00d4aa] transition-colors">Developers</a>
          </div>
        </div>
        <button 
          onClick={() => router.push('/onboarding')}
          className="bg-gradient-to-r from-[#00d4aa] to-[#3b82f6] text-[#070b12] text-xs font-black uppercase tracking-widest px-8 py-3 rounded-full hover:shadow-[0_0_30px_rgba(0,212,170,0.4)] transition-all transform hover:-translate-y-0.5 active:translate-y-0"
        >
          Join the Network
        </button>
      </nav>

      <main className="relative z-10">
        {/* HERO */}
        <section className="max-w-6xl mx-auto pt-24 md:pt-40 pb-32 text-center px-6">
          <div className="inline-flex items-center gap-3 mb-8 px-4 py-2 rounded-full border border-white/10 bg-white/5 text-xs font-bold tracking-[0.2em] uppercase animate-fade-up">
            <span className="flex h-2 w-2 rounded-full bg-[#00d4aa] animate-ping" />
            Active across Addis Ababa
          </div>
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8 animate-fade-up" style={{ animationDelay: '100ms' }}>
            The Premier <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40">Hotel Trust Network.</span>
          </h1>
          <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-12 leading-relaxed animate-fade-up" style={{ animationDelay: '200ms' }}>
            Turn "No Vacancy" into a high-margin revenue stream. Refer guests instantly via a cryptographically secure handshake. <br />
            <span className="amharic text-white/30 block mt-4">“ሙሉ ነው” የሚለውን መልስ ወደ ገቢ ይቀይሩ። በታማኝነት መረባችን እንግዶችን ያጋሩ።</span>
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6 animate-fade-up" style={{ animationDelay: '300ms' }}>
            <button 
              onClick={() => router.push('/dashboard')}
              className="group relative w-full sm:w-auto bg-white text-[#070b12] font-black text-sm uppercase tracking-widest px-12 py-5 rounded-2xl transition-all hover:shadow-[0_20px_40px_rgba(255,255,255,0.1)] active:scale-95"
            >
              Partner Login
            </button>
            <button 
              onClick={() => router.push('/onboarding')}
              className="w-full sm:w-auto bg-white/5 border border-white/10 text-white font-black text-sm uppercase tracking-widest px-12 py-5 rounded-2xl hover:bg-white/10 transition-all active:scale-95"
            >
              Register Hotel
            </button>
          </div>
        </section>

        {/* LOGO SWEEP */}
        <div className="relative py-20 border-y border-white/5 overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-40 bg-gradient-to-r from-[#070b12] to-transparent z-20" />
          <div className="absolute right-0 top-0 bottom-0 w-40 bg-gradient-to-l from-[#070b12] to-transparent z-20" />
          
          <div className="flex gap-20 animate-marquee whitespace-nowrap items-center w-max px-20">
            {[...Array(3)].map((_, j) => (
              <div key={j} className="flex gap-24 items-center">
                {['Skyline', 'Inter-Addis', 'Hilton', 'Sheraton', 'Radisson', 'Hyatt', 'Marriott', 'Capital'].map((logo, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="text-3xl font-black text-white/10 hover:text-white transition-all duration-500 transform hover:scale-110 tracking-tighter italic">
                      {logo.toUpperCase()}
                    </div>
                    <div className="text-[10px] font-black text-white/5 tracking-widest uppercase">HOTEL</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* STATS */}
        <section className="max-w-7xl mx-auto py-24 px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: 'Active Partners', value: '500+' },
            { label: 'Monthly Referrals', value: '12k+' },
            { label: 'Uptime SLA', value: '99.99%' },
            { label: 'Revenue Generated', value: '25M+' }
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className="text-4xl md:text-5xl font-black tracking-tighter text-[#00d4aa]">{stat.value}</div>
              <div className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mt-2">{stat.label}</div>
            </div>
          ))}
        </section>

        {/* FEATURES */}
        <section id="network" className="max-w-7xl mx-auto py-32 px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-6xl font-black tracking-tighter mb-6">Network of Trust.</h2>
            <p className="text-white/40 text-lg max-w-2xl mx-auto leading-relaxed">Infrastructure powering the future of Ethiopian hospitality. Secure, fast, and transparent.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { title: 'Real-time Sync', desc: 'Sync availability in 340ms across the entire network.', icon: '⚡' },
              { title: 'Trust Score', desc: 'Reputation management powered by transparent algorithms.', icon: '🛡️' },
              { title: 'Instant Payouts', desc: 'Automated settlement via Telebirr, CBE Birr & Dash.', icon: '💸' },
              { title: 'Handshake 2.0', desc: 'Offline validation for reliable guest check-ins.', icon: '🤝' }
            ].map((f, i) => (
              <div key={i} className="bg-white/5 border border-white/5 rounded-[2.5rem] p-10 hover:bg-white/10 transition-all duration-500">
                <div className="text-4xl mb-12">{f.icon}</div>
                <h3 className="text-xl font-bold mb-4 tracking-tight">{f.title}</h3>
                <p className="text-sm text-white/40 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section id="how-it-works" className="max-w-7xl mx-auto py-32 px-6 border-t border-white/5">
          <div className="grid lg:grid-cols-2 gap-20 items-center">
            <div>
              <h2 className="text-4xl md:text-5xl font-black tracking-tighter mb-12">How it works.</h2>
              <div className="space-y-12">
                {[
                  { step: '01', title: 'Hotel signals "No Vacancy"', desc: 'The front desk triggers an emergency referral fan-out to the trusted network.' },
                  { step: '02', title: 'Network nodes respond', desc: 'Nearby hotels with verified availability bid for the guest in real-time.' },
                  { step: '03', title: 'Handshake generated', desc: 'Guest receives a secure code. Destination hotel expects their arrival.' }
                ].map((item, i) => (
                  <div key={i} className="flex gap-8 group">
                    <div className="text-5xl font-black text-white/5 group-hover:text-[#00d4aa] transition-colors leading-none">{item.step}</div>
                    <div>
                      <h3 className="text-xl font-bold mb-2 tracking-tight">{item.title}</h3>
                      <p className="text-sm text-white/40 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-[3rem] p-4">
              <div className="bg-[#070b12] rounded-[2.5rem] p-8 border border-white/5 shadow-2xl">
                <div className="flex justify-between items-start mb-10">
                  <div className="h-12 w-12 bg-[#00d4aa] rounded-2xl flex items-center justify-center text-[#070b12] font-black text-xl">✓</div>
                  <div className="text-right">
                    <div className="text-[10px] font-black text-white/20 uppercase tracking-widest mb-1">Status</div>
                    <div className="text-xs font-bold text-[#00d4aa]">HANDSHAKE ACTIVE</div>
                  </div>
                </div>
                <div className="space-y-4 mb-10">
                  <div className="h-4 w-full bg-white/5 rounded-full" />
                  <div className="h-4 w-3/4 bg-white/5 rounded-full" />
                  <div className="h-4 w-1/2 bg-white/5 rounded-full" />
                </div>
                <div className="bg-white/5 p-6 rounded-2xl border border-white/10 text-center">
                  <div className="text-[10px] font-black text-white/30 uppercase tracking-[0.3em] mb-3">Validation Code</div>
                  <div className="text-4xl font-black tracking-[0.2em] font-mono text-white">LX-4291</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* DOCS */}
        <section id="docs" className="max-w-7xl mx-auto py-32 px-6 border-t border-white/5">
          <div className="flex flex-col lg:flex-row items-center gap-24">
            <div className="flex-1">
              <div className="text-xs font-black text-[#3b82f6] tracking-[0.3em] uppercase mb-6">API Core</div>
              <h2 className="text-4xl md:text-6xl font-black tracking-tighter mb-8 leading-tight">Integration <br /> made effortless.</h2>
              <p className="text-xl text-white/50 mb-12 leading-relaxed">
                Connect your Property Management System (PMS) to the LodgeLink network in minutes.
              </p>
              <div className="space-y-6">
                {['Full OpenAPI Specification', 'Webhook Event Stream', 'Production Environments'].map((item, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="h-6 w-6 rounded-full border border-white/20 flex items-center justify-center shrink-0">
                      <div className="h-1.5 w-1.5 rounded-full bg-white" />
                    </div>
                    <div className="text-sm font-bold">{item}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex-1 w-full overflow-hidden bg-[#0a0f18] border border-white/10 rounded-3xl shadow-2xl">
              <div className="flex items-center gap-2 px-6 py-4 bg-white/5 border-b border-white/10">
                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
              </div>
              <div className="p-8 overflow-x-auto">
                <pre className="text-xs font-mono leading-loose">
                  <span className="text-[#ff79c6]">const</span> response = <span className="text-[#ff79c6]">await</span> fetch(<span className="text-[#f1fa8c]">'https://api.lodge-link.et/v1/referrals'</span>, {'{'}
                  {'\n  '}method: <span className="text-[#f1fa8c]">'POST'</span>,
                  {'\n  '}headers: {'{'}
                  {'\n    '}<span className="text-[#f1fa8c]">'Authorization'</span>: <span className="text-[#f1fa8c]">'Bearer sk_live_...'</span>
                  {'\n  }'}
                  {'\n}'});
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* PRICING */}
        <section id="pricing" className="max-w-7xl mx-auto py-32 px-6 border-t border-white/5">
          <div className="text-center mb-24">
            <h2 className="text-4xl md:text-6xl font-black tracking-tighter mb-8">Transparent pricing.</h2>
            <p className="text-white/40 text-lg max-w-xl mx-auto">Start for free. Scale as you earn from the network.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { name: 'Starter', price: 'Free', unit: '/50 refs', active: false },
              { name: 'Network', price: '2%', unit: '/referral', active: true },
              { name: 'Enterprise', price: 'Custom', unit: '', active: false }
            ].map((p, i) => (
              <div key={i} className={`flex flex-col p-12 rounded-[2.5rem] border transition-all duration-500 ${p.active ? 'bg-white text-[#070b12] border-white' : 'bg-white/5 border-white/10'}`}>
                <div className="text-xs font-black uppercase tracking-widest mb-4 opacity-50">{p.name}</div>
                <div className="flex items-baseline gap-2 mb-12">
                  <span className="text-5xl font-black tracking-tighter">{p.price}</span>
                  <span className="text-sm font-bold opacity-40">{p.unit}</span>
                </div>
                <button className={`w-full py-5 rounded-2xl text-xs font-black uppercase tracking-widest ${p.active ? 'bg-[#070b12] text-white' : 'bg-white/10 text-white'}`}>
                  Join {p.name}
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-7xl mx-auto py-32 px-6">
          <div className="bg-gradient-to-r from-[#00d4aa] to-[#3b82f6] rounded-[3rem] p-12 md:p-24 text-center text-[#070b12]">
            <h2 className="text-4xl md:text-7xl font-black tracking-tighter mb-8 leading-[0.9]">Join the future of <br className="hidden md:block" /> hospitality.</h2>
            <p className="text-lg md:text-xl font-bold mb-12 opacity-80 max-w-2xl mx-auto">Registration takes less than 2 minutes. Get your secure access today.</p>
            <button onClick={() => router.push('/onboarding')} className="bg-[#070b12] text-white text-xs font-black uppercase tracking-widest px-12 py-5 rounded-2xl hover:scale-105 active:scale-95 transition-all">
              Start Registration
            </button>
          </div>
        </section>
      </main>

      {/* FOOTER */}
      <footer className="max-w-7xl mx-auto py-20 px-6 border-t border-white/5 text-center">
        <div className="text-2xl font-black tracking-tighter mb-8">
          Lodge<span className="text-[#00d4aa]">Link</span>
        </div>
        <div className="flex flex-wrap justify-center gap-8 text-[10px] font-black uppercase tracking-widest text-white/30 mb-8">
          <a href="#" className="hover:text-white transition-colors">Privacy</a>
          <a href="#" className="hover:text-white transition-colors">Terms</a>
          <a href="#" className="hover:text-white transition-colors">Contact</a>
          <a href="#" className="hover:text-white transition-colors">GitHub</a>
        </div>
        <div className="text-[10px] text-white/10 font-mono uppercase tracking-[0.2em]">
          &copy; 2026 LodgeLink Inc. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
