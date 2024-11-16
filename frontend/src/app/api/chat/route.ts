import { NextResponse } from 'next/server';

export async function POST(req: Request) {
    try {
        const { message, session_id } = await req.json();

        const backendUrl = process.env.BACKEND_URL

        
        const response = await fetch(`${backendUrl}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message, session_id }),
        });

        // Forward the streaming response
        return new Response(response.body, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            },
        });
    } catch (error) {
        console.error('Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
} 