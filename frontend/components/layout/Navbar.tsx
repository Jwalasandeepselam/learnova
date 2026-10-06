'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const isHome = pathname === '/';

  return (
    <header className="header">
      <Link href="/" className="logo">
        <div className="logo-mark" />
        <span>Learnova</span>
      </Link>

      <nav className="nav">
        <a href={isHome ? '#analysis' : '/#analysis'}>ANALYZE</a>
        <a href={isHome ? '#learn' : '/#learn'}>LEARN</a>
        <a href={isHome ? '#study-pack' : '/#study-pack'}>STUDY PACK</a>
        <a href={isHome ? '#method' : '/#method'}>METHOD</a>
      </nav>

      <div className="header-right">
        <span className="status">
          <i className="dot" /> AI TUTOR ONLINE
        </span>
        <span>V1.0</span>
      </div>
    </header>
  );
};
