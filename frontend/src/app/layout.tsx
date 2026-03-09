import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Sidebar from '@/components/Sidebar';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Faceless Video Creator',
  description: 'Create viral faceless videos - Reddit stories, AI-generated, auto-clipped, and UGC content',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#0a0a0a] text-white`}>
        <Sidebar />
        <main className="ml-64 min-h-screen p-8">{children}</main>
      </body>
    </html>
  );
}
