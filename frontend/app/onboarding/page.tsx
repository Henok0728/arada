'use client';
import { useState, useEffect } from 'react';
import Tier1Sandbox from '../../components/kyc/Tier1Sandbox';
import Tier2DocumentUpload from '../../components/kyc/Tier2DocumentUpload';
import AgreementReview from '../../components/kyc/AgreementReview';

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-3xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-12">
          <div className="flex items-center justify-between relative">
            <div className="absolute left-0 top-1/2 w-full h-1 bg-gray-200 -z-10 transform -translate-y-1/2"></div>
            <div className={`absolute left-0 top-1/2 h-1 bg-brand-500 -z-10 transform -translate-y-1/2 transition-all duration-300 ${step === 1 ? 'w-0' : step === 2 ? 'w-1/2' : 'w-full'}`}></div>
            
            {[1, 2, 3].map((num) => (
              <div key={num} className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${step >= num ? 'bg-brand-600 text-white shadow-md' : 'bg-gray-200 text-gray-500'}`}>
                {num}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs font-medium text-gray-500">
            <span>Sandbox</span>
            <span>Documents</span>
            <span>Agreement</span>
          </div>
        </div>

        {/* Form Content */}
        {step === 1 && <Tier1Sandbox onNext={() => setStep(2)} />}
        {step === 2 && <Tier2DocumentUpload onNext={() => setStep(3)} />}
        {step === 3 && <AgreementReview onFinish={() => alert("KYC Submitted Successfully!")} />}
      </div>
    </div>
  );
}
