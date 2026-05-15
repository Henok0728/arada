'use client';

import { useEffect, useState } from 'react';
import { apiCall } from '@/lib/api';

export default function AuditLogList() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  async function loadLogs() {
    setLoading(true);
    try {
      const data = await apiCall('/v1/admin/audit-log');
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="text-slate-400">Loading audit log...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-light text-slate-200">Security Audit Log</h2>
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/50">
              <th className="p-4 font-medium text-slate-400">Timestamp</th>
              <th className="p-4 font-medium text-slate-400">Actor</th>
              <th className="p-4 font-medium text-slate-400">Action</th>
              <th className="p-4 font-medium text-slate-400">Target</th>
              <th className="p-4 font-medium text-slate-400">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {logs.map(log => (
              <tr key={log.id} className="hover:bg-slate-800/20 transition-colors">
                <td className="p-4 text-slate-400 font-mono whitespace-nowrap">
                  {new Date(log.created_at).toLocaleString()}
                </td>
                <td className="p-4 text-slate-300">{log.actor_email || 'System'}</td>
                <td className="p-4">
                  <span className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs font-mono">
                    {log.action}
                  </span>
                </td>
                <td className="p-4 text-slate-400 font-mono text-xs">
                  {log.target_type}: {log.target_id || 'null'}
                </td>
                <td className="p-4 text-slate-500 font-mono text-xs truncate max-w-xs">
                  {log.metadata ? JSON.stringify(log.metadata) : '-'}
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-500">
                  No audit logs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
