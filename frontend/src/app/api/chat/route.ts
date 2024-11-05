import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { message } = await req.json();

    // This is where you'll add your actual AI service call
    // For example:
    // const aiResponse = await fetch('your-ai-service-url', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     'Authorization': `Bearer ${process.env.AI_SERVICE_KEY}`
    //   },
    //   body: JSON.stringify({ message, context: 'meeting_minutes' })
    // });
    // const data = await aiResponse.json();

    const response = {
      id: Date.now(),
      text: `Server received: ${message}`, // This will be replaced with actual AI response
      sender: 'ai'
    };

    await new Promise(resolve => setTimeout(resolve, 1000));

    return NextResponse.json(response);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Failed to process message' },
      { status: 500 }
    );
  }
} 