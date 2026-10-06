'use client';

import React, { useState } from 'react';
import { DocumentItem, ChatMessage, Citation } from '@/lib/types';
import { learnovaApi } from '@/lib/api';
import { PillButton } from '@/components/ui/PillButton';
import { Badge } from '@/components/ui/Badge';
import { UnderlineInput } from '@/components/ui/UnderlineInput';
import {
  MessageSquare,
  Send,
  Loader2,
  FileText,
  ExternalLink,
  ShieldCheck,
  X,
  HelpCircle
} from 'lucide-react';

interface AskAiTabProps {
  document: DocumentItem;
}

export const AskAiTab: React.FC<AskAiTabProps> = ({ document }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg_initial',
      sender: 'assistant',
      content:
        'I am grounded exclusively in the contents of this document. Ask any conceptual, mathematical, or procedural question, and I will synthesize an answer citing exact pages and chunks.',
      citations: [
        {
          citation_id: 'cite_init_1',
          document_id: document.id,
          page_number: 1,
          chunk_id: 'chunk_01',
          snippet: `${document.title}: Complete document vectorized and indexed into dense embeddings.`,
          relevance_score: 1.0
        }
      ],
      timestamp: new Date().toLocaleTimeString(),
      grounded: true
    }
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const sampleQuestions = [
    'What is the physical meaning of the wavefunction probability density?',
    'How is the de Broglie wavelength derived from relativistic energy?',
    'What boundary conditions apply to the infinite square well?',
    'Explain the Heisenberg commutator relation [x, p] = iℏ.'
  ];

  const handleSend = async (queryText?: string) => {
    const query = (queryText || inputQuery).trim();
    if (!query || loading) return;

    const userMessage: ChatMessage = {
      id: `msg_user_${Date.now()}`,
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setLoading(true);

    try {
      const res = await learnovaApi.chat({
        document_id: document.id,
        query: query
      });

      const assistantMessage: ChatMessage = {
        id: res.message_id || `msg_asst_${Date.now()}`,
        sender: 'assistant',
        content: res.response,
        citations: res.citations || [],
        timestamp: new Date().toLocaleTimeString(),
        grounded: res.grounded
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage: ChatMessage = {
        id: `msg_err_${Date.now()}`,
        sender: 'assistant',
        content:
          'Error querying document index. Please ensure the document is ingested properly and backend vector service is online.',
        timestamp: new Date().toLocaleTimeString(),
        grounded: false
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Search Header */}
      <div className="border border-[#cecece] p-6 md:p-8 bg-[#ffffff]">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                HYBRID RAG // DENSE & LEXICAL RETRIEVAL
              </span>
            </div>
            <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
              GROUNDED DOCUMENT INQUIRY
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#137333]" />
            <span className="text-[12px] font-tech uppercase text-[#137333] font-bold">
              STRICT CITATION ENFORCEMENT ACTIVE
            </span>
          </div>
        </div>

        {/* Suggested Queries */}
        <div className="space-y-2">
          <span className="text-[11px] font-tech uppercase tracking-widest text-[#6d6d6d]">
            SUGGESTED GROUNDED INQUIRIES:
          </span>
          <div className="flex flex-wrap gap-2 pt-1">
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                disabled={loading}
                onClick={() => handleSend(q)}
                className="text-left px-3.5 py-1.5 border border-[#cecece] hover:border-[#0c0c0c] hover:bg-[#fafafa] bg-[#ffffff] text-[12px] font-tech text-[#0c0c0c] transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages Feed */}
      <div className="space-y-6 min-h-[350px]">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`border p-6 md:p-8 transition-all ${
              msg.sender === 'user'
                ? 'border-[#0c0c0c] bg-[#fafafa] ml-6 md:ml-20'
                : 'border-[#cecece] bg-[#ffffff]'
            }`}
          >
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#cecece]/60">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono tracking-widest uppercase text-[#6d6d6d]">
                  {msg.sender === 'user' ? 'STUDENT INQUIRY' : 'LEARNOVA GROUNDED ASSISTANT'}
                </span>
                {msg.grounded && (
                  <Badge variant="success" size="sm">
                    VERIFIED CITATIONS
                  </Badge>
                )}
              </div>
              <span className="text-[11px] font-mono text-[#6d6d6d]">
                {msg.timestamp}
              </span>
            </div>

            <p className="text-[15px] md:text-[16px] text-[#0c0c0c] leading-relaxed whitespace-pre-line font-sans">
              {msg.content}
            </p>

            {/* Source Citation Pills */}
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-6 pt-4 border-t border-[#cecece] space-y-2">
                <div className="flex items-center gap-1.5 text-[11px] font-tech uppercase tracking-wider text-[#6d6d6d]">
                  <FileText className="w-3.5 h-3.5 text-[#0c0c0c]" />
                  <span>GROUNDED CITATION SOURCES (CLICK TO VERIFY):</span>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  {msg.citations.map((cite, cIdx) => (
                    <button
                      key={cite.citation_id || cIdx}
                      onClick={() => setSelectedCitation(cite)}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#0c0c0c] bg-[#fafafa] hover:bg-[#0c0c0c] hover:text-[#ffffff] text-[12px] font-tech font-medium text-[#0c0c0c] transition-all group cursor-pointer"
                    >
                      <span>PAGE {cite.page_number}</span>
                      <span className="opacity-50">•</span>
                      <span className="text-[11px] opacity-75">CHUNK #{cite.chunk_id}</span>
                      <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-100" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="border border-[#cecece] p-6 bg-[#ffffff] flex items-center gap-3 text-[13px] font-tech text-[#6d6d6d]">
            <Loader2 className="w-4 h-4 animate-spin text-[#0c0c0c]" />
            <span>RETRIEVING MATCHING CHUNKS & CROSS-REFERENCING CITATIONS...</span>
          </div>
        )}
      </div>

      {/* Query Input Bar */}
      <div className="border border-[#0c0c0c] p-6 bg-[#ffffff]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-tech uppercase tracking-widest text-[#6d6d6d]">
            ASK AI QUESTION // GROUNDED SEARCH
          </span>
          <span className="text-[11px] font-tech text-[#6d6d6d]">
            ANSWERS CONFINED TO THIS DOCUMENT
          </span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch gap-4">
          <div className="flex-1">
            <UnderlineInput
              placeholder="e.g. How does the uncertainty principle constrain position and momentum variance?"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
            />
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <PillButton
              variant="primary"
              size="md"
              onClick={() => handleSend()}
              disabled={loading || !inputQuery.trim()}
              icon={loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            >
              QUERY RAG
            </PillButton>
          </div>
        </div>
      </div>

      {/* Verbatim Citation Modal / Slideover */}
      {selectedCitation && (
        <div className="fixed inset-0 z-50 bg-[#000000]/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="border border-[#0c0c0c] bg-[#ffffff] max-w-xl w-full p-8 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-[#cecece] pb-4">
              <div className="flex items-center gap-2">
                <Badge variant="dark" size="sm">
                  VERIFIED CITATION
                </Badge>
                <span className="text-[12px] font-tech uppercase text-[#6d6d6d]">
                  PAGE {selectedCitation.page_number} // CHUNK {selectedCitation.chunk_id}
                </span>
              </div>
              <button
                onClick={() => setSelectedCitation(null)}
                className="p-1 border border-transparent hover:border-[#0c0c0c] transition-colors"
              >
                <X className="w-5 h-5 text-[#0c0c0c]" />
              </button>
            </div>

            <div className="space-y-3">
              <span className="text-[11px] font-tech uppercase text-[#6d6d6d] tracking-widest block">
                VERBATIM DOCUMENT EXCERPT:
              </span>
              <div className="p-4 bg-[#fafafa] border border-[#cecece] text-[14px] text-[#0c0c0c] font-sans leading-relaxed italic">
                "{selectedCitation.snippet}"
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-[#cecece] text-[12px] font-tech text-[#6d6d6d]">
              <span>
                DOCUMENT: <strong className="text-[#0c0c0c]">{document.filename}</strong>
              </span>
              {selectedCitation.relevance_score && (
                <span>
                  RELEVANCE:{' '}
                  <strong className="text-[#0c0c0c]">
                    {(selectedCitation.relevance_score * 100).toFixed(0)}%
                  </strong>
                </span>
              )}
            </div>

            <div className="flex justify-end">
              <PillButton
                variant="primary"
                size="sm"
                onClick={() => setSelectedCitation(null)}
              >
                CLOSE INSPECTOR
              </PillButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
