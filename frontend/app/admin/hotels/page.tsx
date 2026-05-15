'use client';

import { useEffect, useState } from 'react';
import { apiCall } from '@/lib/api';
import Link from 'next/link';

export default function HotelsList() {
  const [hotels, setHotels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHotels();
  }, []);

  async function loadHotels() {
    setLoading(true);
    try {
      const data = await apiCall('/v1/admin/hotels');
      setHotels(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="text-slate-400">Loading hotels...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-light text-slate-200">Manage Hotels</h2>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/50">
              <th className="p-4 font-medium text-slate-400">Hotel Name</th>
              <th className="p-4 font-medium text-slate-400">City</th>
              <th className="p-4 font-medium text-slate-400">Status</th>
              <th className="p-4 font-medium text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {hotels.map(hotel => (
              <tr key={hotel.id} className="hover:bg-slate-800/20 transition-colors">
                <td className="p-4 text-slate-200 font-medium">{hotel.name}</td>
                <td className="p-4 text-slate-400">{hotel.city}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs ${
                    hotel.status === 'ACTIVE' ? 'bg-teal-900/50 text-teal-400' :
                    hotel.status === 'SUSPENDED' ? 'bg-rose-900/50 text-rose-400' :
                    'bg-amber-900/50 text-amber-400'
                  }`}>
                    {hotel.status}
                  </span>
                </td>
                <td className="p-4">
                  <Link href={`/admin/hotels/${hotel.id}`} className="text-teal-500 hover:text-teal-400 text-sm font-medium">
                    Manage →
                  </Link>
                </td>
              </tr>
            ))}
            {hotels.length === 0 && (
              <tr>
                <td colSpan={4} className="p-8 text-center text-slate-500">
                  No hotels found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
