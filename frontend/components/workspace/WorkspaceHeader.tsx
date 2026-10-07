'use client';

import React from 'react';
import Link from 'next/link';
import { DocumentItem } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { PillButton } from '@/components/ui/PillButton';
import { ArrowLeft, BookOpen, BrainCircuit, MessageSquareQuote, CheckSquare, FileSpreadsheet, Activity } from 'lucide-react';

export type WorkspaceTab = 'overview' | 'tutor' | 'ask' | 'quiz' | 'packs' | 'mastery';

interface WorkspaceHeaderProps {
  document: DocumentItem;
  activeTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
}

export const WorkspaceHeader: React.FC<WorkspaceHeaderProps> = ({
  document,
  activeTab,
  onTabChange
}) => {
  const tabs = [
    { id: 'overview' as WorkspaceTab, label: '01 // OVERVIEW & TOPICS', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { id: 'tutor' as WorkspaceTab, label: '02 // AI TUTOR', icon: <BrainCircuit className="w-3.5 h-3.5" /> },
    { id: 'ask' as WorkspaceTab, label: '03 // ASK AI (YOUR MATERIAL)', icon: <MessageSquareQuote className="w-3.5 h-3.5" /> },
    { id: 'quiz' as WorkspaceTab, label: '04 // QUIZ ARENA', icon: <CheckSquare className="w-3.5 h-3.5" /> },
    { id: 'packs' as WorkspaceTab, label: '05 // STUDY PACKS & PDF', icon: <FileSpreadsheet className="w-3.5 h-3.5" /> },
    { id: 'mastery' as WorkspaceTab, label: '06 // YOUR PROGRESS', icon: <Activity className="w-3.5 h-3.5" /> }
  ];

  return (
    <div className="w-full bg-[#ffffff] border-b border-[#cecece]">
      {/* Top Bar Navigation */}
      <div className="max-w-7xl mx-auto px-6 md:px-10 py-6 border-b border-[#cecece]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 border border-[#cecece] hover:border-[#0c0c0c] hover:bg-[#fafafa] transition-colors"
            >
              <ArrowLeft className="w-4 h-4 text-[#0c0c0c]" />
            </Link>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                  DOSSIER REF // {document.id.toUpperCase()}
                </span>
                <Badge variant="dark" size="sm">
                  {document.filename.split('.').pop()?.toUpperCase()}
                </Badge>
                <Badge variant={document.status === 'READY' ? 'success' : 'default'} size="sm">
                  {document.status}
                </Badge>
              </div>

              <h1 className="text-[24px] md:text-[28px] font-bold text-[#0c0c0c] font-tech leading-tight mt-1">
                {document.title}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4 text-[12px] font-tech text-[#6d6d6d]">
            <div className="px-3 py-1.5 border border-[#cecece] bg-[#fafafa]">
              PAGES: <strong className="text-[#0c0c0c]">{document.total_pages}</strong>
            </div>
            <div className="px-3 py-1.5 border border-[#cecece] bg-[#fafafa]">
              CHUNKS: <strong className="text-[#0c0c0c]">{document.total_chunks}</strong>
            </div>
            <div className="px-3 py-1.5 border border-[#cecece] bg-[#fafafa]">
              WORDS: <strong className="text-[#0c0c0c]">{document.word_count || '28.4k'}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Workspace Subnav Tabs */}
      <div className="max-w-7xl mx-auto px-6 md:px-10 overflow-x-auto">
        <nav className="flex space-x-2 md:space-x-8 min-w-max py-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-2 py-3 px-1 border-b-2 font-tech text-[13px] tracking-wider uppercase transition-all ${
                  isActive
                    ? 'border-[#0c0c0c] text-[#0c0c0c] font-bold'
                    : 'border-transparent text-[#6d6d6d] hover:text-[#0c0c0c] hover:border-[#cecece]'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
