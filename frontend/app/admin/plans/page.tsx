'use client';

import { useEffect, useState } from 'react';
import { apiCall } from '@/lib/api';

export default function PlansList() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPlans();
  }, []);

  async function loadPlans() {
    setLoading(true);
    try {
      const data = await apiCall('/v1/admin/plans');
      setPlans(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="text-slate-400">Loading plans...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-light text-slate-200">Subscription Plans</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map(plan => (
          <div key={plan.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-medium text-slate-200">{plan.display_name}</h3>
            <div className="mt-4 text-3xl font-light text-teal-400">
              {plan.price_etb ? `ETB ${plan.price_etb}` : 'Custom'}
              <span className="text-sm text-slate-500 ml-2">/ mo</span>
            </div>
            <div className="mt-6 flex items-center justify-between">
              <span className={`px-2 py-1 rounded text-xs ${plan.is_active ? 'bg-teal-900/50 text-teal-400' : 'bg-slate-800 text-slate-400'}`}>
                {plan.is_active ? 'Active' : 'Inactive'}
              </span>
              <button className="text-sm text-slate-400 hover:text-slate-200">Edit →</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
