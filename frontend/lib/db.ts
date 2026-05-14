import { openDB, IDBPDatabase } from 'idb';

const DB_NAME = 'lodge-link-pwa';
const DB_VERSION = 1;

export interface OfflineReferral {
  id: string;
  guest_name: string;
  hotel_id: string;
  handshake_code_hash: string;
  status: string;
  check_in_date: string;
  verified_locally: boolean;
  synced: boolean;
}

export const initDB = async (): Promise<IDBPDatabase> => {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('referrals')) {
        db.createObjectStore('referrals', { keyPath: 'id' });
      }
    },
  });
};

export const saveReferrals = async (referrals: OfflineReferral[]) => {
  const db = await initDB();
  const tx = db.transaction('referrals', 'readwrite');
  const store = tx.objectStore('referrals');
  
  // Clear and save the last 50
  await store.clear();
  for (const referral of referrals.slice(0, 50)) {
    await store.put(referral);
  }
  await tx.done;
};

export const getReferral = async (id: string): Promise<OfflineReferral | undefined> => {
  const db = await initDB();
  return db.get('referrals', id);
};

export const markAsVerifiedLocally = async (id: string) => {
  const db = await initDB();
  const referral = await db.get('referrals', id);
  if (referral) {
    referral.verified_locally = true;
    referral.status = 'COMPLETED';
    referral.synced = false;
    await db.put('referrals', referral);
  }
};
