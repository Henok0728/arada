'use client';
import { useTranslation } from 'react-i18next';
import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function LandingPage() {
  const { t, i18n } = useTranslation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'en' ? 'am' : 'en';
    i18n.changeLanguage(nextLang);
  };

  if (!mounted) return null; // Avoid hydration mismatch

  return (
    <div className="min-h-screen bg-brand-50 flex flex-col font-sans">
      {/* Header & Language Switcher */}
      <header className="w-full p-4 flex justify-between items-center bg-white shadow-sm sticky top-0 z-50">
        <div className="text-2xl font-bold text-brand-600">Lodge-Link</div>
        <div className="flex items-center space-x-4">
          <Link href="/auth/signin" className="text-sm font-medium text-gray-600 hover:text-brand-600 transition-colors">
            {t('nav_signin')}
          </Link>
          <button
            onClick={toggleLanguage}
            className="px-4 py-2 text-sm font-medium border border-brand-500 text-brand-600 rounded-md hover:bg-brand-50 transition-colors"
          >
            {i18n.language === 'en' ? 'አማርኛ' : 'English'}
          </button>
        </div>
      </header>

      <main className="flex-grow">
        {/* Hero Section */}
        <section className="px-6 py-16 md:py-24 max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-brand-900 leading-tight mb-6">
            {t('hero_headline')}
          </h1>
          <p className="text-lg md:text-xl text-gray-700 mb-10 max-w-2xl mx-auto">
            {t('hero_subheadline')}
          </p>
          <Link href="/auth/signup" className="inline-block w-full sm:w-auto px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white text-lg font-bold rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1">
            {t('cta_button')}
          </Link>
          
          <div className="mt-8 flex items-center justify-center space-x-2 text-sm font-medium text-gray-500 bg-white inline-flex px-4 py-2 rounded-full shadow-sm">
            <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>{t('trust_bar')}</span>
          </div>
        </section>

        {/* Social Proof / Live Counter */}
        <section className="bg-brand-600 text-white py-4 text-center text-sm md:text-base font-semibold">
          {t('live_counter')}
        </section>

        {/* How It Works Section */}
        <section className="py-16 px-6 bg-white">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-brand-900 mb-12">{t('how_it_works_title')}</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[1, 2, 3].map((step) => (
                <div key={step} className="bg-brand-50 rounded-xl p-8 text-center shadow-sm hover:shadow-md transition-shadow border border-brand-100">
                  <div className="w-16 h-16 bg-brand-500 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6 shadow-md">
                    {step}
                  </div>
                  <h3 className="text-xl font-bold text-brand-900 mb-4">{t(`step_${step}_title`)}</h3>
                  <p className="text-gray-600 leading-relaxed">{t(`step_${step}_desc`)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Feature Comparison */}
        <section className="py-16 px-6 bg-gray-50">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-brand-900 mb-12">{t('comparison_title')}</h2>
            
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
              <div className="grid grid-cols-2 bg-gray-100 p-4 font-bold text-center">
                <div className="text-red-600">{t('before_title')}</div>
                <div className="text-green-600">{t('after_title')}</div>
              </div>
              
              {[1, 2, 3, 4].map((item) => (
                <div key={item} className="grid grid-cols-2 border-b border-gray-100 last:border-b-0">
                  <div className="p-4 md:p-6 text-center text-gray-500 flex items-center justify-center border-r border-gray-100">
                    <span className="mr-2 text-red-500">❌</span> {t(`before_${item}`)}
                  </div>
                  <div className="p-4 md:p-6 text-center text-brand-900 font-medium flex items-center justify-center bg-brand-50/30">
                    <span className="mr-2 text-green-500">✅</span> {t(`after_${item}`)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-20 px-6 text-center max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-brand-900 mb-8">{t('hero_headline')}</h2>
          <Link href="/auth/signup" className="inline-block w-full sm:w-auto px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white text-lg font-bold rounded-lg shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-1">
            {t('cta_button')}
          </Link>
        </section>
      </main>

      <footer className="bg-white border-t border-gray-200 py-8 text-center text-gray-500 text-sm">
        {t('footer_text')}
      </footer>
    </div>
  );
}
