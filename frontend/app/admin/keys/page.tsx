'use client';

export default function KeysManage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-light text-slate-200">API Key Management</h2>
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
        Global key management. Search for keys to revoke them.
        <div className="mt-4 flex max-w-md mx-auto">
          <input type="text" placeholder="Enter API Key ID or Prefix..." className="flex-1 bg-slate-950 border border-slate-800 rounded-l-lg px-4 py-2 text-slate-200 outline-none focus:border-teal-500" />
          <button className="bg-teal-600 hover:bg-teal-500 text-white px-4 py-2 rounded-r-lg">Search</button>
        </div>
      </div>
    </div>
  );
}
