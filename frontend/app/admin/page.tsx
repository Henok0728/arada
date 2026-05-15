'use client';

import { useEffect, useState } from 'react';
import { apiCall } from '@/lib/api';

export default function AdminDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await apiCall('/v1/admin/stats');
        setStats(data);
      } catch (err) {
        console.error("Failed to load stats", err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) return <div className="text-slate-400">Loading platform metrics...</div>;
  if (!stats) return <div className="text-red-400">Failed to load platform metrics.</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Hotels" value={stats.hotels.total} subtitle={`${stats.hotels.pending_kyc} pending KYC`} />
        <StatCard title="Active Keys" value={stats.api_keys.live_keys_issued} subtitle={`${stats.api_keys.sandbox_keys_active} sandbox`} />
        <StatCard title="Revenue (ETB)" value={`ETB ${stats.revenue.commission_earned_etb_all_time}`} subtitle="All time" />
        <StatCard title="Referrals" value={stats.referrals.total_all_time} subtitle={`${Math.round(stats.referrals.fulfillment_rate * 100)}% fulfillment`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Platform Trust Score</h3>
          <div className="flex items-end gap-4">
            <div className="text-5xl font-light text-teal-400">{stats.trust.avg_platform_trust_score}/100</div>
            <div className="text-slate-500 mb-2">Network Average</div>
          </div>
          <div className="mt-6 flex items-center gap-2 text-sm text-slate-400">
            <span className="w-2 h-2 rounded-full bg-teal-500"></span>
            {stats.trust.hotels_with_score} hotels tracked
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <a href="/admin/kyc" className="block p-4 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <div className="font-medium text-slate-200">Review KYC Queue</div>
              <div className="text-sm text-slate-400">{stats.hotels.pending_kyc} pending</div>
            </a>
            <a href="/admin/hotels" className="block p-4 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <div className="font-medium text-slate-200">Manage Hotels</div>
              <div className="text-sm text-slate-400">Suspend or assign plans</div>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle }: { title: string, value: string | number, subtitle: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
      <div className="text-slate-400 text-sm">{title}</div>
      <div className="mt-4 text-3xl font-light text-slate-200">{value}</div>
      <div className="mt-2 text-xs text-slate-500">{subtitle}</div>
    </div>
  );
}
