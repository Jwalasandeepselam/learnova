'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { DocumentItem } from '@/lib/types';
import { learnovaApi } from '@/lib/api';
import { WorkspaceHeader, WorkspaceTab } from '@/components/workspace/WorkspaceHeader';
import { OverviewTab } from '@/components/workspace/OverviewTab';
import { SocraticTutorTab } from '@/components/workspace/SocraticTutorTab';
import { AskAiTab } from '@/components/workspace/AskAiTab';
import { QuizArenaTab } from '@/components/workspace/QuizArenaTab';
import { StudyPacksTab } from '@/components/workspace/StudyPacksTab';
import { MasteryTab } from '@/components/workspace/MasteryTab';
import { Loader2 } from 'lucide-react';

function DocumentWorkspaceInner() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const documentId = (params?.id as string) || 'doc_quantum_01';
  const initialTab = (searchParams.get('tab') as WorkspaceTab) || 'overview';
  const initialTopic = searchParams.get('topic') || undefined;

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>(initialTab);
  const [selectedTopic, setSelectedTopic] = useState<string | undefined>(initialTopic);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        setLoading(true);
        const doc = await learnovaApi.getDocument(documentId);
        setDocument(doc);
      } catch (err) {
        console.error('Failed to fetch document:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [documentId]);

  useEffect(() => {
    const tabParam = searchParams.get('tab') as WorkspaceTab;
    if (tabParam && ['overview', 'tutor', 'ask', 'quiz', 'packs', 'mastery'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
    const topicParam = searchParams.get('topic');
    if (topicParam) {
      setSelectedTopic(topicParam);
    }
  }, [searchParams]);

  const handleTabChange = (tab: WorkspaceTab) => {
    setActiveTab(tab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    window.history.pushState({}, '', url.toString());
  };

  const handleLaunchTutorForTopic = (topicName: string) => {
    setSelectedTopic(topicName);
    setActiveTab('tutor');
    const url = new URL(window.location.href);
    url.searchParams.set('tab', 'tutor');
    url.searchParams.set('topic', topicName);
    window.history.pushState({}, '', url.toString());
  };

  if (loading) {
    return (
      <div className="w-full min-h-[60vh] flex flex-col items-center justify-center space-y-4 pt-[98px]">
        <Loader2 className="w-8 h-8 animate-spin text-[#0c0c0c]" />
        <span className="text-[13px] font-tech text-[#6d6d6d] uppercase tracking-wider">
          LOADING YOUR STUDY MATERIAL...
        </span>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="w-full min-h-[80vh] flex flex-col items-center justify-center p-6 md:p-10 pt-[120px] text-center bg-[#ffffff]">
        <div className="max-w-md border border-[#0c0c0c] p-8 md:p-10 bg-[#ffffff] space-y-6 shadow-sm">
          <div className="w-14 h-14 rounded-full border border-[#0c0c0c] mx-auto flex items-center justify-center text-xl font-tech">
            ?
          </div>
          <div className="space-y-2">
            <h2 className="font-tech text-[20px] uppercase font-bold text-[#0c0c0c]">
              DOCUMENT NOT FOUND
            </h2>
            <p className="font-sans text-[14px] text-[#6d6d6d] leading-relaxed">
              This document could not be located. Please upload your study material to begin your AI tutoring session.
            </p>
          </div>
          <div className="pt-2 flex flex-col gap-3 items-center">
            <Link href="/#hero" className="w-full">
              <button className="black-btn" style={{ width: '100%' }}>
                UPLOAD STUDY MATERIAL
              </button>
            </Link>
            <Link href="/" className="text-btn" style={{ marginTop: '6px' }}>
              RETURN TO HOME
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen bg-[#ffffff] pt-[98px]">
      {/* Workspace Header & Mode Tabs */}
      <WorkspaceHeader
        document={document}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      {/* Main Mode View Container */}
      <main className="max-w-7xl mx-auto px-6 md:px-10 py-10">
        {activeTab === 'overview' && (
          <OverviewTab
            document={document}
            onSelectTopicForTutor={handleLaunchTutorForTopic}
          />
        )}

        {activeTab === 'tutor' && (
          <SocraticTutorTab
            document={document}
            initialTopic={selectedTopic}
          />
        )}

        {activeTab === 'ask' && (
          <AskAiTab
            document={document}
          />
        )}

        {activeTab === 'quiz' && (
          <QuizArenaTab
            document={document}
          />
        )}

        {activeTab === 'packs' && (
          <StudyPacksTab
            document={document}
          />
        )}

        {activeTab === 'mastery' && (
          <MasteryTab
            document={document}
            onLaunchTutorForTopic={handleLaunchTutorForTopic}
          />
        )}
      </main>
    </div>
  );
}

export default function DocumentWorkspacePage() {
  return (
    <Suspense
      fallback={
        <div className="w-full min-h-[60vh] flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-[#0c0c0c]" />
          <span className="text-[13px] font-tech text-[#6d6d6d] uppercase tracking-wider">
            LOADING DOSSIER...
          </span>
        </div>
      }
    >
      <DocumentWorkspaceInner />
    </Suspense>
  );
}
