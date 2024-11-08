import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    
    // Send to FastAPI backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/upload-documents`, {
      method: 'POST',
      body: formData, // FastAPI expects multipart/form-data
    });

    if (!response.ok) {
      throw new Error('Failed to upload files');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: 'Failed to upload files' },
      { status: 500 }
    );
  }
} 