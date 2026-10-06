'use client';

import React from 'react';
import { DocumentItem, Topic } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { PillButton } from '@/components/ui/PillButton';
import { BrainCircuit, BookMarked, Sparkles, CheckCircle2 } from 'lucide-react';

interface OverviewTabProps {
  document: DocumentItem;
  onSelectTopicForTutor: (topicName: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  document,
  onSelectTopicForTutor
}) => {
  const topics: Topic[] = document.topics || [
    {
      id: 'top_01',
      name: 'Wave-Particle Duality & de Broglie Hypothesis',
      difficulty_level: 'INTERMEDIATE',
      chunk_count: 24,
      mastery_score: 0.88,
      description: 'Foundational framework linking wavelength λ to momentum p via Planck constant.'
    },
    {
      id: 'top_02',
      name: 'Born Statistical Interpretation of Wavefunctions',
      difficulty_level: 'INTERMEDIATE',
      chunk_count: 32,
      mastery_score: 0.74,
      description: 'Probability density representation |ψ|² and the normalization condition.'
    },
    {
      id: 'top_03',
      name: 'Time-Dependent Schrödinger Dynamics',
      difficulty_level: 'ADVANCED',
      chunk_count: 48,
      mastery_score: 0.52,
      description: 'Differential wave equation iℏ ∂ψ/∂t = Ĥψ governing non-relativistic state vectors.'
    },
    {
      id: 'top_04',
      name: 'Heisenberg Uncertainty Principle',
      difficulty_level: 'INTERMEDIATE',
      chunk_count: 20,
      mastery_score: 0.92,
      description: 'Invariance bounds Δx·Δp ≥ ℏ/2 stemming from operator non-commutativity.'
    }
  ];

  const extractedFormulas = [
    {
      name: 'de Broglie Relation',
      latex: 'λ = h / p = 2πℏ / p',
      significance: 'Unifies particle linear momentum with matter wave spatial periodicity.'
    },
    {
      name: 'Time-Dependent Schrödinger Equation',
      latex: 'iℏ ∂ψ/∂t = - (ℏ² / 2m) ∇²ψ + V(x)ψ',
      significance: 'Governs unitary state evolution in coordinate space.'
    },
    {
      name: 'Continuity & Probability Current',
      latex: 'J(x, t) = (ℏ / 2mi) [ψ* ∇ψ - ψ ∇ψ*]',
      significance: 'Conserves total probability via ∂ρ/∂t + ∇·J = 0.'
    },
    {
      name: 'Uncertainty Lower Bound',
      latex: 'σ_x σ_p ≥ ℏ / 2',
      significance: 'Fundamental Cauchy-Schwarz constraint for non-commuting observables.'
    }
  ];

  return (
    <div className="space-y-10">
      {/* Executive Summary Card */}
      <div className="border border-[#cecece] p-8 md:p-10 bg-[#ffffff]">
        <div className="flex items-center justify-between pb-4 border-b border-[#cecece] mb-6">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              STUDY ANALYZER // SYNTHESIS
            </span>
          </div>
          <Badge variant="dark" size="sm">
            DOCUMENT DIGEST
          </Badge>
        </div>

        <h3 className="text-[20px] font-bold text-[#0c0c0c] font-tech uppercase mb-3">
          EXECUTIVE CONCEPTUAL OVERVIEW
        </h3>

        <p className="text-[16px] text-[#0c0c0c] leading-relaxed font-sans max-w-4xl">
          {document.summary ||
            'This ingested curriculum resource covers foundational quantum dynamics, establishing the probabilistic interpretation of wavefunctions, Hamiltonian operator formalisms, boundary conditions in infinite potential wells, and Fourier conjugate limits.'}
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-[#cecece]">
          <div>
            <span className="text-[11px] font-tech uppercase text-[#6d6d6d]">SOURCE FORMAT</span>
            <p className="text-[15px] font-bold font-tech text-[#0c0c0c]">
              {document.filename.split('.').pop()?.toUpperCase()} (ENCODED)
            </p>
          </div>
          <div>
            <span className="text-[11px] font-tech uppercase text-[#6d6d6d]">KNOWLEDGE DENSITY</span>
            <p className="text-[15px] font-bold font-tech text-[#0c0c0c]">
              {Math.round((document.total_chunks || 142) / (document.total_pages || 38))} CHUNKS/PAGE
            </p>
          </div>
          <div>
            <span className="text-[11px] font-tech uppercase text-[#6d6d6d]">IDENTIFIED CONCEPTS</span>
            <p className="text-[15px] font-bold font-tech text-[#0c0c0c]">
              {topics.length} CORE DOMAINS
            </p>
          </div>
          <div>
            <span className="text-[11px] font-tech uppercase text-[#6d6d6d]">CURRICULUM LEVEL</span>
            <p className="text-[15px] font-bold font-tech text-[#0c0c0c]">
              ADVANCED UNDERGRAD
            </p>
          </div>
        </div>
      </div>

      {/* Extracted Topics & Concept Hierarchy */}
      <div className="border border-[#cecece] p-8 md:p-10 bg-[#ffffff]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#cecece] mb-6 gap-2">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              KNOWLEDGE GRAPH // DECOMPOSED TOPICS
            </span>
            <h3 className="text-[20px] font-bold text-[#0c0c0c] font-tech uppercase mt-0.5">
              CONCEPT HIERARCHY & REASONING PATH
            </h3>
          </div>
          <span className="text-[12px] font-tech text-[#6d6d6d] uppercase">
            CLICK ANY CONCEPT TO ENGAGE SOCRATIC TUTOR
          </span>
        </div>

        <div className="divide-y divide-[#cecece]">
          {topics.map((topic, idx) => (
            <div
              key={topic.id || idx}
              className="py-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-[#fafafa] px-4 -mx-4 transition-colors"
            >
              <div className="space-y-1 max-w-2xl">
                <div className="flex items-center gap-3">
                  <span className="text-[12px] font-mono text-[#6d6d6d]">
                    0{idx + 1}.
                  </span>
                  <h4 className="text-[16px] font-bold text-[#0c0c0c] font-tech">
                    {topic.name}
                  </h4>
                  <Badge
                    variant={
                      topic.difficulty_level === 'ADVANCED'
                        ? 'dark'
                        : topic.difficulty_level === 'INTERMEDIATE'
                        ? 'default'
                        : 'outline'
                    }
                    size="sm"
                  >
                    {topic.difficulty_level}
                  </Badge>
                </div>
                {topic.description && (
                  <p className="text-[13px] text-[#6d6d6d] pl-7">
                    {topic.description}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-6 self-end md:self-center">
                <div className="text-right">
                  <span className="text-[11px] font-tech text-[#6d6d6d] block uppercase">
                    EST. MASTERY
                  </span>
                  <span className="text-[15px] font-bold font-tech text-[#0c0c0c]">
                    {Math.round((topic.mastery_score || 0.6) * 100)}%
                  </span>
                </div>

                <PillButton
                  variant="secondary"
                  size="sm"
                  icon={<BrainCircuit className="w-3.5 h-3.5" />}
                  onClick={() => onSelectTopicForTutor(topic.name)}
                >
                  TEACH ME
                </PillButton>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Extracted Mathematical Foundations */}
      <div className="border border-[#cecece] p-8 md:p-10 bg-[#ffffff]">
        <div className="flex items-center justify-between pb-4 border-b border-[#cecece] mb-6">
          <div>
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              AXIOMATIC EQUATIONS // SYSTEM SPEC
            </span>
            <h3 className="text-[20px] font-bold text-[#0c0c0c] font-tech uppercase mt-0.5">
              EXTRACTED GOVERNING FORMULAS
            </h3>
          </div>
          <Badge variant="outline" size="sm">
            LATEX READY
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {extractedFormulas.map((form, idx) => (
            <div
              key={idx}
              className="border border-[#cecece] p-6 bg-[#fafafa] flex flex-col justify-between"
            >
              <div>
                <span className="text-[10px] font-mono text-[#6d6d6d] uppercase block mb-1">
                  EQUATION // 0{idx + 1}
                </span>
                <h4 className="text-[15px] font-bold text-[#0c0c0c] font-tech mb-3">
                  {form.name}
                </h4>
                <div className="bg-[#ffffff] border border-[#cecece] p-3 text-center my-2 font-mono text-[14px] text-[#0c0c0c] overflow-x-auto">
                  {form.latex}
                </div>
              </div>
              <p className="text-[12px] text-[#6d6d6d] mt-3 pt-3 border-t border-[#cecece]">
                {form.significance}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
