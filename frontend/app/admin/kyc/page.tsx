'use client';

import { useEffect, useState } from 'react';
import { apiCall } from '@/lib/api';

export default function KycQueue() {
  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<string | null>(null);
  const [liveKey, setLiveKey] = useState<string | null>(null);

  useEffect(() => {
    loadQueue();
  }, []);

  async function loadQueue() {
    setLoading(true);
    try {
      const data = await apiCall('/v1/admin/kyc/queue');
      setQueue(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function approveKyc(hotelId: string) {
    setApproving(hotelId);
    try {
      const res = await apiCall(`/v1/admin/kyc/${hotelId}/approve`, {
        method: 'POST',
        body: JSON.stringify({ reviewer_notes: 'Approved via dashboard' })
      });
      setLiveKey(res.live_api_key);
      await loadQueue();
    } catch (err) {
      console.error(err);
      alert('Failed to approve KYC');
    } finally {
      setApproving(null);
    }
  }

  async function rejectKyc(hotelId: string) {
    const reason = prompt("Enter rejection reason:");
    if (!reason) return;
    setRejecting(hotelId);
    try {
      await apiCall(`/v1/admin/kyc/${hotelId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason })
      });
      await loadQueue();
    } catch (err) {
      console.error(err);
      alert('Failed to reject KYC');
    } finally {
      setRejecting(null);
    }
  }

  if (loading) return <div className="text-slate-400">Loading KYC queue...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-light text-slate-200">KYC Review Queue</h2>
        <div className="px-3 py-1 bg-slate-800 text-slate-300 rounded-full text-sm">
          {queue.length} Pending
        </div>
      </div>

      {liveKey && (
        <div className="bg-teal-900/30 border border-teal-500/50 p-6 rounded-xl animate-fade-in">
          <h3 className="text-teal-400 font-medium mb-2">Live API Key Generated</h3>
          <p className="text-sm text-slate-300 mb-4">This key is returned exactly once. Provide this to the hotel securely.</p>
          <code className="block p-4 bg-slate-950 text-teal-300 rounded-lg select-all break-all text-sm font-mono">
            {liveKey}
          </code>
          <button 
            onClick={() => setLiveKey(null)}
            className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {queue.length === 0 ? (
        <div className="text-slate-500 text-center py-12 bg-slate-900/50 rounded-xl border border-slate-800">
          No pending KYC applications.
        </div>
      ) : (
        <div className="grid gap-6">
          {queue.map(item => (
            <div key={item.hotel_id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row gap-6 justify-between items-start">
              <div>
                <h3 className="text-xl text-slate-200 font-medium">{item.display_name}</h3>
                <div className="mt-2 space-y-1 text-sm text-slate-400">
                  <p>Email: <span className="text-slate-300">{item.email}</span></p>
                  <p>Phone: <span className="text-slate-300">{item.phone}</span></p>
                  <p>Location: <span className="text-slate-300">{item.city}</span></p>
                  <p>Submitted: <span className="text-slate-300">{new Date(item.submitted_at).toLocaleDateString()}</span> ({item.days_waiting} days ago)</p>
                </div>
                <div className="mt-4">
                  <p className="text-sm text-slate-500 mb-2">Documents</p>
                  <div className="flex gap-2">
                    {item.documents.map((doc: string) => (
                      <span key={doc} className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs">
                        {doc}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 md:flex-col md:w-48">
                <button
                  onClick={() => approveKyc(item.hotel_id)}
                  disabled={approving === item.hotel_id || rejecting === item.hotel_id}
                  className="w-full py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {approving === item.hotel_id ? 'Approving...' : 'Approve & Issue Key'}
                </button>
                <button
                  onClick={() => rejectKyc(item.hotel_id)}
                  disabled={approving === item.hotel_id || rejecting === item.hotel_id}
                  className="w-full py-2 bg-rose-900/50 text-rose-400 hover:bg-rose-900/80 rounded-lg transition-colors border border-rose-900 disabled:opacity-50"
                >
                  {rejecting === item.hotel_id ? 'Rejecting...' : 'Reject'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
