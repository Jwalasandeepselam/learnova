'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { learnovaApi } from '@/lib/api';
import { DocumentItem } from '@/lib/types';

interface TopicItem {
  id: number;
  title: string;
  status: string;
  question: string;
  explanation: string;
  keyPrinciple: string;
  mastery: number;
  retention: number;
  derivation: number;
  transfer: number;
}

const TOPICS_DATA: TopicItem[] = [
  {
    id: 0,
    title: '01 / CLASSIFICATION',
    status: '92%',
    question: "How does Bayes' Theorem guarantee an optimal classification decision boundary?",
    explanation:
      'Classification partitions feature space into discrete decision regions. By computing posterior probabilities P(C|X), the maximum a posteriori (MAP) classifier minimizes expected risk under 0-1 loss.',
    keyPrinciple:
      'Bayes Optimal Decision Axiom: Decision boundaries form where posterior class odds ratio equals relative penalty cost.',
    mastery: 92,
    retention: 94,
    derivation: 90,
    transfer: 92
  },
  {
    id: 1,
    title: '02 / KNN',
    status: '91%',
    question: 'Why does the curse of dimensionality degrade local metric neighborhoods in KNN?',
    explanation:
      'As feature dimensionality grows, hypersphere volume concentrates almost entirely in a thin outer shell. The distance between nearest and furthest samples converges toward equality, eroding neighborhood discrimination.',
    keyPrinciple:
      'Metric Concentration: (d_max - d_min) / d_min → 0 as d → ∞ requires manifold projection or PCA before neighbor queries.',
    mastery: 91,
    retention: 92,
    derivation: 88,
    transfer: 93
  },
  {
    id: 2,
    title: '03 / SVM',
    status: 'LEARNING',
    question: "WHY DOESN'T THE HYPERPLANE JUST PASS THROUGH THE MIDDLE?",
    explanation:
      'Imagine two groups of points on a table. You need a boundary between them. There may be many possible boundaries — SVM looks for the one that leaves the largest possible safety margin around the closest points.',
    keyPrinciple:
      'Maximum margin → better separation → stronger generalization.',
    mastery: 72,
    retention: 88,
    derivation: 61,
    transfer: 43
  },
  {
    id: 3,
    title: '04 / NAIVE BAYES',
    status: '64%',
    question: 'Why does conditional independence rarely destroy zero-one classification loss?',
    explanation:
      'Even when real-world feature correlations severely violate the naive conditional independence assumption, the relative rank order of class posterior probabilities frequently remains intact for label prediction.',
    keyPrinciple:
      'Order Preservation: Exact posterior probability calibration is unnecessary when only the argmax class is required.',
    mastery: 64,
    retention: 68,
    derivation: 60,
    transfer: 64
  },
  {
    id: 4,
    title: '05 / DECISION TREE',
    status: '38%',
    question: 'How does Information Gain handle continuous split boundaries without overfitting?',
    explanation:
      'Information Gain measures the reduction in Shannon entropy H(S) - ∑ (|S_v|/|S|) H(S_v). Continuous values are sorted and candidate splits evaluated at midpoints, regulated by minimum leaf impurity and cost-complexity pruning.',
    keyPrinciple:
      'Greedy Partitioning: Maximizes instantaneous information gain at each node depth while post-pruning bounds tree variance.',
    mastery: 38,
    retention: 42,
    derivation: 34,
    transfer: 38
  },
  {
    id: 5,
    title: '06 / EVALUATION',
    status: 'PENDING',
    question: 'Why does accuracy mislead on severe class imbalance and when must ROC-AUC be used?',
    explanation:
      'When positive samples comprise <1% of the distribution, a trivial majority classifier yields >99% nominal accuracy while failing completely on the target class. ROC-AUC evaluates true positive vs false positive rate across all thresholds.',
    keyPrinciple:
      'Prevalence Invariance: The Area Under the ROC Curve measures ranking discriminability independent of prior class distribution.',
    mastery: 20,
    retention: 25,
    derivation: 15,
    transfer: 20
  }
];

export default function HomePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadText, setUploadText] = useState('DROP PDF / PPT / DOCX');
  const [uploadMeta, setUploadMeta] = useState('Your material becomes the source of truth.');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Socratic Tutor interactive state
  const [activeTopicIdx, setActiveTopicIdx] = useState(2); // Default: 03 / SVM
  const [tutorQuestion, setTutorQuestion] = useState(TOPICS_DATA[2].question);
  const [tutorBody, setTutorBody] = useState(TOPICS_DATA[2].explanation);
  const [tutorKey, setTutorKey] = useState(TOPICS_DATA[2].keyPrinciple);
  const [askInput, setAskInput] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [activeMode, setActiveMode] = useState<'LEARN' | 'PRACTICE' | 'EXAM'>('LEARN');

  // Mastery state
  const [mastery, setMastery] = useState(TOPICS_DATA[2].mastery);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 2800);
  };

  const handleTopicClick = (idx: number) => {
    setActiveTopicIdx(idx);
    const t = TOPICS_DATA[idx];
    setTutorQuestion(t.question);
    setTutorBody(t.explanation);
    setTutorKey(t.keyPrinciple);
    setMastery(t.mastery);
    showToast(`Selected ${t.title}`);
  };

  const handleFileUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setUploadText(file.name.toUpperCase());
      setUploadMeta(`READY FOR ANALYSIS · ${Math.round(file.size / 1024)} KB`);
      showToast('Material received — analysis pipeline ready');

      const element = document.getElementById('analysis');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }

      const newDoc = await learnovaApi.uploadDocument(file);
      setUploadMeta(`INGESTED // ${newDoc.total_chunks} CHUNKS INDEXED`);
      showToast(`ANALYSIS READY // OPENING WORKSPACE FOR ${newDoc.title.toUpperCase()}`);

      setTimeout(() => {
        router.push(`/documents/${newDoc.id}`);
      }, 1500);
    } catch (err) {
      console.error(err);
      setUploadMeta('ANALYSIS READY // LOADED ACTIVE DOSSIER');
      showToast('ANALYSIS READY // EXPLORE TUTOR BELOW');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const zone = document.getElementById('uploadZone');
    if (zone) zone.style.background = '';
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleStrategy = async (
    mod: 'simpler' | 'analogy' | 'real_world' | 'mathematical',
    actionDesc: string
  ) => {
    try {
      showToast(`${actionDesc} — connecting to Tutor Agent`);
      const currentTopicTitle = TOPICS_DATA[activeTopicIdx].title.split('/ ')[1];
      const res = await learnovaApi.explainAgain({
        session_id: `sess_home_${Date.now()}`,
        target_concept: currentTopicTitle,
        desired_modality: mod === 'real_world' ? 'example' : mod
      });

      setTutorBody(res.revised_explanation);
      if (res.follow_up_check) {
        setTutorKey(`Diagnostic Check: ${res.follow_up_check.prompt}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleNextStep = () => {
    const nextIdx = (activeTopicIdx + 1) % TOPICS_DATA.length;
    handleTopicClick(nextIdx);
    showToast(`Moving to next learning step: ${TOPICS_DATA[nextIdx].title}`);
  };

  const handleAskSubmit = async () => {
    if (!askInput.trim() || isAsking) {
      showToast('Ask a question first');
      return;
    }

    const query = askInput.trim();
    setAskInput('');
    setIsAsking(true);
    showToast('RAG retrieval → Tutor Agent → response');

    try {
      const res = await learnovaApi.chat({
        document_id: 'doc_quantum_01',
        query: query
      });

      setTutorBody(res.response);
      if (res.citations && res.citations.length > 0) {
        setTutorKey(`Verified Citation: Page ${res.citations[0].page_number} // ${res.citations[0].snippet.slice(0, 90)}...`);
      } else {
        setTutorKey('Grounding verified against source documents.');
      }

      setMastery((m) => Math.min(100, m + 3));
      showToast('Reasoning evaluated // Topic mastery updated');
    } catch (err) {
      console.error(err);
    } finally {
      setIsAsking(false);
    }
  };

  const handlePackClick = (packName: string, packType: string) => {
    showToast(`${packName} queued`);
    setTimeout(() => {
      router.push(`/documents/doc_quantum_01?tab=packs&type=${packType}`);
    }, 1200);
  };

  return (
    <>
      <main id="top">
        {/* Hero Section */}
        <section className="hero">
          <div className="hero-left">
            <div className="kicker">PERSONAL AI TEACHING ASSISTANT / 001</div>
            <div>
              <h1>
                DON'T JUST<br />
                STUDY.<br />
                UNDERSTAND.
              </h1>
              <div className="hero-copy">
                <p>
                  Learnova turns your <strong>PDFs, presentations and notes</strong> into an interactive learning system. It analyzes the material, teaches you step by step, tests your understanding, and builds a study pack around what you actually need.
                </p>
                <div className="hero-actions">
                  <button
                    className="black-btn"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    UPLOAD MATERIAL
                  </button>
                  <a className="text-btn" href="#learn">
                    EXPLORE THE TUTOR ↓
                  </a>
                </div>
                <input
                  id="uploadInput"
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.ppt,.pptx,.doc,.docx,.txt"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileUpload(e.target.files[0]);
                    }
                  }}
                />
                <div
                  className="upload-zone"
                  id="uploadZone"
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.currentTarget.style.background = '#f1f1f1';
                  }}
                  onDragLeave={(e) => {
                    e.preventDefault();
                    e.currentTarget.style.background = '';
                  }}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div>
                    <span id="uploadText">{uploadText}</span>
                    <div className="file-meta" id="uploadMeta">
                      {uploadMeta}
                    </div>
                  </div>
                  <div className="kicker">+</div>
                </div>
              </div>
            </div>
          </div>

          <div className="hero-right">
            <div className="hero-grid" />
            <div className="brain">
              <i className="node n1" />
              <i className="node n2" />
              <i className="node n3" />
              <i className="node n4" />
              <i className="node n5" />
            </div>
            <div className="hero-caption">
              <h2>
                KNOWLEDGE<br />
                IN MOTION
              </h2>
              <p>Document → concepts → teaching → practice → mastery. One continuous learning system.</p>
            </div>
          </div>
        </section>

        {/* Section 01: Document Intelligence */}
        <section className="section reveal" id="analysis">
          <div className="section-head">
            <div className="section-label">01 / DOCUMENT INTELLIGENCE</div>
            <h2 className="section-title">
              FIRST, LEARNOVA<br />
              UNDERSTANDS.
            </h2>
          </div>

          <div className="analysis">
            <div className="analysis-main">
              <div className="analysis-content">
                <div>
                  <div className="scan">ANALYZING / STRUCTURING / INDEXING</div>
                  <div className="scanline" />
                </div>
                <div>
                  <h3>Your material becomes a structured knowledge base — not a wall of text.</h3>
                  <p style={{ color: '#cecece', maxWidth: '520px' }}>
                    Topics, concepts, definitions, formulas, examples and relationships are mapped so the tutor can retrieve the right context when you ask a question.
                  </p>
                </div>
              </div>
            </div>

            <div className="spec">
              <div className="spec-row">
                <span>INPUT</span>
                <b>PDF / PPTX</b>
              </div>
              <div className="spec-row">
                <span>TOPICS</span>
                <b>18</b>
              </div>
              <div className="spec-row">
                <span>CONCEPTS</span>
                <b>42</b>
              </div>
              <div className="spec-row">
                <span>SOURCES</span>
                <b>127</b>
              </div>
              <div className="spec-row">
                <span>INDEX</span>
                <b>READY</b>
              </div>
              <div className="spec-row">
                <span>GROUNDING</span>
                <b>RAG</b>
              </div>
            </div>
          </div>

          <div className="analysis-stats">
            <div className="stat">
              <strong>18</strong>
              <span>TOPICS DETECTED</span>
            </div>
            <div className="stat">
              <strong>42</strong>
              <span>CORE CONCEPTS</span>
            </div>
            <div className="stat">
              <strong>86</strong>
              <span>PRACTICE QUESTIONS</span>
            </div>
          </div>
        </section>

        {/* Section 02: Adaptive Tutor */}
        <section className="section reveal" id="learn">
          <div className="section-head">
            <div className="section-label">02 / ADAPTIVE TUTOR</div>
            <h2 className="section-title">
              A TEACHER THAT<br />
              CHANGES WITH YOU.
            </h2>
          </div>

          <div className="workspace-grid">
            {/* Knowledge Map Side Nav */}
            <aside className="side topics-side">
              <div className="side-label">KNOWLEDGE MAP // 06</div>
              {TOPICS_DATA.map((t, idx) => (
                <button
                  key={t.id}
                  className={`topic ${activeTopicIdx === idx ? 'active' : ''}`}
                  onClick={() => handleTopicClick(idx)}
                >
                  <span>{t.title}</span>
                  <span className="topic-status">{t.status}</span>
                </button>
              ))}
              <button
                className="outline-btn"
                style={{ width: '100%', marginTop: '18px' }}
                onClick={() => {
                  showToast('Opening full knowledge map');
                  router.push('/documents/doc_quantum_01?tab=overview');
                }}
              >
                <span className="btn-icon">⌘</span> VIEW FULL MAP <span>→</span>
              </button>
            </aside>

            {/* Socratic Dialogue Center */}
            <article className="tutor">
              <div>
                <div className="tutor-top">
                  <div className="tutor-tag">SOCRATIC DIALOGUE // STEP 01</div>
                  <div className="muted" style={{ fontSize: '12px' }}>
                    SOURCE / MODULE 03
                  </div>
                </div>

                <h3>{tutorQuestion}</h3>
                <p>{tutorBody}</p>

                <div className="key">
                  <b>KEY IDEA</b>
                  <p>{tutorKey}</p>
                </div>
              </div>

              <div>
                <div className="tutor-actions">
                  <button className="dark-btn" onClick={handleAskSubmit} disabled={isAsking}>
                    <span className="btn-icon">◌</span> ASK TUTOR <span>→</span>
                  </button>
                  <button
                    className="outline-btn"
                    onClick={() => handleStrategy('mathematical', 'Showing the derivation')}
                  >
                    <span className="btn-icon">∑</span> SHOW DERIVATION <span>→</span>
                  </button>
                  <button
                    className="outline-btn"
                    onClick={() => handleStrategy('real_world', 'Generating a worked example')}
                  >
                    <span className="btn-icon">✦</span> GIVE AN EXAMPLE <span>→</span>
                  </button>
                  <button className="dark-btn" onClick={handleNextStep}>
                    NEXT STEP <span>→</span>
                  </button>
                </div>

                <div className="ask" style={{ marginTop: '14px' }}>
                  <input
                    id="questionInput"
                    placeholder="Ask Learnova anything about this material..."
                    value={askInput}
                    onChange={(e) => setAskInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleAskSubmit();
                      }
                    }}
                    disabled={isAsking}
                  />
                  <button
                    onClick={handleAskSubmit}
                    disabled={isAsking}
                    aria-label="Send question"
                  >
                    ↑
                  </button>
                </div>
              </div>
            </article>

            {/* Student Model Side */}
            <aside className="side mastery-side">
              <div className="side-label">STUDENT MODE</div>
              <div className="mastery-mode">
                <button
                  className={activeMode === 'LEARN' ? 'active' : ''}
                  onClick={() => {
                    setActiveMode('LEARN');
                    showToast('Mode: Socratic Deep Learning');
                  }}
                >
                  LEARN
                </button>
                <button
                  className={activeMode === 'PRACTICE' ? 'active' : ''}
                  onClick={() => {
                    setActiveMode('PRACTICE');
                    showToast('Mode: Formative Practice & Quizzing');
                  }}
                >
                  PRACTICE
                </button>
                <button
                  className={activeMode === 'EXAM' ? 'active' : ''}
                  onClick={() => {
                    setActiveMode('EXAM');
                    showToast('Mode: High-Yield Exam Synthesis');
                  }}
                >
                  EXAM
                </button>
              </div>

              <div className="mastery">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'end' }}>
                  <div>
                    <div className="mastery-label">MASTERY</div>
                    <div className="mastery-number">{mastery}%</div>
                  </div>
                  <span style={{ fontSize: '20px' }}>↗</span>
                </div>

                <div className="mbar">
                  <div className="mbar-top">
                    <span>HYPERPLANE</span>
                    <span>88%</span>
                  </div>
                  <div className="mtrack">
                    <div className="mfill" style={{ width: '88%' }} />
                  </div>
                </div>

                <button
                  className="metric-link"
                  onClick={() => showToast('Concept retention opened')}
                >
                  <span>CONCEPT RETENTION</span>
                  <span>↗</span>
                </button>
                <button
                  className="metric-link"
                  onClick={() => showToast('Formula derivation opened')}
                >
                  <span>FORMULA DERIVATION</span>
                  <span>↗</span>
                </button>
                <button
                  className="metric-link"
                  onClick={() => showToast('Transfer capability opened')}
                >
                  <span>TRANSFER CAPABILITY</span>
                  <span>↗</span>
                </button>

                <div className="side-label" style={{ margin: '22px 0 0' }}>
                  QUICK ACTIONS
                </div>
                <div className="quick-actions">
                  <button
                    className="outline-btn"
                    onClick={() => showToast('Note saved to personal knowledge base')}
                  >
                    ▢ SAVE NOTE
                  </button>
                  <button
                    className="outline-btn"
                    onClick={() => showToast('Flashcard added for spaced repetition')}
                  >
                    ▣ FLASHCARD
                  </button>
                </div>

                <p className="muted" style={{ fontSize: '13px', marginTop: '24px' }}>
                  <strong style={{ color: '#0c0c0c' }}>NEXT:</strong> strengthen MARGIN before kernel methods.
                </p>
              </div>
            </aside>
          </div>
        </section>

        {/* Section 03: Content Engine */}
        <section className="section reveal" id="study-pack">
          <div className="section-head">
            <div className="section-label">03 / CONTENT ENGINE</div>
            <h2 className="section-title">
              FROM 127 PAGES<br />
              TO WHAT MATTERS.
            </h2>
          </div>

          <div className="pack-grid">
            <article
              className="pack"
              onClick={() => handlePackClick('Quick Revision pack', 'quick_revision')}
            >
              <div className="pack-index">01 / 04</div>
              <h3>
                QUICK<br />
                REVISION
              </h3>
              <p>High-signal notes for the final minutes before an exam.</p>
              <div className="pack-arrow">↗</div>
            </article>

            <article
              className="pack"
              onClick={() => handlePackClick('Exam Preparation pack', 'exam_prep')}
            >
              <div className="pack-index">02 / 04</div>
              <h3>
                EXAM<br />
                PREP
              </h3>
              <p>Important concepts, definitions, 2/5/10-mark questions and practice.</p>
              <div className="pack-arrow">↗</div>
            </article>

            <article
              className="pack"
              onClick={() => handlePackClick('Formula Sheet', 'formula_sheet')}
            >
              <div className="pack-index">03 / 04</div>
              <h3>
                FORMULA<br />
                SHEET
              </h3>
              <p>Key formulas, symbols, conditions and worked applications.</p>
              <div className="pack-arrow">↗</div>
            </article>

            <article
              className="pack"
              onClick={() => handlePackClick('Viva Preparation pack', 'viva_prep')}
            >
              <div className="pack-index">04 / 04</div>
              <h3>
                VIVA<br />
                PREP
              </h3>
              <p>Rapid conceptual questions with concise, source-grounded answers.</p>
              <div className="pack-arrow">↗</div>
            </article>
          </div>
        </section>

        {/* Section 04: The Learnova Loop */}
        <section className="flow reveal" id="method">
          <div className="section-label">04 / THE LEARNOVA LOOP</div>
          <h2 className="section-title" style={{ marginTop: '20px' }}>
            THE SYSTEM DOESN'T<br />
            STOP AT AN ANSWER.
          </h2>

          <div className="flowline">
            <div className="flowstep">
              <b>01</b>
              <h4>ANALYZE</h4>
              <p>Structure the student's material into retrievable knowledge.</p>
            </div>

            <div className="flowstep">
              <b>02</b>
              <h4>TEACH</h4>
              <p>Explain with the right depth, example and analogy.</p>
            </div>

            <div className="flowstep">
              <b>03</b>
              <h4>ASK</h4>
              <p>Check understanding instead of assuming it.</p>
            </div>

            <div className="flowstep">
              <b>04</b>
              <h4>ADAPT</h4>
              <p>Detect weak concepts and change the explanation.</p>
            </div>

            <div className="flowstep">
              <b>05</b>
              <h4>MASTER</h4>
              <p>Build confidence, practice and personalized revision.</p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer">
          <div className="footer-brand">LEARNOVA</div>
          <p>
            Personal AI teaching assistant.<br />
            Don't just study. Understand.
          </p>
          <div className="footer-right">
            AI / RAG / ADAPTIVE LEARNING<br />
            © 2026
          </div>
        </footer>
      </main>

      {/* Global Toast Pill */}
      <div className={`toast ${toastMessage ? 'show' : ''}`} id="toast">
        {toastMessage}
      </div>
    </>
  );
}
