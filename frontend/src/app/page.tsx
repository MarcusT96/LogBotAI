'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import FileUpload from '@/components/fileUpload';
import Header from '@/components/header';

export default function Home() {
  const router = useRouter();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleUploadComplete = () => {
    setIsProcessing(true);
    // Simulate processing time
    setTimeout(() => {
      setIsProcessing(false);
      router.push('/chat'); // Navigate to chat route
    }, 3000);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex-1 pt-16">
        <div className={`h-full transition-opacity duration-500 ${isProcessing ? 'opacity-50' : 'opacity-100'}`}>
          <FileUpload 
            onUploadComplete={handleUploadComplete} 
            isProcessing={isProcessing} 
          />
        </div>
        
        {isProcessing && (
          <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 transition-opacity duration-500 z-50">
            <div className="bg-white p-8 rounded-lg shadow-xl text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-4 text-lg">Bearbetar dina filer...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
