/** @type {import('next').NextConfig} */
const nextConfig = {
  // PWA support will be added via next-pwa in Phase 1
  reactStrictMode: true,
  i18n: {
    locales: ['en', 'am'],   // English + Amharic
    defaultLocale: 'en',
  },
}

module.exports = nextConfig
