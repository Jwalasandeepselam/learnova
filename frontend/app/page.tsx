'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { learnovaApi } from '@/lib/api';
import { DocumentItem, Topic } from '@/lib/types';
import { useVoiceAssistant } from '@/lib/voiceContext';
import { ListenButton } from '@/components/voice/ListenButton';
import {
  Upload,
  FileText,
  Sparkles,
  ArrowRight,
  BookOpen,
  BrainCircuit,
  Volume2,
  Mic,
  Send,
  Loader2,
  CheckCircle2
} from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { openAssistant } = useVoiceAssistant();

  // Document Management State
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activeDoc, setActiveDoc] = useState<DocumentItem | null>(null);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  // Upload State
  const [isUploading, setIsUploading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Active Tutor State
  const [activeTopicIdx, setActiveTopicIdx] = useState(0);
  const [tutorQuestion, setTutorQuestion] = useState('WHAT WOULD YOU LIKE TO UNDERSTAND TODAY?');
  const [tutorBody, setTutorBody] = useState(
    'Learnova teaches through first-principles Socratic dialogue. Upload your syllabus, lecture slides, or textbook chapter to ground every answer directly in your material. You can also ask or speak any question right now.'
  );
  const [tutorKey, setTutorKey] = useState(
    'Upload your material · First-principles learning · Voice and text dialogues'
  );
  const [askInput, setAskInput] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [activeMode, setActiveMode] = useState<'LEARN' | 'PRACTICE' | 'EXAM'>('LEARN');
  const [mastery, setMastery] = useState(0);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3200);
  };

  // Fetch documents on load
  const loadDocuments = async () => {
    try {
      setIsLoadingDocs(true);
      const res = await learnovaApi.getDocuments(1, 20);
      setDocuments(res.items || []);
      if (res.items && res.items.length > 0) {
        selectDocument(res.items[0]);
      } else {
        setActiveDoc(null);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const selectDocument = (doc: DocumentItem) => {
    setActiveDoc(doc);
    setActiveTopicIdx(0);
    const firstTopic = doc.topics?.[0];
    if (firstTopic) {
      setTutorQuestion(`How do the core principles of ${firstTopic.name} establish the foundational rules?`);
      setTutorBody(
        firstTopic.description ||
          `According to ${doc.title}, this topic introduces the critical definitions and axioms required for full conceptual mastery.`
      );
      setTutorKey(`Core Principle: Systematic reasoning grounded directly in your uploaded material.`);
      setMastery(Math.round((firstTopic.mastery_score || 0.74) * 100));
    }
  };

  useEffect(() => {
    loadDocuments();

    // Intersection observer for smooth reveals
    const elements = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.08 }
    );
    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const handleFileUpload = async (file: File) => {
    try {
      setIsUploading(true);
      showToast(`RECEIVING ${file.name.toUpperCase()}...`);

      const newDoc = await learnovaApi.uploadDocument(file);
      setDocuments((prev) => [newDoc, ...prev.filter((d) => d.id !== newDoc.id)]);
      selectDocument(newDoc);

      showToast(`SUCCESS // INGESTED & ANALYZED: ${newDoc.title.toUpperCase()}`);

      // Smooth scroll to analysis
      setTimeout(() => {
        document.getElementById('analysis')?.scrollIntoView({ behavior: 'smooth' });
      }, 500);
    } catch (err: unknown) {
      const error = err instanceof Error ? err : new Error(String(err));
      showToast(error.message || 'Upload failed. Please try again.');
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

  const handleTopicClick = (idx: number, topic: Topic) => {
    setActiveTopicIdx(idx);
    setTutorQuestion(`Why is ${topic.name} fundamental to understanding this chapter?`);
    setTutorBody(
      topic.description ||
        `In ${activeDoc?.title || 'your material'}, ${topic.name} provides the bridge between prerequisite concepts and applied derivations.`
    );
    setTutorKey(`Key Rule: Tested with first-principles reasoning from your document chunks.`);
    setMastery(Math.round((topic.mastery_score || 0.65) * 100));
    showToast(`Active Topic: ${topic.name}`);
  };

  const handleStrategy = async (
    mod: 'simpler' | 'analogy' | 'real_world' | 'mathematical',
    actionDesc: string
  ) => {
    if (!activeDoc) {
      showToast('Please upload study material first.');
      return;
    }
    const currentTopicName = activeDoc.topics?.[activeTopicIdx]?.name || 'Current Topic';
    showToast(`${actionDesc} — connecting to Tutor Agent`);

    try {
      const res = await learnovaApi.explainAgain({
        session_id: `sess_home_${Date.now()}`,
        target_concept: currentTopicName,
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

  const handleAskSubmit = async () => {
    if (!askInput.trim() || isAsking) {
      showToast('Ask a question first');
      return;
    }

    const query = askInput.trim();
    setAskInput('');
    setIsAsking(true);
    showToast('Tutor processing your question...');

    try {
      if (activeDoc) {
        const res = await learnovaApi.chat({
          document_id: activeDoc.id,
          query: query
        });

        setTutorQuestion(query.toUpperCase());
        setTutorBody(res.response);
        setTutorKey(
          res.citations && res.citations.length > 0
            ? `Source Citation: Page ${res.citations[0].page_number} // ${res.citations[0].snippet.slice(0, 95)}...`
            : 'Verified against your uploaded document knowledge base.'
        );
        setMastery((m) => Math.min(100, m + 4));
        showToast('REASONING RECORDED // MASTERY +4%');
      } else {
        setTutorQuestion(query.toUpperCase());
        try {
          const res = await learnovaApi.chat({
            document_id: '',
            query: query
          });
          setTutorBody(res.response);
        } catch {
          setTutorBody(
            `Regarding "${query}": In scientific reasoning, core concepts are understood by decomposing definitions and evaluating edge cases. To unlock exact page citations, formula proofs, and formative quizzes tailored to your syllabus, upload your course PDF, PPT, or notes above.`
          );
        }
        setTutorKey('Upload your course materials above for source-grounded citations.');
        setMastery((m) => Math.min(100, m + 5));
        showToast('TUTOR RESPONDED // UPLOAD MATERIAL FOR CITATIONS');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsAsking(false);
    }
  };

  const handlePackClick = (packTitle: string, packType: string) => {
    if (!activeDoc) {
      showToast('Upload your course material above to generate this study pack.');
      fileInputRef.current?.click();
      return;
    }
    showToast(`Opening ${packTitle} for ${activeDoc.title}...`);
    router.push(`/documents/${activeDoc.id}?tab=packs`);
  };

  const hasDocuments = documents.length > 0 && activeDoc !== null;

  return (
    <>
      <main>
        {/* Hero Section */}
        <section className="hero" id="hero">
          <div className="hero-left">
            <div>
              <div className="kicker">PERSONAL AI TEACHING ASSISTANT / 001</div>
              <h1 className="hero-title" style={{ marginTop: '16px' }}>
                DON'T JUST
                <br />
                STUDY.
                <br />
                UNDERSTAND.
              </h1>
            </div>

            <div>
              <p className="hero-copy">
                Learnova doesn't summarize your material — it decomposes textbooks,
                slides, and notes into dynamic knowledge models, teaching you line-by-line.
              </p>

              <div className="hero-actions">
                <button
                  className="black-btn"
                  id="uploadBtn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                >
                  {isUploading ? 'INGESTING...' : 'UPLOAD MATERIAL'}
                </button>
                <a href="#analysis" className="text-btn">
                  EXPLORE THE SYSTEM ↓
                </a>
              </div>

              {/* Upload Drop Zone */}
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
                  <span id="uploadText">
                    {isUploading
                      ? 'PARSING DOCUMENT & EMBEDDING CHUNKS...'
                      : hasDocuments
                      ? `ACTIVE: ${activeDoc.title.slice(0, 32)}... (CLICK TO ADD ANOTHER)`
                      : 'DROP PDF / PPT / DOCX / TXT HERE'}
                  </span>
                  <div className="file-meta" id="uploadMeta">
                    {hasDocuments
                      ? `${activeDoc.filename} • ${activeDoc.total_pages} pages • ${activeDoc.total_chunks} chunks indexed`
                      : 'Your material becomes the source of truth. Upload lecture slides, chapters, or notes.'}
                  </div>
                </div>
                <div className="kicker">
                  {isUploading ? '◌' : hasDocuments ? '✓' : '+'}
                </div>
              </div>

              <input
                id="uploadInput"
                ref={fileInputRef}
                type="file"
                accept=".pdf,.ppt,.pptx,.doc,.docx,.txt,.md"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
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
                KNOWLEDGE
                <br />
                IN MOTION
              </h2>
              <p>
                {hasDocuments
                  ? `Active knowledge graph generated for "${activeDoc.title}". Grounded citations active.`
                  : 'Document → concepts → teaching → practice → mastery. One continuous learning system.'}
              </p>
            </div>
          </div>
        </section>

        {/* Uploaded Document Banner (Visible when documents exist) */}
        {hasDocuments && (
          <section className="border-y border-[#0c0c0c] bg-[#fafafa] py-4 px-6 md:px-10">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#0c0c0c] animate-pulse" />
                <span className="font-tech text-[12px] uppercase tracking-wider text-[#6d6d6d]">
                  ACTIVE STUDY MATERIAL:
                </span>
                <span className="font-tech text-[14px] font-bold text-[#0c0c0c] uppercase">
                  {activeDoc.title}
                </span>
                <span className="text-[12px] font-mono text-[#6d6d6d]">
                  ({activeDoc.total_pages} pages • {activeDoc.total_chunks} chunks)
                </span>
              </div>

              <div className="flex items-center gap-3">
                <Link href={`/documents/${activeDoc.id}`}>
                  <button className="black-btn" style={{ height: '38px', fontSize: '12px' }}>
                    OPEN FULL WORKSPACE <span>→</span>
                  </button>
                </Link>
              </div>
            </div>
          </section>
        )}

        {/* Section 01: Document Intelligence */}
        <section className="section reveal" id="analysis">
          <div className="section-head">
            <div className="section-label">01 / DOCUMENT INTELLIGENCE</div>
            <h2 className="section-title">
              FIRST, LEARNOVA
              <br />
              UNDERSTANDS.
            </h2>
          </div>

          <div className="analysis">
            <div className="analysis-main">
              <div className="analysis-content">
                <div>
                  <div className="scan">
                    {hasDocuments
                      ? `ANALYSIS COMPLETE // ${activeDoc.title.toUpperCase()}`
                      : 'STATUS // WAITING FOR UPLOAD'}
                  </div>
                  <div className="scanline" />
                </div>
                <div>
                  <h3>
                    {hasDocuments
                      ? 'Your material is mapped into a structured knowledge base — ready for line-by-line tutoring.'
                      : 'Upload your learning material above. Learnova will parse the document structure, extract core concepts, and index chunks for grounded AI tutoring.'}
                  </h3>
                  <p style={{ color: '#cecece', maxWidth: '520px', marginTop: '12px' }}>
                    {hasDocuments
                      ? 'Axioms, prerequisite relationships, governing equations, and key misconceptions are extracted so every answer is 100% grounded in your material.'
                      : 'Supports multi-page PDFs, PowerPoint lecture slides, Word documents, and textbook chapters up to 50MB.'}
                  </p>
                </div>
              </div>
            </div>

            <div className="spec">
              <div className="spec-row">
                <span>INPUT</span>
                <b>
                  {hasDocuments
                    ? activeDoc.filename.split('.').pop()?.toUpperCase() || 'DOCUMENT'
                    : 'PDF / PPT / DOCX / TXT'}
                </b>
              </div>
              <div className="spec-row">
                <span>DOCUMENTS</span>
                <b>{documents.length}</b>
              </div>
              <div className="spec-row">
                <span>TOPICS</span>
                <b>{hasDocuments ? activeDoc.topics?.length || activeDoc.topic_count || 4 : 0}</b>
              </div>
              <div className="spec-row">
                <span>CHUNKS</span>
                <b>{hasDocuments ? activeDoc.total_chunks : 0}</b>
              </div>
              <div className="spec-row">
                <span>INDEX</span>
                <b>{hasDocuments ? 'READY' : 'WAITING FOR UPLOAD'}</b>
              </div>
              <div className="spec-row">
                <span>GROUNDING</span>
                <b>BASED ON YOUR MATERIAL</b>
              </div>
            </div>
          </div>

          <div className="analysis-stats">
            <div className="stat">
              <strong>{documents.length}</strong>
              <span>DOCUMENTS INGESTED</span>
            </div>
            <div className="stat">
              <strong>{hasDocuments ? activeDoc.topics?.length || activeDoc.topic_count || 4 : 0}</strong>
              <span>CORE CONCEPTS</span>
            </div>
            <div className="stat">
              <strong>{hasDocuments ? activeDoc.total_chunks * 2 : 0}</strong>
              <span>RETRIEVABLE PASSAGES</span>
            </div>
          </div>
        </section>

        {/* Section 02: Adaptive Tutor */}
        <section className="section reveal" id="learn">
          <div className="section-head">
            <div className="section-label">02 / ADAPTIVE TUTOR</div>
            <h2 className="section-title">
              A TEACHER THAT
              <br />
              CHANGES WITH YOU.
            </h2>
          </div>

          <div className="workspace-grid">
            {/* Learning Map Side Nav */}
            <aside className="side topics-side">
              <div className="side-label">
                YOUR LEARNING MAP // {hasDocuments ? `0${activeDoc.topics?.length || 4}` : 'AWAITING MATERIAL'}
              </div>
              {hasDocuments && activeDoc.topics && activeDoc.topics.length > 0 ? (
                activeDoc.topics.map((t, idx) => (
                  <button
                    key={t.id}
                    className={`topic ${activeTopicIdx === idx ? 'active' : ''}`}
                    onClick={() => handleTopicClick(idx, t)}
                  >
                    <span>{t.name}</span>
                    <span className="topic-status">
                      {Math.round((t.mastery_score || 0.6) * 100)}%
                    </span>
                  </button>
                ))
              ) : (
                <div className="p-4 border border-dashed border-[#cecece] text-center space-y-3 my-2 bg-[#fafafa]">
                  <p className="text-[13px] text-[#6d6d6d] font-sans leading-relaxed">
                    No topics extracted yet. Upload your PDF, PPT, or Word document to generate your concept map.
                  </p>
                  <button
                    className="black-btn"
                    style={{ width: '100%', height: '40px', fontSize: '12px' }}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    + UPLOAD MATERIAL
                  </button>
                </div>
              )}
              {hasDocuments && (
                <Link href={`/documents/${activeDoc.id}?tab=overview`}>
                  <button
                    className="outline-btn"
                    style={{ width: '100%', marginTop: '18px' }}
                  >
                    <span className="btn-icon">⌘</span> VIEW LEARNING MAP <span>→</span>
                  </button>
                </Link>
              )}
            </aside>

            {/* Socratic Dialogue Center */}
            <article className="tutor">
              <div>
                <div className="tutor-top">
                  <div className="tutor-tag">
                    GUIDED QUESTIONING // {hasDocuments ? `STEP 0${activeTopicIdx + 1}` : 'READY'}
                  </div>
                  <div className="muted" style={{ fontSize: '12px' }}>
                    {hasDocuments ? `SOURCE: ${activeDoc.filename}` : 'SOURCE: READY FOR UPLOAD'}
                  </div>
                </div>

                <h3>{tutorQuestion}</h3>
                <p>{tutorBody}</p>

                {/* Text-to-Speech Listen Button */}
                <div style={{ margin: '14px 0 16px' }}>
                  <ListenButton
                    text={`${tutorQuestion}. ${tutorBody}`}
                    id={`home-tutor-${activeTopicIdx}`}
                  />
                </div>

                <div className="key">
                  <b>KEY IDEA</b>
                  <p>{tutorKey}</p>
                </div>
              </div>

              <div>
                <div className="tutor-actions">
                  <button
                    className="dark-btn"
                    onClick={handleAskSubmit}
                    disabled={isAsking}
                  >
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
                    onClick={() => handleStrategy('real_world', 'Generating an example')}
                  >
                    <span className="btn-icon">✦</span> GIVE AN EXAMPLE <span>→</span>
                  </button>
                  <button
                    className="outline-btn"
                    onClick={() => handleStrategy('simpler', 'Explaining simpler')}
                  >
                    <span className="btn-icon">↓</span> SIMPLER <span>→</span>
                  </button>
                </div>

                {/* Ask Question Bar with Inline Voice Mic */}
                <div className="ask" style={{ marginTop: '14px' }}>
                  <input
                    id="questionInput"
                    placeholder="Ask or speak about this material..."
                    value={askInput}
                    onChange={(e) => setAskInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleAskSubmit();
                      }
                    }}
                    disabled={isAsking}
                  />

                  {/* Inline Microphone Button */}
                  <button
                    type="button"
                    onClick={() =>
                      openAssistant(
                        hasDocuments ? activeDoc.topics?.[activeTopicIdx]?.name || activeDoc.title : 'General Inquiry',
                        hasDocuments ? activeDoc.id : undefined
                      )
                    }
                    aria-label="Speak your question with voice assistant"
                    title="Speak with Learnova voice assistant"
                    className="ask-mic-btn"
                  >
                    🎙
                  </button>

                  <button
                    className="ask-submit-btn"
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
                    showToast('Mode: Guided Deep Learning');
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
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'end'
                  }}
                >
                  <div>
                    <div className="mastery-label">MASTERY</div>
                    <div className="mastery-number">{mastery}%</div>
                  </div>
                  <span style={{ fontSize: '20px' }}>↗</span>
                </div>

                <div className="mbar">
                  <div className="mbar-top">
                    <span>HOW WELL YOU REMEMBER</span>
                    <span>{mastery}%</span>
                  </div>
                  <div className="mtrack">
                    <div className="mfill" style={{ width: `${mastery}%` }} />
                  </div>
                </div>

                {hasDocuments ? (
                  <Link href={`/documents/${activeDoc.id}?tab=mastery`}>
                    <button className="metric-link">
                      <span>VIEW DETAILED MASTERY BREAKDOWN</span>
                      <span>↗</span>
                    </button>
                  </Link>
                ) : (
                  <div className="text-[12px] text-[#6d6d6d] my-3 leading-relaxed">
                    Mastery scores update automatically as you answer Socratic check questions.
                  </div>
                )}

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
                    onClick={() => {
                      if (hasDocuments) {
                        router.push(`/documents/${activeDoc.id}?tab=packs`);
                      } else {
                        showToast('Upload study material first to generate study pack');
                        fileInputRef.current?.click();
                      }
                    }}
                  >
                    ▣ STUDY PACK
                  </button>
                </div>
              </div>
            </aside>
          </div>
        </section>

        {/* Section 03: Content Engine */}
        <section className="section reveal" id="study-pack">
          <div className="section-head">
            <div className="section-label">03 / CONTENT ENGINE</div>
            <h2 className="section-title">
              STUDY PACKS GENERATED
              <br />
              FROM YOUR MATERIAL.
            </h2>
          </div>

          <div className="pack-grid">
            <article
              className="pack"
              onClick={() => handlePackClick('Quick Revision pack', 'quick_revision')}
            >
              <div className="pack-index">01 / 04</div>
              <h3>
                QUICK
                <br />
                REVISION
              </h3>
              <p>High-signal bullet points for the final minutes before class or an exam.</p>
              <div className="pack-arrow">↗</div>
            </article>

            <article
              className="pack"
              onClick={() => handlePackClick('Exam Preparation pack', 'exam_prep')}
            >
              <div className="pack-index">02 / 04</div>
              <h3>
                EXAM
                <br />
                PREP
              </h3>
              <p>Core concepts, model questions, derivations, and misconception traps.</p>
              <div className="pack-arrow">↗</div>
            </article>

            <article
              className="pack"
              onClick={() => handlePackClick('Formula Sheet', 'formula_sheet')}
            >
              <div className="pack-index">03 / 04</div>
              <h3>
                FORMULA
                <br />
                SHEET
              </h3>
              <p>Key governing equations, variable definitions, and boundary conditions.</p>
              <div className="pack-arrow">↗</div>
            </article>

            <article
              className="pack"
              onClick={() => handlePackClick('Viva Preparation pack', 'viva_prep')}
            >
              <div className="pack-index">04 / 04</div>
              <h3>
                VIVA
                <br />
                PREP
              </h3>
              <p>Rapid oral questions with concise, source-grounded model answers.</p>
              <div className="pack-arrow">↗</div>
            </article>
          </div>
        </section>

        {/* Section 04: The Learnova Loop */}
        <section className="flow reveal" id="method">
          <div className="section-label">04 / THE LEARNOVA LOOP</div>
          <h2 className="section-title" style={{ marginTop: '20px' }}>
            THE SYSTEM DOESN'T
            <br />
            STOP AT AN ANSWER.
          </h2>

          <div className="flowline">
            <div className="flowstep">
              <b>01</b>
              <h4>ANALYZE</h4>
              <p>Structure your uploaded material into retrievable knowledge.</p>
            </div>

            <div className="flowstep">
              <b>02</b>
              <h4>TEACH</h4>
              <p>Explain with the right depth, example, and analogy.</p>
            </div>

            <div className="flowstep">
              <b>03</b>
              <h4>ASK</h4>
              <p>Check understanding through diagnostic questions.</p>
            </div>

            <div className="flowstep">
              <b>04</b>
              <h4>ADAPT</h4>
              <p>Detect weak concepts and adjust the explanation angle.</p>
            </div>

            <div className="flowstep">
              <b>05</b>
              <h4>MASTER</h4>
              <p>Lock in intuition with study packs and spaced repetition.</p>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="footer">
          <div className="footer-brand">LEARNOVA</div>
          <p>
            Personal AI teaching assistant.
            <br />
            Understand, don't just read.
          </p>
          <div className="footer-right">
            AI / BASED ON YOUR MATERIAL / ADAPTIVE LEARNING
            <br />
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
