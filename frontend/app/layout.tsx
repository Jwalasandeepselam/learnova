import type { Metadata } from 'next';
import { Space_Grotesk, Inter } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/layout/Navbar';
import { VoiceAssistantProvider } from '@/lib/voiceContext';
import { FloatingVoiceButton } from '@/components/voice/FloatingVoiceButton';
import { VoiceAssistantModal } from '@/components/voice/VoiceAssistantModal';

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
  weight: ['400', '500', '600', '700'],
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  weight: ['400', '500', '600', '700'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Learnova — Understand, Don\'t Just Read',
  description:
    'Learnova doesn\'t summarize your material — it decomposes textbooks, slides, and notes into dynamic knowledge models, teaching you line-by-line.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <VoiceAssistantProvider>
          <Navbar />
          <main className="flex-1 w-full">{children}</main>
          <FloatingVoiceButton />
          <VoiceAssistantModal />
        </VoiceAssistantProvider>
      </body>
    </html>
  );
}
