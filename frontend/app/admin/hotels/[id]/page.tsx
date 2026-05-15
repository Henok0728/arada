'use client';

import { useEffect, useState } from 'react';
import { apiCall } from '@/lib/api';
import { useParams } from 'next/navigation';

export default function HotelManage() {
  const params = useParams();
  const hotelId = params.id as string;
  const [hotel, setHotel] = useState<any>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [hotelData, plansData] = await Promise.all([
        apiCall(`/v1/admin/hotels/${hotelId}`),
        apiCall('/v1/admin/plans')
      ]);
      setHotel(hotelData);
      setPlans(plansData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(action: 'suspend' | 'reinstate') {
    const reason = action === 'suspend' ? prompt("Reason for suspension:") : 'reinstated';
    if (action === 'suspend' && !reason) return;
    
    try {
      await apiCall(`/v1/admin/hotels/${hotelId}/${action}`, {
        method: 'POST',
        body: JSON.stringify({ reason })
      });
      await loadData();
    } catch (err) {
      console.error(err);
      alert(`Failed to ${action} hotel`);
    }
  }

  async function assignPlan(planId: string) {
    if (!confirm('Assign new plan?')) return;
    try {
      await apiCall(`/v1/admin/hotels/${hotelId}/plan`, {
        method: 'POST',
        body: JSON.stringify({ plan_id: planId, effective_from: new Date().toISOString() })
      });
      await loadData();
      alert('Plan assigned');
    } catch (err) {
      console.error(err);
      alert('Failed to assign plan');
    }
  }

  if (loading) return <div className="text-slate-400">Loading...</div>;
  if (!hotel) return <div className="text-rose-400">Hotel not found.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h2 className="text-2xl font-light text-slate-200">{hotel.name}</h2>
        <span className={`px-2 py-1 rounded text-xs ${
          hotel.status === 'ACTIVE' ? 'bg-teal-900/50 text-teal-400' :
          hotel.status === 'SUSPENDED' ? 'bg-rose-900/50 text-rose-400' :
          'bg-amber-900/50 text-amber-400'
        }`}>
          {hotel.status}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Lifecycle Management</h3>
          <div className="flex gap-4">
            {hotel.status !== 'SUSPENDED' ? (
              <button onClick={() => updateStatus('suspend')} className="px-4 py-2 bg-rose-900/50 text-rose-400 hover:bg-rose-900/80 rounded-lg transition-colors border border-rose-900">
                Suspend Hotel
              </button>
            ) : (
              <button onClick={() => updateStatus('reinstate')} className="px-4 py-2 bg-teal-900/50 text-teal-400 hover:bg-teal-900/80 rounded-lg transition-colors border border-teal-900">
                Reinstate Hotel
              </button>
            )}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-medium text-slate-200 mb-4">Billing Plan</h3>
          <div className="flex gap-2 flex-wrap">
            {plans.map(p => (
              <button 
                key={p.id}
                onClick={() => assignPlan(p.id)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors border border-slate-700"
              >
                Assign {p.display_name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
