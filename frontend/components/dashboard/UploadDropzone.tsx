'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { PillButton } from '@/components/ui/PillButton';
import { UnderlineInput } from '@/components/ui/UnderlineInput';
import { DocumentItem } from '@/lib/types';
import { learnovaApi } from '@/lib/api';

interface UploadDropzoneProps {
  onDocumentUploaded: (doc: DocumentItem) => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onDocumentUploaded }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['.pdf', '.docx', '.txt', '.pptx', '.md'];

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    setSuccessMessage(null);
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      setErrorMessage(`Unsupported file format. Supported: ${allowedExtensions.join(', ')}`);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage('File size exceeds 50 MB limit.');
      return;
    }

    setSelectedFile(file);
    if (!title) {
      const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ');
      setTitle(cleanName);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setErrorMessage(null);
      setUploadProgress(30);

      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => (prev < 90 ? prev + 15 : prev));
      }, 200);

      const uploadedDoc = await learnovaApi.uploadDocument(selectedFile, title.trim());

      clearInterval(progressInterval);
      setUploadProgress(100);
      setSuccessMessage(`Ingestion verified: "${uploadedDoc.title}" is ready for tutoring.`);
      onDocumentUploaded(uploadedDoc);

      // Reset form after short delay
      setTimeout(() => {
        setSelectedFile(null);
        setTitle('');
        setUploading(false);
        setUploadProgress(0);
      }, 1500);
    } catch (err: unknown) {
      const error = err instanceof Error ? err : new Error(String(err));
      setErrorMessage(error.message || 'Upload failed. Please check network connection.');
      setUploading(false);
    }
  };

  return (
    <div
      id="upload-zone"
      className="border border-[#cecece] bg-[#ffffff] p-8 md:p-10 transition-all scroll-mt-28"
    >
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 mb-6 border-b border-[#cecece] gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono tracking-widest uppercase text-[#6d6d6d]">
              INGESTION MODULE // PROTOCOL 01
            </span>
          </div>
          <h2 className="text-[22px] font-bold tracking-tight text-[#0c0c0c] font-tech uppercase mt-1">
            INGEST EDUCATIONAL RESOURCE
          </h2>
        </div>
        <div className="text-[12px] text-[#6d6d6d] font-tech uppercase tracking-wider">
          MAX 50MB // PDF, DOCX, TXT, PPTX
        </div>
      </div>

      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed p-8 md:p-12 text-center transition-all cursor-pointer ${
          dragActive
            ? 'border-[#0c0c0c] bg-[#fafafa]'
            : selectedFile
            ? 'border-[#0c0c0c] bg-[#ffffff] cursor-default'
            : 'border-[#cecece] hover:border-[#6d6d6d] bg-[#fafafa]'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt,.pptx,.md"
          onChange={handleChange}
        />

        {!selectedFile ? (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-14 h-14 rounded-full border border-[#cecece] bg-[#ffffff] flex items-center justify-center text-[#0c0c0c]">
              <Upload className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-[15px] font-medium text-[#0c0c0c]">
                Drag and drop your syllabus, textbook, or lecture notes here
              </p>
              <p className="text-[13px] text-[#6d6d6d]">
                or <span className="underline cursor-pointer text-[#0c0c0c]">browse files from local storage</span>
              </p>
            </div>
          </div>
        ) : (
          <div className="w-full text-left space-y-6">
            <div className="flex items-center justify-between border-b border-[#cecece] pb-4">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 border border-[#0c0c0c] bg-[#0c0c0c] text-[#ffffff] flex items-center justify-center rounded-none">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-tech text-[15px] font-bold text-[#0c0c0c]">
                    {selectedFile.name}
                  </p>
                  <p className="text-[12px] text-[#6d6d6d] font-mono">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type || 'DOCUMENT'}
                  </p>
                </div>
              </div>

              {!uploading && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                    setTitle('');
                  }}
                  className="text-[12px] font-tech uppercase text-[#6d6d6d] hover:text-[#0c0c0c] underline"
                >
                  DISCARD FILE
                </button>
              )}
            </div>

            <div className="space-y-4" onClick={(e) => e.stopPropagation()}>
              <UnderlineInput
                label="DOCUMENT DOSSIER TITLE (OPTIONAL)"
                placeholder="e.g. Modern Physics Chapter 4 - Atomic Spectra"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={uploading}
              />
            </div>

            {uploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[12px] font-tech text-[#6d6d6d]">
                  <span>INGESTING & VECTORIZING CHUNKS...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full h-1 bg-[#eaeaea] overflow-hidden">
                  <div
                    className="h-full bg-[#0c0c0c] transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center justify-end gap-4 pt-2">
              <PillButton
                variant="primary"
                size="md"
                disabled={uploading}
                onClick={(e) => {
                  e.stopPropagation();
                  handleUploadSubmit();
                }}
                icon={uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
              >
                {uploading ? 'INGESTING RESOURCE...' : 'START DEEP ANALYSIS'}
              </PillButton>
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="mt-4 p-4 border border-[#f5b4af] bg-[#fce8e6] text-[#c5221f] text-[13px] flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="mt-4 p-4 border border-[#b7e1cd] bg-[#eaf7ee] text-[#137333] text-[13px] flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}
    </div>
  );
};
