'use client';

import React, { useState } from 'react';
import { DocumentItem, PedagogicalMode, TeachResponse, EvaluateAnswerResponse } from '@/lib/types';
import { learnovaApi } from '@/lib/api';
import { PillButton } from '@/components/ui/PillButton';
import { Badge } from '@/components/ui/Badge';
import { UnderlineInput } from '@/components/ui/UnderlineInput';
import {
  BrainCircuit,
  Sparkles,
  HelpCircle,
  Lightbulb,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Send,
  Loader2,
  Bookmark
} from 'lucide-react';

interface SocraticTutorTabProps {
  document: DocumentItem;
  initialTopic?: string;
}

interface SocraticStep {
  id: string;
  type: 'explanation' | 'student_answer' | 'evaluation' | 'alternate_modality';
  title?: string;
  content: string;
  modality?: string;
  diagnosticQuestion?: {
    question_id: string;
    prompt: string;
    hints?: string[];
  };
  evaluation?: EvaluateAnswerResponse;
  timestamp: string;
}

export const SocraticTutorTab: React.FC<SocraticTutorTabProps> = ({
  document,
  initialTopic
}) => {
  const [currentTopic, setCurrentTopic] = useState(
    initialTopic || document.topics?.[0]?.name || 'Wave-Particle Duality & de Broglie Relation'
  );
  const [sessionId, setSessionId] = useState(`sess_${Date.now()}`);
  const [steps, setSteps] = useState<SocraticStep[]>([
    {
      id: 'step_intro',
      type: 'explanation',
      title: 'FOUNDATIONAL SCAFFOLDING // STEP 01',
      content:
        'Welcome to the Socratic Learning Lab. Rather than lecturing, we construct understanding together through first principles. Consider matter: in classical mechanics, an electron has a point position and linear momentum p = mv. But in quantum physics, de Broglie proposed that anything carrying momentum p must also carry an intrinsic wavelength λ = h / p.',
      diagnosticQuestion: {
        question_id: 'q_diag_01',
        prompt:
          'If we accelerate an electron such that its momentum p triples (p → 3p), what happens to its associated matter wavelength λ?',
        hints: [
          'Examine the mathematical relation λ = h/p.',
          'Is the relationship direct or inversely proportional?'
        ]
      },
      timestamp: new Date().toLocaleTimeString()
    }
  ]);

  const [studentAnswer, setStudentAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [showHints, setShowHints] = useState(false);

  // Strategy Quick Action Pills
  const strategyPills: Array<{
    label: string;
    modality: 'simpler' | 'analogy' | 'example' | 'step_by_step' | 'mathematical' | 'socratic';
    action: string;
  }> = [
    { label: 'Explain Simpler', modality: 'simpler', action: 'explain' },
    { label: 'Give Analogy', modality: 'analogy', action: 'explain' },
    { label: 'Real-World Example', modality: 'example', action: 'explain' },
    { label: 'Step-by-Step', modality: 'step_by_step', action: 'explain' },
    { label: 'Mathematical', modality: 'mathematical', action: 'explain' },
    { label: 'Test Me', modality: 'socratic', action: 'teach' },
    { label: 'Go Deeper', modality: 'socratic', action: 'teach' }
  ];

  const handleApplyStrategy = async (item: typeof strategyPills[0]) => {
    try {
      setLoading(true);
      if (item.action === 'explain') {
        const res = await learnovaApi.explainAgain({
          session_id: sessionId,
          target_concept: currentTopic,
          desired_modality: item.modality as 'simpler' | 'analogy' | 'example' | 'step_by_step' | 'mathematical'
        });

        setSteps((prev) => [
          ...prev,
          {
            id: `step_${Date.now()}`,
            type: 'alternate_modality',
            title: `PEDAGOGICAL SHIFT // [${item.label.toUpperCase()}]`,
            content: res.revised_explanation,
            modality: res.modality_used,
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      } else {
        const res = await learnovaApi.teachConcept({
          document_id: document.id,
          session_id: sessionId,
          pedagogical_mode: item.modality
        });

        setSteps((prev) => [
          ...prev,
          {
            id: `step_${Date.now()}`,
            type: 'explanation',
            title: `SOCRATIC PROGRESSION // [${item.label.toUpperCase()}]`,
            content: res.scaffold_explanation,
            diagnosticQuestion: res.diagnostic_question,
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async () => {
    if (!studentAnswer.trim()) return;

    try {
      setLoading(true);
      const activeQuestion = [...steps].reverse().find((s) => s.diagnosticQuestion)?.diagnosticQuestion;
      const questionId = activeQuestion?.question_id || 'q_diag_01';

      // Append student answer step
      const answerText = studentAnswer;
      setStudentAnswer('');

      const evalRes = await learnovaApi.evaluateAnswer({
        session_id: sessionId,
        question_id: questionId,
        student_answer: answerText
      });

      setSteps((prev) => [
        ...prev,
        {
          id: `step_ans_${Date.now()}`,
          type: 'student_answer',
          title: 'STUDENT REASONING SUBMITTED',
          content: answerText,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: `step_eval_${Date.now()}`,
          type: 'evaluation',
          title: evalRes.is_correct ? 'VALIDATION // ACCURATE' : 'DIAGNOSIS // MISCONCEPTION DETECTED',
          content: evalRes.scaffolded_hint || 'Answer evaluated.',
          evaluation: evalRes,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Topic Dossier Header */}
      <div className="border border-[#cecece] p-6 md:p-8 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                SOCRATIC TUTORING ENGINE // ACTIVE DIALECTIC
              </span>
            </div>
            <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
              {currentTopic}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[11px] font-tech uppercase text-[#6d6d6d]">
              TOPIC SWITCHER:
            </span>
            <select
              value={currentTopic}
              onChange={(e) => {
                setCurrentTopic(e.target.value);
                setSessionId(`sess_${Date.now()}`);
                setSteps([
                  {
                    id: 'step_new',
                    type: 'explanation',
                    title: 'SOCRATIC FOCUS // INITIAL INQUIRY',
                    content: `We are now exploring "${e.target.value}". What is your current mental model of how this concept works? Or would you like me to introduce its first principles?`,
                    timestamp: new Date().toLocaleTimeString()
                  }
                ]);
              }}
              className="border border-[#cecece] bg-transparent text-[13px] font-tech text-[#0c0c0c] py-1.5 px-3 outline-none focus:border-[#0c0c0c]"
            >
              {document.topics?.map((t) => (
                <option key={t.id} value={t.name}>
                  {t.name}
                </option>
              )) || <option>{currentTopic}</option>}
            </select>
          </div>
        </div>

        {/* Quick Action Strategy Pills */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-tech uppercase tracking-widest text-[#6d6d6d]">
              PEDAGOGICAL MODALITY CONTROLS // QUICK ACTIONS:
            </span>
            <span className="text-[11px] font-tech text-[#6d6d6d]">
              ADAPT TUTOR'S COGNITIVE ANGLE
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {strategyPills.map((pill) => (
              <button
                key={pill.label}
                disabled={loading}
                onClick={() => handleApplyStrategy(pill)}
                className="px-4 py-1.5 rounded-full border border-[#cecece] bg-[#ffffff] hover:border-[#0c0c0c] hover:bg-[#fafafa] text-[12px] font-tech font-medium text-[#0c0c0c] tracking-tight transition-all disabled:opacity-40"
              >
                [{pill.label}]
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Socratic Dialog Feed */}
      <div className="space-y-6">
        {steps.map((step) => (
          <div
            key={step.id}
            className={`border p-6 md:p-8 transition-all ${
              step.type === 'student_answer'
                ? 'border-[#0c0c0c] bg-[#fafafa] ml-4 md:ml-12'
                : step.type === 'evaluation'
                ? step.evaluation?.is_correct
                  ? 'border-[#b7e1cd] bg-[#eaf7ee]'
                  : 'border-[#f5b4af] bg-[#fce8e6]'
                : step.type === 'alternate_modality'
                ? 'border-[#cecece] bg-[#ffffff]'
                : 'border-[#cecece] bg-[#ffffff]'
            }`}
          >
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#cecece]/60">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                  {step.title || 'SOCRATIC NODE'}
                </span>
                {step.modality && (
                  <Badge variant="outline" size="sm">
                    {step.modality.toUpperCase()}
                  </Badge>
                )}
              </div>
              <span className="text-[11px] font-mono text-[#6d6d6d]">
                {step.timestamp}
              </span>
            </div>

            <p className="text-[15px] md:text-[16px] text-[#0c0c0c] leading-relaxed whitespace-pre-line font-sans">
              {step.content}
            </p>

            {/* Diagnostic Formative Question */}
            {step.diagnosticQuestion && (
              <div className="mt-6 p-6 border border-[#0c0c0c] bg-[#fafafa] space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-[#0c0c0c]" />
                    <span className="text-[11px] font-tech uppercase tracking-widest text-[#0c0c0c] font-bold">
                      FORMATIVE DIAGNOSTIC CHECK
                    </span>
                  </div>
                  {step.diagnosticQuestion.hints && (
                    <button
                      onClick={() => setShowHints(!showHints)}
                      className="text-[11px] font-tech uppercase text-[#6d6d6d] hover:text-[#0c0c0c] underline flex items-center gap-1"
                    >
                      <Lightbulb className="w-3.5 h-3.5" />
                      {showHints ? 'HIDE HINTS' : 'VIEW HINTS'}
                    </button>
                  )}
                </div>

                <p className="text-[15px] font-medium text-[#0c0c0c] font-sans">
                  {step.diagnosticQuestion.prompt}
                </p>

                {showHints && step.diagnosticQuestion.hints && (
                  <div className="p-3 bg-[#ffffff] border border-[#cecece] text-[12px] text-[#6d6d6d] space-y-1">
                    <span className="font-bold text-[#0c0c0c] block uppercase font-tech">
                      SCAFFOLDING HINTS:
                    </span>
                    {step.diagnosticQuestion.hints.map((hint, hIdx) => (
                      <p key={hIdx}>• {hint}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Misconception Alert Diagnosis */}
            {step.evaluation?.misconception?.detected && (
              <div className="mt-4 p-4 border border-[#c5221f] bg-[#ffffff] space-y-2">
                <div className="flex items-center gap-2 text-[#c5221f]">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-[12px] font-tech uppercase font-bold tracking-wider">
                    MISCONCEPTION DIAGNOSED: {step.evaluation.misconception.category}
                  </span>
                </div>
                <p className="text-[13px] text-[#0c0c0c] font-medium">
                  {step.evaluation.misconception.summary}
                </p>
                <p className="text-[12px] text-[#6d6d6d]">
                  {step.evaluation.misconception.explanation}
                </p>
              </div>
            )}

            {/* Mastery Score Delta */}
            {step.evaluation && (
              <div className="mt-4 flex items-center justify-between text-[12px] font-tech text-[#6d6d6d] border-t border-[#cecece]/40 pt-3">
                <span>
                  UNDERSTANDING LEVEL:{' '}
                  <strong className="text-[#0c0c0c]">{step.evaluation.understanding_level}</strong>
                </span>
                <span>
                  MASTERY DELTA:{' '}
                  <strong
                    className={
                      step.evaluation.mastery_delta >= 0 ? 'text-[#137333]' : 'text-[#c5221f]'
                    }
                  >
                    {step.evaluation.mastery_delta >= 0
                      ? `+${step.evaluation.mastery_delta}`
                      : `${step.evaluation.mastery_delta}`}
                  </strong>
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Answer Input Bar */}
      <div className="border border-[#0c0c0c] p-6 bg-[#ffffff]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-tech uppercase tracking-widest text-[#6d6d6d]">
            YOUR SCIENTIFIC REASONING // RESPONSE INPUT
          </span>
          <span className="text-[11px] font-tech text-[#6d6d6d]">
            EXPLAIN IN YOUR OWN WORDS
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch gap-4">
          <div className="flex-1">
            <UnderlineInput
              placeholder="e.g. Since wavelength λ is inversely proportional to momentum p (λ = h/p), tripling momentum reduces λ to one third..."
              value={studentAnswer}
              onChange={(e) => setStudentAnswer(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAnswerSubmit();
                }
              }}
              disabled={loading}
            />
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <PillButton
              variant="primary"
              size="md"
              onClick={handleAnswerSubmit}
              disabled={loading || !studentAnswer.trim()}
              icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            >
              EVALUATE REASONING
            </PillButton>
          </div>
        </div>
      </div>
    </div>
  );
};
