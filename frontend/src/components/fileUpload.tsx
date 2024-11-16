'use client';

import { useState, useRef } from 'react';
import { Upload, X, FileText, Loader2, AlertCircle } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { useRouter } from 'next/navigation';

interface FileUploadProps {
  onUploadComplete: () => void;
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.name.endsWith('.docx')
    );
    
    if (droppedFiles.length > 0) {
      setFiles(prev => [...prev, ...droppedFiles]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };

  const removeFile = (fileToRemove: File) => {
    setFiles(files.filter(file => file !== fileToRemove));
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (files.length > 0) {
      setIsProcessing(true);
      setError(null);
      try {
        const formData = new FormData();
        files.forEach(file => {
          formData.append('files', file);
        });

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Uppladdningen misslyckades. Vänligen försök igen.');
        }

        const data = await response.json();
        
        if (data.session_id) {
          localStorage.setItem('chatSessionId', data.session_id);
        }

        onUploadComplete();
        router.push('/chat');
      } catch (error) {
        console.error('Upload error:', error);
        setError('Något gick fel vid uppladdningen. Vänligen försök igen.');
      } finally {
        setIsProcessing(false);
      }
    }
  };

  return (
    <div className="flex flex-col relative">
      {/* Error Message Overlay */}
      {error && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center space-y-4 max-w-md mx-4">
            <AlertCircle className="h-8 w-8 text-red-600" />
            <p className="text-gray-800 font-medium text-center">{error}</p>
            <Button 
              onClick={() => setError(null)}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              Stäng
            </Button>
          </div>
        </div>
      )}

      {/* Processing Overlay */}
      {isProcessing && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
            <p className="text-gray-800 font-medium">{processingProgress || 'Bearbetar filer...'}</p>
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col items-center p-4 overflow-y-auto mt-16">
        <div className="max-w-4xl w-full space-y-8 pt-8">
          {/* Hero Section */}
          <div className="text-center p-8">
            <div className="inline-block text-indigo-600 mb-2 px-6 py-2 rounded-full bg-indigo-50 text-sm font-medium shadow-sm">
              Få ut mer av dina mötesanteckningar – på ditt sätt
            </div>
            <h2 className="text-5xl font-bold mb-4 leading-tight">
              Dina protokoll <span className="hero-gradient">stärkta med AI</span>
            </h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto mb-6">
              Spara timmar av arbete genom att chatta med dina protokoll! Låt vår AI analysera dina mötesprotokoll och få 
              direkt tillgång till viktiga beslut och åtgärdspunkter genom en enkel konversation. 
            </p>
          </div>

          <div className="space-y-4">
            {/* Upload area */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`card-gradient border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all shadow-lg
                ${isDragging ? 'border-indigo-500 bg-indigo-50/50' : 'border-indigo-200'}
                hover:border-indigo-500 hover:shadow-xl`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx"
                onChange={handleFileSelect}
                className="hidden"
                multiple
              />
              <Upload className="mx-auto h-12 w-12 text-indigo-500" />
              <p className="mt-2 text-sm text-gray-600">
                Dra och släpp dina .docx filer här eller
              </p>
              <Button 
                variant="outline" 
                className="mt-2 border-indigo-200 hover:border-indigo-500 hover:bg-indigo-50" 
                onClick={handleButtonClick}
              >
                Välj filer
              </Button>
            </div>

            {/* Compact File List and Upload Button */}
            {files.length > 0 && (
              <div className="flex flex-col items-center space-y-4">
                {/* File Icons */}
                <div className="flex flex-wrap gap-2 justify-center">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="relative group"
                    >
                      <div className="card-gradient p-3 rounded-lg shadow-sm flex items-center space-x-2 hover:shadow-md transition-all">
                        <FileText className="h-5 w-5 text-indigo-500" />
                        <span className="text-xs text-gray-600 max-w-[100px] truncate">
                          {file.name}
                        </span>
                        <button
                          onClick={() => removeFile(file)}
                          className="opacity-0 group-hover:opacity-100 absolute -top-2 -right-2 bg-white rounded-full p-1 shadow-md hover:bg-red-50 transition-all"
                          disabled={isProcessing}
                        >
                          <X className="h-3 w-3 text-gray-400 hover:text-red-500" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Upload Button */}
                <Button
                  className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg transition-all px-8"
                  onClick={handleUpload}
                  disabled={isProcessing}
                >
                  Ladda upp
                </Button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
} 