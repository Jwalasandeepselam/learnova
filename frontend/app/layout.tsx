import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Learnova — Make knowledge yours', description: 'A personal learning space for your documents. Explore, ask, practice, and understand.' };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><a className="skip-link" href="#main">Skip to content</a>{children}</body></html>;
}
