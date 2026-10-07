'use client';

import React, { useState, useEffect } from 'react';
import { DocumentItem, TopicMastery, StudentProgress } from '@/lib/types';
import { learnovaApi } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { PillButton } from '@/components/ui/PillButton';
import {
  Activity,
  BrainCircuit,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Layers,
  Sparkles
} from 'lucide-react';

interface MasteryTabProps {
  document: DocumentItem;
  onLaunchTutorForTopic: (topicName: string) => void;
}

export const MasteryTab: React.FC<MasteryTabProps> = ({
  document,
  onLaunchTutorForTopic
}) => {
  const [topics, setTopics] = useState<TopicMastery[]>([]);
  const [progress, setProgress] = useState<StudentProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMastery = async () => {
      try {
        setLoading(true);
        const [mastRes, progRes] = await Promise.all([
          learnovaApi.getTopicMastery(document.id),
          learnovaApi.getStudentProgress()
        ]);
        setTopics(mastRes);
        setProgress(progRes);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMastery();
  }, [document.id]);

  const avgMastery =
    topics.length > 0
      ? Math.round((topics.reduce((acc, t) => acc + t.mastery_score, 0) / topics.length) * 100)
      : 76;

  const weakTopics = topics.filter((t) => t.mastery_score < 0.6);

  return (
    <div className="space-y-10">
      {/* Overview Analytics Rail */}
      <div className="border border-[#cecece] p-6 md:p-8 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                LEARNING PROGRESS // HOW WELL YOU REMEMBER
              </span>
            </div>
            <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
              MASTERY GAUGES & SPACED INTERVALS
            </h2>
          </div>

          <Badge variant="dark" size="md">
            DOCUMENT MASTERY: {avgMastery}%
          </Badge>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-2">
          <div>
            <span className="text-[11px] font-tech text-[#6d6d6d] uppercase block">
              HOW WELL YOU REMEMBER
            </span>
            <span className="text-[36px] font-bold font-tech text-[#0c0c0c] leading-none">
              {avgMastery}%
            </span>
            <span className="text-[11px] text-[#6d6d6d] block mt-1">
              Memory Strength Calibrated
            </span>
          </div>

          <div>
            <span className="text-[11px] font-tech text-[#6d6d6d] uppercase block">
              TRACKED CONCEPTS
            </span>
            <span className="text-[36px] font-bold font-tech text-[#0c0c0c] leading-none">
              {topics.length || 5}
            </span>
            <span className="text-[11px] text-[#6d6d6d] block mt-1">
              Independent Knowledge Nodes
            </span>
          </div>

          <div>
            <span className="text-[11px] font-tech text-[#6d6d6d] uppercase block">
              SPACED REVIEWS DUE
            </span>
            <span className="text-[36px] font-bold font-tech text-[#c5221f] leading-none">
              {weakTopics.length}
            </span>
            <span className="text-[11px] text-[#6d6d6d] block mt-1">
              Requires Formative Practice
            </span>
          </div>

          <div>
            <span className="text-[11px] font-tech text-[#6d6d6d] uppercase block">
              STUDY STREAK
            </span>
            <span className="text-[36px] font-bold font-tech text-[#0c0c0c] leading-none">
              {progress?.current_streak_days || 7}d
            </span>
            <span className="text-[11px] text-[#6d6d6d] block mt-1">
              Active Daily Discipline
            </span>
          </div>
        </div>
      </div>

      {/* Weak Concept Immediate Interventions */}
      {weakTopics.length > 0 && (
        <div className="border border-[#c5221f] p-6 md:p-8 bg-[#ffffff]">
          <div className="flex items-center gap-2 mb-2 text-[#c5221f]">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="text-[16px] font-bold font-tech uppercase tracking-wide">
              CONCEPTS NEEDING REVIEW // BOOST YOUR RETENTION
            </h3>
          </div>
          <p className="text-[13px] text-[#6d6d6d] mb-6">
            The following concepts are due for review.
            Practicing with the AI Tutor now will help lock them into your long-term memory.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {weakTopics.map((wt) => (
              <div
                key={wt.topic_id}
                className="border border-[#cecece] p-4 bg-[#fafafa] flex items-center justify-between"
              >
                <div>
                  <span className="text-[14px] font-bold font-tech text-[#0c0c0c] block">
                    {wt.topic_name}
                  </span>
                  <span className="text-[12px] font-mono text-[#c5221f]">
                    Current Mastery: {Math.round(wt.mastery_score * 100)}%
                  </span>
                </div>
                <PillButton
                  variant="primary"
                  size="sm"
                  onClick={() => onLaunchTutorForTopic(wt.topic_name)}
                  icon={<BrainCircuit className="w-3.5 h-3.5" />}
                >
                  TUTOR ME
                </PillButton>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Granular Concept Mastery Table */}
      <div className="border border-[#cecece] p-6 md:p-8 bg-[#ffffff] space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#cecece]">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              TOPIC BREAKDOWN // COGNITIVE TRACE
            </span>
            <h3 className="text-[20px] font-bold font-tech text-[#0c0c0c] uppercase mt-0.5">
              CONCEPT PROGRESSION & SPACED REPETITION SCHEDULE
            </h3>
          </div>
          <span className="text-[12px] font-tech text-[#6d6d6d]">
            UPDATED AFTER EVERY FORMATION INTERACTION
          </span>
        </div>

        <div className="divide-y divide-[#cecece] border border-[#cecece]">
          {topics.map((t, idx) => {
            const masteryPercent = Math.round(t.mastery_score * 100);
            return (
              <div
                key={t.topic_id || idx}
                className="p-6 bg-[#ffffff] hover:bg-[#fafafa] transition-colors flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="space-y-2 flex-1 max-w-xl">
                  <div className="flex items-center gap-3">
                    <span className="text-[12px] font-mono text-[#6d6d6d]">
                      0{idx + 1}.
                    </span>
                    <h4 className="text-[16px] font-bold font-tech text-[#0c0c0c]">
                      {t.topic_name}
                    </h4>
                    <Badge
                      variant={
                        t.status === 'MASTERED'
                          ? 'dark'
                          : t.status === 'PRACTICING'
                          ? 'default'
                          : 'alert'
                      }
                      size="sm"
                    >
                      {t.status}
                    </Badge>
                  </div>

                  <div className="w-full bg-[#eaeaea] h-2">
                    <div
                      className={`h-full transition-all duration-500 ${
                        masteryPercent >= 80
                          ? 'bg-[#0c0c0c]'
                          : masteryPercent >= 60
                          ? 'bg-[#6d6d6d]'
                          : 'bg-[#c5221f]'
                      }`}
                      style={{ width: `${masteryPercent}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-8 self-end md:self-center">
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-tech text-[#6d6d6d] block">
                      SCORE
                    </span>
                    <span className="text-[18px] font-bold font-tech text-[#0c0c0c]">
                      {masteryPercent}%
                    </span>
                  </div>

                  <div className="text-right border-x border-[#cecece] px-6">
                    <span className="text-[10px] uppercase font-tech text-[#6d6d6d] block">
                      INTERVAL
                    </span>
                    <span className="text-[14px] font-bold font-mono text-[#0c0c0c]">
                      +{t.spaced_repetition_interval_days || 1}d
                    </span>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] uppercase font-tech text-[#6d6d6d] block">
                      NEXT DUE
                    </span>
                    <span className="text-[14px] font-mono text-[#0c0c0c]">
                      {t.next_review_at ? new Date(t.next_review_at).toLocaleDateString() : 'Today'}
                    </span>
                  </div>

                  <PillButton
                    variant="outline"
                    size="sm"
                    onClick={() => onLaunchTutorForTopic(t.topic_name)}
                  >
                    PRACTICE
                  </PillButton>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
