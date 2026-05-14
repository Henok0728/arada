'use client';
import { useTranslation } from 'react-i18next';

export default function Tier2DocumentUpload({ onNext }: { onNext: () => void }) {
  const { t } = useTranslation();
  
  const docs = [
    "Business Registration Certificate",
    "Tax Identification Number (TIN)",
    "Operating License",
    "Manager's National ID"
  ];

  return (
    <div className="bg-white p-8 rounded-xl shadow-sm border border-brand-100">
      <h3 className="text-2xl font-bold text-gray-900 mb-4">{t('kyc_step2_title')}</h3>
      <p className="text-gray-600 mb-8">{t('kyc_step2_desc')}</p>

      <div className="space-y-4 mb-8">
        {docs.map((doc, i) => (
          <div key={i} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-gray-50">
            <span className="font-medium text-gray-700">{doc}</span>
            <button className="px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
              {t('upload_button')}
            </button>
          </div>
        ))}
      </div>

      <button onClick={onNext} className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-md transition-colors">
        Save & Continue
      </button>
    </div>
  );
}
