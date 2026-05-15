'use client';

import { useEffect } from 'react';

const OLD_HOSTNAME = 'arada-faqzwaex5-eyob2ones-projects.vercel.app';
const NEW_URL = 'https://arada-rho.vercel.app';

export default function RedirectGuard() {
  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.hostname === OLD_HOSTNAME) {
      window.location.replace(NEW_URL);
    }
  }, []);

  return null;
}
