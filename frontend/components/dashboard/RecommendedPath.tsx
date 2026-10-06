'use client';

import React from 'react';
import Link from 'next/link';
import { TopicMastery } from '@/lib/types';
import { PillButton } from '@/components/ui/PillButton';
import { Badge } from '@/components/ui/Badge';
import { AlertTriangle, Clock, ArrowRight, BrainCircuit } from 'lucide-react';

interface RecommendedPathProps {
  weakTopics: TopicMastery[];
}

export const RecommendedPath: React.FC<RecommendedPathProps> = ({ weakTopics }) => {
  return (
    <div className="border border-[#cecece] bg-[#ffffff] p-8 md:p-10">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              BAYESIAN KNOWLEDGE TRACING // ACTIVE INTERVENTIONS
            </span>
          </div>
          <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
            TARGETED REMEDIATION & SPACED REPETITION
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="alert" size="sm">
            {weakTopics.length} INTERVENTIONS QUEUED
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {weakTopics.map((topic, idx) => {
          const masteryPercent = Math.round(topic.mastery_score * 100);

          return (
            <div
              key={topic.topic_id || idx}
              className="border border-[#cecece] p-6 flex flex-col justify-between hover:border-[#0c0c0c] transition-all bg-[#fafafa]"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-mono uppercase text-[#6d6d6d]">
                    DEFICIT ITEM // 0{idx + 1}
                  </span>
                  <Badge
                    variant={masteryPercent < 50 ? 'alert' : 'warning'}
                    size="sm"
                  >
                    {masteryPercent}% MASTERY
                  </Badge>
                </div>

                <h4 className="text-[16px] font-bold text-[#0c0c0c] font-tech mb-2">
                  {topic.topic_name}
                </h4>

                <div className="w-full bg-[#eaeaea] h-1.5 my-3">
                  <div
                    className={`h-full ${
                      masteryPercent < 50 ? 'bg-[#c5221f]' : 'bg-[#b06000]'
                    }`}
                    style={{ width: `${masteryPercent}%` }}
                  />
                </div>

                <div className="flex items-center gap-2 text-[12px] text-[#6d6d6d] my-3">
                  <Clock className="w-3.5 h-3.5" />
                  <span>
                    Spaced repetition due:{' '}
                    <strong className="text-[#0c0c0c] font-mono">
                      {topic.next_review_at ? new Date(topic.next_review_at).toLocaleDateString() : 'Today'}
                    </strong>
                  </span>
                </div>

                <p className="text-[12px] text-[#6d6d6d] leading-relaxed">
                  Pedagogical recommendation: Review first principles and complete diagnostic
                  misconception checks to reinforce memory trace.
                </p>
              </div>

              <div className="pt-6 border-t border-[#cecece] mt-6 flex items-center justify-between">
                <Link
                  href={`/documents/${topic.document_id}?tab=tutor&topic=${encodeURIComponent(
                    topic.topic_name
                  )}`}
                  className="w-full"
                >
                  <PillButton
                    variant="outline"
                    size="sm"
                    className="w-full"
                    icon={<BrainCircuit className="w-3.5 h-3.5" />}
                  >
                    SOCRATIC REMEDIATION
                  </PillButton>
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
