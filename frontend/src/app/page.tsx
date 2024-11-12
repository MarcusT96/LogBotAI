'use client';

import FileUpload from '@/components/fileUpload';

export default function Home() {
  const handleUploadComplete = () => {
    // This function can be empty now, as the redirection is handled in the FileUpload component
  };

  return (
    <FileUpload onUploadComplete={handleUploadComplete} />
  );
}
