'use client';

import React from 'react';
import Link from 'next/link';
import { Badge } from '@/components/ui/Badge';
import { PillButton } from '@/components/ui/PillButton';
import { DocumentItem } from '@/lib/types';
import { BookOpen, FileSpreadsheet, Trash2, ArrowUpRight } from 'lucide-react';

interface DocumentCardProps {
  document: DocumentItem;
  onDelete?: (id: string) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({ document, onDelete }) => {
  const getFileExtension = (filename: string) => {
    const ext = filename.split('.').pop()?.toUpperCase() || 'DOC';
    return ext;
  };

  return (
    <div className="border border-[#cecece] bg-[#ffffff] p-8 flex flex-col justify-between hover:border-[#0c0c0c] transition-all group">
      <div>
        {/* Header badges */}
        <div className="flex items-center justify-between pb-4 border-b border-[#cecece] mb-6">
          <div className="flex items-center gap-2">
            <Badge variant="dark" size="sm">
              {getFileExtension(document.filename)}
            </Badge>
            <Badge
              variant={document.status === 'READY' ? 'success' : 'default'}
              size="sm"
            >
              {document.status}
            </Badge>
          </div>
          <span className="text-[11px] font-mono tracking-wider text-[#6d6d6d] uppercase">
            REF // {document.id.slice(-6).toUpperCase()}
          </span>
        </div>

        {/* Title */}
        <h3 className="text-[19px] font-bold text-[#0c0c0c] font-tech leading-snug tracking-tight mb-2 group-hover:text-[#6d6d6d] transition-colors">
          <Link href={`/documents/${document.id}`}>
            {document.title}
          </Link>
        </h3>

        {/* Metadata subline */}
        <p className="text-[12px] font-mono text-[#6d6d6d] mb-4 truncate">
          {document.filename}
        </p>

        {/* Technical specs inline rail */}
        <div className="grid grid-cols-3 gap-2 py-3 border-y border-[#cecece] my-4 text-center">
          <div>
            <div className="text-[10px] uppercase font-tech text-[#6d6d6d]">PAGES</div>
            <div className="text-[16px] font-bold font-tech text-[#0c0c0c]">
              {document.total_pages || 1}
            </div>
          </div>
          <div className="border-x border-[#cecece]">
            <div className="text-[10px] uppercase font-tech text-[#6d6d6d]">CHUNKS</div>
            <div className="text-[16px] font-bold font-tech text-[#0c0c0c]">
              {document.total_chunks || 0}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-tech text-[#6d6d6d]">TOPICS</div>
            <div className="text-[16px] font-bold font-tech text-[#0c0c0c]">
              {document.topics?.length || document.topic_count || 3}
            </div>
          </div>
        </div>

        {/* Summary text */}
        {document.summary && (
          <p className="text-[13px] text-[#6d6d6d] leading-relaxed mb-6 line-clamp-3">
            {document.summary}
          </p>
        )}

        {/* Extracted Topics Pill list */}
        {document.topics && document.topics.length > 0 && (
          <div className="mb-6 space-y-1.5">
            <span className="text-[10px] font-tech uppercase tracking-widest text-[#6d6d6d]">
              IDENTIFIED CONCEPTS:
            </span>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {document.topics.slice(0, 3).map((topic) => (
                <span
                  key={topic.id}
                  className="text-[11px] font-tech px-2 py-0.5 bg-[#f5f5f5] text-[#0c0c0c] border border-[#cecece]"
                >
                  {topic.name}
                </span>
              ))}
              {document.topics.length > 3 && (
                <span className="text-[11px] font-tech px-2 py-0.5 bg-[#ffffff] text-[#6d6d6d] border border-[#cecece]">
                  +{document.topics.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-[#cecece] flex items-center justify-between gap-2 mt-4">
        <Link href={`/documents/${document.id}`} className="flex-1">
          <PillButton
            variant="primary"
            size="sm"
            className="w-full"
            icon={<BookOpen className="w-3.5 h-3.5" />}
          >
            ENTER WORKSPACE
          </PillButton>
        </Link>

        <Link href={`/documents/${document.id}?tab=packs`}>
          <button
            title="Generate Study Pack"
            className="p-2 border border-[#cecece] hover:border-[#0c0c0c] hover:bg-[#fafafa] transition-colors text-[#0c0c0c]"
          >
            <FileSpreadsheet className="w-4 h-4" />
          </button>
        </Link>

        {onDelete && (
          <button
            title="Delete Document"
            onClick={() => onDelete(document.id)}
            className="p-2 border border-[#cecece] hover:border-red-600 hover:text-red-600 hover:bg-[#fce8e6] transition-colors text-[#6d6d6d]"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
