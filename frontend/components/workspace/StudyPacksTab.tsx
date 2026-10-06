'use client';

import React, { useState } from 'react';
import { DocumentItem, StudyPack } from '@/lib/types';
import { learnovaApi } from '@/lib/api';
import { MOCK_STUDY_PACKS } from '@/lib/mockData';
import { PillButton } from '@/components/ui/PillButton';
import { Badge } from '@/components/ui/Badge';
import {
  FileSpreadsheet,
  Download,
  Sparkles,
  BookOpen,
  CheckCircle2,
  FileText,
  RotateCw,
  Loader2,
  Layers,
  Printer
} from 'lucide-react';

interface StudyPacksTabProps {
  document: DocumentItem;
}

export const StudyPacksTab: React.FC<StudyPacksTabProps> = ({ document }) => {
  const [packType, setPackType] = useState<
    'complete' | 'quick_revision' | 'formula_sheet' | 'exam_prep'
  >('complete');
  const [includeFlashcards, setIncludeFlashcards] = useState(true);
  const [includeCheatSheet, setIncludeCheatSheet] = useState(true);
  const [includePracticeExam, setIncludePracticeExam] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [studyPack, setStudyPack] = useState<StudyPack>(
    MOCK_STUDY_PACKS[document.id] || MOCK_STUDY_PACKS.doc_quantum_01
  );
  const [flippedCards, setFlippedCards] = useState<Record<string, boolean>>({});

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const generated = await learnovaApi.generateStudyPack({
        document_id: document.id,
        title: `${document.title} — ${
          packType === 'complete'
            ? 'Complete Study Dossier'
            : packType === 'quick_revision'
            ? 'Quick Revision Brief'
            : packType === 'formula_sheet'
            ? 'Formula Reference Sheet'
            : 'Exam Preparation Pack'
        }`,
        pack_type: packType,
        include_flashcards: includeFlashcards,
        include_cheat_sheet: includeCheatSheet,
        include_practice_exam: includePracticeExam
      });

      setStudyPack(generated);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPdf = () => {
    const downloadUrl = learnovaApi.getStudyPackPdfDownloadUrl(studyPack.id);
    // Trigger download via anchor
    const link = window.document.createElement('a');
    link.href = downloadUrl;
    link.target = '_blank';
    link.download = `Learnova_StudyPack_${studyPack.id}.pdf`;
    window.document.body.appendChild(link);
    link.click();
    window.document.body.removeChild(link);
  };

  const toggleFlip = (id: string) => {
    setFlippedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-10">
      {/* Pack Generation Controls */}
      <div className="border border-[#cecece] p-6 md:p-8 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                STUDY PACK SYNTHESIS // REPORTLAB COMPATIBLE
              </span>
            </div>
            <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
              CURRICULUM DOSSIER & PDF EXPORTER
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <PillButton
              variant="primary"
              size="sm"
              onClick={handleGenerate}
              disabled={generating}
              icon={generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            >
              {generating ? 'SYNTHESIZING DOSSIER...' : 'GENERATE STUDY PACK'}
            </PillButton>
          </div>
        </div>

        {/* Pack Type Selectors */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            {
              id: 'complete',
              title: 'COMPLETE DOSSIER',
              desc: 'Executive summary, full formula sheet, flashcards, and exam problems.'
            },
            {
              id: 'quick_revision',
              title: 'QUICK REVISION',
              desc: 'High-density bullet points and essential definitions for 15-minute review.'
            },
            {
              id: 'formula_sheet',
              title: 'FORMULA SHEET',
              desc: 'Governing equations, symbols, units, and physical interpretations.'
            },
            {
              id: 'exam_prep',
              title: 'EXAM PREPARATION',
              desc: 'Targeted practice problems, model derivations, and misconception traps.'
            }
          ].map((type) => (
            <button
              key={type.id}
              onClick={() => setPackType(type.id as any)}
              className={`p-4 border text-left transition-all ${
                packType === type.id
                  ? 'border-[#0c0c0c] bg-[#fafafa]'
                  : 'border-[#cecece] bg-[#ffffff] hover:border-[#6d6d6d]'
              }`}
            >
              <span className="text-[10px] font-mono uppercase text-[#6d6d6d] block mb-1">
                TYPE // {type.id.toUpperCase()}
              </span>
              <h4 className="text-[14px] font-bold font-tech text-[#0c0c0c] mb-1">
                {type.title}
              </h4>
              <p className="text-[12px] text-[#6d6d6d] leading-relaxed">
                {type.desc}
              </p>
            </button>
          ))}
        </div>

        {/* Checkbox Options */}
        <div className="flex flex-wrap items-center gap-6 pt-4 border-t border-[#cecece] text-[13px] font-tech text-[#0c0c0c]">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includeFlashcards}
              onChange={(e) => setIncludeFlashcards(e.target.checked)}
              className="accent-[#0c0c0c] w-4 h-4 rounded-none"
            />
            <span>INCLUDE FLASHCARD RETRIEVAL DECK</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includeCheatSheet}
              onChange={(e) => setIncludeCheatSheet(e.target.checked)}
              className="accent-[#0c0c0c] w-4 h-4 rounded-none"
            />
            <span>INCLUDE MATHEMATICAL CHEAT SHEET</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={includePracticeExam}
              onChange={(e) => setIncludePracticeExam(e.target.checked)}
              className="accent-[#0c0c0c] w-4 h-4 rounded-none"
            />
            <span>INCLUDE MODEL PRACTICE EXAM</span>
          </label>
        </div>
      </div>

      {/* Structured Dossier Preview & PDF Action Bar */}
      <div className="border border-[#0c0c0c] bg-[#ffffff]">
        {/* Prominent Action Bar */}
        <div className="p-6 md:p-8 bg-[#fafafa] border-b border-[#0c0c0c] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="dark" size="sm">
                DOSSIER READY FOR EXPORT
              </Badge>
              <span className="text-[11px] font-mono text-[#6d6d6d]">
                DOC ID: {studyPack.id}
              </span>
            </div>
            <h3 className="text-[20px] font-bold font-tech text-[#0c0c0c] uppercase mt-1">
              {studyPack.title}
            </h3>
          </div>

          <div className="flex items-center gap-3">
            <PillButton
              variant="primary"
              size="lg"
              icon={<Download className="w-4 h-4" />}
              onClick={handleDownloadPdf}
            >
              DOWNLOAD OFFICIAL PDF
            </PillButton>
          </div>
        </div>

        {/* Dossier Content Preview */}
        <div className="p-8 md:p-12 space-y-12">
          {/* Executive Summary Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#cecece] pb-2">
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                SECTION 01 // CONCEPTUAL FOUNDATION
              </span>
            </div>
            <p className="text-[16px] text-[#0c0c0c] leading-relaxed font-sans">
              {studyPack.summary}
            </p>

            {studyPack.key_takeaways && (
              <div className="mt-4 p-4 bg-[#fafafa] border border-[#cecece] space-y-2">
                <span className="text-[11px] font-tech uppercase font-bold text-[#0c0c0c] block">
                  KEY AXIOMATIC TAKEAWAYS:
                </span>
                <ul className="space-y-1 text-[13px] text-[#6d6d6d] pl-4 list-disc">
                  {studyPack.key_takeaways.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Formula Sheet Section */}
          {studyPack.formula_sheet && studyPack.formula_sheet.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#cecece] pb-2">
                <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                  SECTION 02 // GOVERNING EQUATIONS REFERENCE
                </span>
              </div>

              <div className="border border-[#cecece] divide-y divide-[#cecece]">
                <div className="grid grid-cols-12 p-3 bg-[#fafafa] text-[11px] font-tech uppercase text-[#6d6d6d]">
                  <div className="col-span-4">RELATION / LAW</div>
                  <div className="col-span-4">MATHEMATICAL FORMULA</div>
                  <div className="col-span-4">VARIABLES & DEFINITION</div>
                </div>

                {studyPack.formula_sheet.map((f, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-1 md:grid-cols-12 p-4 gap-2 items-center text-[13px] hover:bg-[#fafafa]"
                  >
                    <div className="md:col-span-4 font-bold font-tech text-[#0c0c0c]">
                      {f.name}
                    </div>
                    <div className="md:col-span-4 font-mono text-[14px] bg-[#f4f4f4] p-2 border border-[#cecece] text-[#0c0c0c]">
                      {f.formula}
                    </div>
                    <div className="md:col-span-4 text-[#6d6d6d] text-[12px]">
                      {f.variables}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Flashcards Retrieval Deck Section */}
          {studyPack.flashcards && studyPack.flashcards.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#cecece] pb-2">
                <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                  SECTION 03 // ACTIVE RECALL FLASHCARDS (CLICK CARD TO REVEAL)
                </span>
                <span className="text-[11px] font-tech text-[#6d6d6d]">
                  {studyPack.flashcards.length} CARDS GENERATED
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {studyPack.flashcards.map((card) => {
                  const isFlipped = flippedCards[card.id];
                  return (
                    <div
                      key={card.id}
                      onClick={() => toggleFlip(card.id)}
                      className={`border p-6 min-h-[170px] flex flex-col justify-between cursor-pointer transition-all ${
                        isFlipped
                          ? 'border-[#0c0c0c] bg-[#fafafa]'
                          : 'border-[#cecece] hover:border-[#6d6d6d] bg-[#ffffff]'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-mono text-[#6d6d6d] uppercase">
                            {card.topic || 'CORE PRINCIPLE'}
                          </span>
                          <span className="text-[11px] font-tech uppercase text-[#6d6d6d] flex items-center gap-1">
                            <RotateCw className="w-3 h-3" />
                            {isFlipped ? 'ANSWER REVEALED' : 'CLICK TO FLIP'}
                          </span>
                        </div>

                        <p className="text-[15px] font-medium text-[#0c0c0c] font-sans">
                          {isFlipped ? card.back : card.front}
                        </p>
                      </div>

                      <div className="pt-3 border-t border-[#cecece]/40 flex items-center justify-between text-[11px] font-tech text-[#6d6d6d]">
                        <span>{isFlipped ? 'RECALL CHECK' : 'PROMPT'}</span>
                        <span className="uppercase font-mono">ID // {card.id}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Model Exam Problems Section */}
          {studyPack.sample_questions && studyPack.sample_questions.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-[#cecece] pb-2">
                <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                  SECTION 04 // MODEL PRACTICE EXAM DERIVATIONS
                </span>
              </div>

              <div className="space-y-4">
                {studyPack.sample_questions.map((sq, idx) => (
                  <div key={idx} className="border border-[#cecece] p-6 bg-[#ffffff] space-y-3">
                    <span className="text-[11px] font-tech uppercase font-bold text-[#6d6d6d]">
                      PROBLEM 0{idx + 1}:
                    </span>
                    <p className="text-[15px] font-bold text-[#0c0c0c] font-tech">
                      {sq.question}
                    </p>
                    <div className="p-4 bg-[#fafafa] border border-[#cecece] text-[13px] text-[#0c0c0c] font-mono leading-relaxed">
                      <strong className="block text-[#6d6d6d] font-tech mb-1 uppercase text-[11px]">
                        MODEL PROOF / SOLUTION:
                      </strong>
                      {sq.answer}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
