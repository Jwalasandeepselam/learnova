'use client';

import React, { useState } from 'react';
import { DocumentItem, Quiz, QuizQuestion, QuizResult, QuestionEvaluationResponse } from '@/lib/types';
import { learnovaApi } from '@/lib/api';
import { PillButton } from '@/components/ui/PillButton';
import { Badge } from '@/components/ui/Badge';
import { UnderlineInput } from '@/components/ui/UnderlineInput';
import {
  CheckSquare,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Award,
  Clock,
  ArrowRight,
  RefreshCw,
  Loader2
} from 'lucide-react';

interface QuizArenaTabProps {
  document: DocumentItem;
}

export const QuizArenaTab: React.FC<QuizArenaTabProps> = ({ document }) => {
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null);
  const [generating, setGenerating] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [evaluations, setEvaluations] = useState<Record<string, QuestionEvaluationResponse>>({});
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [submittingFull, setSubmittingFull] = useState(false);
  const [quizResult, setQuizResult] = useState<QuizResult | null>(null);
  const [difficulty, setDifficulty] = useState<'adaptive' | 'intermediate' | 'advanced'>('adaptive');

  const handleGenerateQuiz = async () => {
    try {
      setGenerating(true);
      setQuizResult(null);
      setSelectedAnswers({});
      setEvaluations({});
      setCurrentQuestionIdx(0);

      const generated = await learnovaApi.generateQuiz({
        document_id: document.id,
        difficulty: difficulty,
        question_count: 4
      });

      setActiveQuiz(generated);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleAnswerSelect = async (questionId: string, answerKey: string) => {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: answerKey }));

    if (activeQuiz) {
      try {
        const evalRes = await learnovaApi.evaluateQuizQuestion(
          activeQuiz.quiz_id,
          questionId,
          answerKey
        );
        setEvaluations((prev) => ({ ...prev, [questionId]: evalRes }));
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleCompleteQuiz = async () => {
    if (!activeQuiz) return;
    try {
      setSubmittingFull(true);
      const submissions = Object.entries(selectedAnswers).map(([qid, ans]) => ({
        question_id: qid,
        submitted_answer: ans
      }));

      const result = await learnovaApi.submitQuiz({
        quiz_id: activeQuiz.quiz_id,
        time_spent_seconds: 180,
        submissions: submissions
      });

      setQuizResult(result);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingFull(false);
    }
  };

  const currentQ = activeQuiz?.questions[currentQuestionIdx];
  const answeredCount = Object.keys(selectedAnswers).length;

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="border border-[#cecece] p-6 md:p-8 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                FORMATIVE ASSESSMENT ARENA // DIAGNOSTIC ENGINE
              </span>
            </div>
            <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
              ADAPTIVE PRACTICE & MASTERY CALIBRATION
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[11px] font-tech uppercase text-[#6d6d6d]">
              DIFFICULTY:
            </span>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as any)}
              className="border border-[#cecece] bg-transparent text-[13px] font-tech text-[#0c0c0c] py-1.5 px-3 outline-none"
              disabled={generating}
            >
              <option value="adaptive">ADAPTIVE (BAYESIAN)</option>
              <option value="intermediate">INTERMEDIATE</option>
              <option value="advanced">ADVANCED</option>
            </select>

            <PillButton
              variant="primary"
              size="sm"
              onClick={handleGenerateQuiz}
              disabled={generating}
              icon={generating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            >
              {activeQuiz ? 'REGENERATE QUIZ' : 'GENERATE QUIZ'}
            </PillButton>
          </div>
        </div>

        <p className="text-[14px] text-[#6d6d6d]">
          Questions test conceptual depth, mathematical derivations, and common student
          misconceptions identified from document chunks.
        </p>
      </div>

      {/* Quiz Active View or Initial CTA */}
      {!activeQuiz && !quizResult ? (
        <div className="border border-[#cecece] p-12 text-center bg-[#fafafa] space-y-6">
          <div className="w-16 h-16 rounded-full border border-[#cecece] bg-[#ffffff] mx-auto flex items-center justify-center text-[#0c0c0c]">
            <CheckSquare className="w-8 h-8" />
          </div>
          <div className="space-y-2 max-w-lg mx-auto">
            <h3 className="text-[20px] font-bold font-tech text-[#0c0c0c] uppercase">
              NO ACTIVE TEST IN SESSION
            </h3>
            <p className="text-[14px] text-[#6d6d6d]">
              Generate a synthesized 4-question formative assessment calibrated to this document's
              concepts to diagnose weak points and reinforce your knowledge retention.
            </p>
          </div>
          <PillButton
            variant="primary"
            size="lg"
            onClick={handleGenerateQuiz}
            disabled={generating}
            icon={generating ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
          >
            {generating ? 'SYNTHESIZING QUESTIONS...' : 'START DIAGNOSTIC TEST'}
          </PillButton>
        </div>
      ) : quizResult ? (
        /* Results View */
        <div className="border border-[#0c0c0c] p-8 md:p-10 bg-[#ffffff] space-y-8">
          <div className="flex items-center justify-between pb-6 border-b border-[#cecece]">
            <div>
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                ASSESSMENT DOSSIER // COMPLETED
              </span>
              <h3 className="text-[26px] font-bold font-tech text-[#0c0c0c] uppercase mt-1">
                PERFORMANCE SCORE: {quizResult.score_percentage}%
              </h3>
            </div>
            <Badge
              variant={quizResult.score_percentage >= 80 ? 'success' : 'warning'}
              size="md"
            >
              {quizResult.correct_count} / {quizResult.total_questions} CORRECT
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-4 border-y border-[#cecece]">
            <div>
              <span className="text-[11px] font-tech text-[#6d6d6d] uppercase">TIME INVESTED</span>
              <p className="text-[28px] font-bold font-tech text-[#0c0c0c]">
                {Math.round(quizResult.time_spent_seconds / 60)}m {quizResult.time_spent_seconds % 60}s
              </p>
            </div>
            <div className="border-y md:border-y-0 md:border-x border-[#cecece] py-2 md:py-0 md:px-6">
              <span className="text-[11px] font-tech text-[#6d6d6d] uppercase">NEXT SPACED REVIEW</span>
              <p className="text-[28px] font-bold font-tech text-[#0c0c0c]">
                {new Date(quizResult.recommended_review_date || Date.now() + 3 * 86400000).toLocaleDateString()}
              </p>
            </div>
            <div className="md:pl-6">
              <span className="text-[11px] font-tech text-[#6d6d6d] uppercase">KNOWLEDGE GAIN</span>
              <p className="text-[28px] font-bold font-tech text-[#137333]">
                +6.5% BKT
              </p>
            </div>
          </div>

          {/* Topic Breakdown */}
          <div className="space-y-4">
            <h4 className="text-[16px] font-bold font-tech text-[#0c0c0c] uppercase">
              TOPIC-BY-TOPIC MASTERY ADJUSTMENTS
            </h4>
            <div className="divide-y divide-[#cecece] border border-[#cecece]">
              {quizResult.topic_breakdown.map((tb, idx) => (
                <div key={idx} className="p-4 flex items-center justify-between bg-[#fafafa]">
                  <div>
                    <span className="font-tech font-bold text-[14px] text-[#0c0c0c]">
                      {tb.topic_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-6">
                    <span className="text-[13px] font-mono text-[#6d6d6d]">
                      Score: {(tb.score * 100).toFixed(0)}%
                    </span>
                    <Badge variant="dark" size="sm">
                      NEW MASTERY: {Math.round(tb.new_mastery_level * 100)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-4 border-t border-[#cecece]">
            <PillButton variant="secondary" size="md" onClick={handleGenerateQuiz}>
              GENERATE NEW PRACTICE SET
            </PillButton>
          </div>
        </div>
      ) : (
        /* Active Questions View */
        currentQ && (
          <div className="border border-[#cecece] p-8 md:p-10 bg-[#ffffff] space-y-8">
            <div className="flex items-center justify-between pb-4 border-b border-[#cecece]">
              <div className="flex items-center gap-3">
                <span className="text-[12px] font-mono text-[#6d6d6d]">
                  QUESTION {currentQuestionIdx + 1} OF {activeQuiz.total_questions}
                </span>
                <Badge variant="outline" size="sm">
                  {currentQ.type.toUpperCase()}
                </Badge>
              </div>

              <div className="flex items-center gap-2">
                {activeQuiz.questions.map((_, qIdx) => (
                  <button
                    key={qIdx}
                    onClick={() => setCurrentQuestionIdx(qIdx)}
                    className={`w-7 h-7 text-[12px] font-mono flex items-center justify-center border transition-all ${
                      currentQuestionIdx === qIdx
                        ? 'border-[#0c0c0c] bg-[#0c0c0c] text-[#ffffff] font-bold'
                        : selectedAnswers[activeQuiz.questions[qIdx].id]
                        ? 'border-[#cecece] bg-[#eaeaea] text-[#0c0c0c]'
                        : 'border-[#cecece] text-[#6d6d6d] hover:border-[#0c0c0c]'
                    }`}
                  >
                    {qIdx + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Prompt */}
            <div className="space-y-4">
              <h3 className="text-[18px] md:text-[20px] font-bold text-[#0c0c0c] font-tech leading-snug">
                {currentQ.prompt}
              </h3>

              {/* Options */}
              {currentQ.options && (
                <div className="space-y-3 pt-2">
                  {currentQ.options.map((opt) => {
                    const isSelected = selectedAnswers[currentQ.id] === opt.key;
                    const evaluation = evaluations[currentQ.id];
                    const isCorrect = evaluation?.is_correct && isSelected;
                    const isWrong = evaluation && !evaluation.is_correct && isSelected;

                    return (
                      <button
                        key={opt.key}
                        onClick={() => handleAnswerSelect(currentQ.id, opt.key)}
                        className={`w-full text-left p-4 border transition-all flex items-start gap-3 ${
                          isSelected
                            ? 'border-[#0c0c0c] bg-[#fafafa]'
                            : 'border-[#cecece] hover:border-[#6d6d6d] bg-[#ffffff]'
                        }`}
                      >
                        <span
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-[12px] font-bold font-mono flex-shrink-0 ${
                            isSelected
                              ? 'bg-[#0c0c0c] text-[#ffffff]'
                              : 'border border-[#cecece] text-[#6d6d6d]'
                          }`}
                        >
                          {opt.key}
                        </span>
                        <span className="text-[15px] text-[#0c0c0c] font-sans pt-0.5">
                          {opt.text}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Short Answer Input */}
              {currentQ.type !== 'mcq' && (
                <div className="space-y-4 pt-4">
                  <UnderlineInput
                    placeholder="Type your explanation or mathematical derivation..."
                    value={selectedAnswers[currentQ.id] || ''}
                    onChange={(e) =>
                      setSelectedAnswers((prev) => ({
                        ...prev,
                        [currentQ.id]: e.target.value
                      }))
                    }
                  />
                  <PillButton
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      handleAnswerSelect(currentQ.id, selectedAnswers[currentQ.id] || '')
                    }
                    disabled={!selectedAnswers[currentQ.id]}
                  >
                    SUBMIT & EVALUATE
                  </PillButton>
                </div>
              )}
            </div>

            {/* Instant Automated Evaluation & Explanation */}
            {evaluations[currentQ.id] && (
              <div
                className={`p-6 border space-y-3 ${
                  evaluations[currentQ.id].is_correct
                    ? 'border-[#b7e1cd] bg-[#eaf7ee]'
                    : 'border-[#f5b4af] bg-[#fce8e6]'
                }`}
              >
                <div className="flex items-center gap-2">
                  {evaluations[currentQ.id].is_correct ? (
                    <CheckCircle2 className="w-5 h-5 text-[#137333]" />
                  ) : (
                    <XCircle className="w-5 h-5 text-[#c5221f]" />
                  )}
                  <span
                    className={`text-[13px] font-tech uppercase font-bold tracking-wider ${
                      evaluations[currentQ.id].is_correct ? 'text-[#137333]' : 'text-[#c5221f]'
                    }`}
                  >
                    {evaluations[currentQ.id].is_correct ? 'CORRECT REASONING' : 'INCORRECT REASONING'}
                  </span>
                </div>

                <p className="text-[14px] text-[#0c0c0c] font-sans leading-relaxed">
                  {evaluations[currentQ.id].explanation}
                </p>

                {evaluations[currentQ.id].citation && (
                  <p className="text-[12px] font-mono text-[#6d6d6d] pt-2 border-t border-[#cecece]/60">
                    Source citation: Page {evaluations[currentQ.id].citation?.page_number} //
                    Chunk {evaluations[currentQ.id].citation?.chunk_id}
                  </p>
                )}
              </div>
            )}

            {/* Question Navigation Footer */}
            <div className="flex items-center justify-between pt-6 border-t border-[#cecece]">
              <button
                disabled={currentQuestionIdx === 0}
                onClick={() => setCurrentQuestionIdx((p) => p - 1)}
                className="text-[13px] font-tech uppercase text-[#6d6d6d] hover:text-[#0c0c0c] disabled:opacity-30"
              >
                PREVIOUS
              </button>

              <div className="flex items-center gap-4">
                {currentQuestionIdx < activeQuiz.total_questions - 1 ? (
                  <PillButton
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentQuestionIdx((p) => p + 1)}
                  >
                    NEXT QUESTION
                  </PillButton>
                ) : (
                  <PillButton
                    variant="primary"
                    size="md"
                    onClick={handleCompleteQuiz}
                    disabled={submittingFull || answeredCount === 0}
                    icon={submittingFull ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
                  >
                    {submittingFull ? 'COMPILING RESULTS...' : 'FINISH & VIEW SCORE'}
                  </PillButton>
                )}
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
};
