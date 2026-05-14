import './globals.css';
import I18nProvider from '../components/I18nProvider';
import OfflineBanner from '../components/OfflineBanner';

export const metadata = {
  title: 'Lodge-Link | Trusted Referral Network',
  description: 'Connect your hotel to a trusted network. Never let a guest leave empty-handed.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <OfflineBanner />
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
