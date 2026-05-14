'use client';
import { useTranslation } from 'react-i18next';

export default function Tier1Sandbox({ onNext }: { onNext: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-brand-100 text-center">
      <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-4">{t('kyc_step1_title')}</h3>
      <p className="text-gray-600 mb-8">{t('kyc_step1_desc')}</p>
      
      <div className="bg-gray-50 p-4 rounded-lg mb-8 text-left border border-gray-200">
        <p className="text-sm text-gray-500 mb-1">Sandbox API Key</p>
        <code className="text-sm font-mono text-gray-900 break-all">ll_test_2aB5nMkRvXqZwPjLcDhGiYeNtOuA9kFmBvWz3pQ7rCdEhJlS1xT</code>
      </div>

      <button onClick={onNext} className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-md transition-colors">
        Continue to Live Key KYC
      </button>
    </div>
  );
}
