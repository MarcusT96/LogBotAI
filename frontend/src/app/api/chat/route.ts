import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { message } = await req.json();

    // Call your FastAPI backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: message })
    });

    if (!response.ok) {
      throw new Error('Backend API call failed');
    }

    const data = await response.json();

    // Format the response to match our frontend's expected structure
    const formattedResponse = {
      id: Date.now(),
      text: data.answer,
      sender: 'ai' as const
    };

    return NextResponse.json(formattedResponse);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { 
        id: Date.now(),
        text: "Ett fel uppstod. Försök igen senare.",
        sender: 'ai'
      },
      { status: 500 }
    );
  }
} 