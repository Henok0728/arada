'use client';
import { useTranslation } from 'react-i18next';

export default function AgreementReview({ onFinish }: { onFinish: () => void }) {
  const { t } = useTranslation();

  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-brand-100">
      <h3 className="text-2xl font-bold text-gray-900 mb-4">{t('kyc_step3_title')}</h3>
      <p className="text-gray-600 mb-8">{t('kyc_step3_desc')}</p>

      <div className="h-48 overflow-y-auto bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 text-sm text-gray-700">
        <h4 className="font-bold mb-2">Lodge-Link Partner Agreement</h4>
        <p className="mb-2">1. Agreement to referral commission rate (1.5–3% of first night&apos;s rate).</p>
        <p className="mb-2">2. Agreement to referral response SLA (must respond to incoming referral within 15 minutes during business hours).</p>
        <p>3. Maintaining price parity for referred guests.</p>
      </div>

      <div className="flex items-start mb-8">
        <input id="agreement" type="checkbox" className="mt-1 h-4 w-4 text-brand-600 border-gray-300 rounded" />
        <label htmlFor="agreement" className="ml-2 block text-sm text-gray-900">
          I have read and agree to the Lodge-Link Partner Agreement and Terms of Service. I authorize my digital signature below.
        </label>
      </div>

      <button onClick={onFinish} className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-md transition-colors">
        {t('submit_kyc_button')}
      </button>
    </div>
  );
}
