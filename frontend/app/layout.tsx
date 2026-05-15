import './globals.css';
import I18nProvider from '../components/I18nProvider';

export const metadata = {
  title: "Lodge-Link | You're Full Tonight. Your Guest Doesn't Have to Leave.",
  description: 'Lodge-Link connects Addis Ababa hotels into a real-time referral network.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0" />
      </head>
      <body className="antialiased selection:bg-[#00d4aa]/30 selection:text-[#00d4aa]">
        <I18nProvider>
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
