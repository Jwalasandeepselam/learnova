'use client';

import React, { useState, useEffect, Suspense } from 'react';
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

  if (loading || !document) {
    return (
      <div className="w-full min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-[#0c0c0c]" />
        <span className="text-[13px] font-tech text-[#6d6d6d] uppercase tracking-wider">
          INITIALIZING LEARNING WORKSPACE DOSSIER...
        </span>
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
