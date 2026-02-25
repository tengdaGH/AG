import { useRef, useState, useCallback } from 'react';

/**
 * Custom hook to manage the MediaRecorder with 5-second WebRTC timeslice chunking.
 * Prevents catastrophic data loss if the browser/network dies in second 44 of a 45s speaking task.
 */
export const useMediaRecorderChunking = (webSocketUrl: string) => {
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const startRecording = useCallback(async () => {
        try {
            // Re-establish WebSocket Connection for the Session
            wsRef.current = new WebSocket(webSocketUrl);
            wsRef.current.onopen = () => console.log('WebSocket for audio chunks ready.');

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Prefer Opus codec for ETS standardization
            const mimeType = 'audio/webm;codecs=opus';
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });

            mediaRecorderRef.current.ondataavailable = (event: BlobEvent) => {
                if (event.data && event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
                    // Stream the 5-second chunk directly to the backend
                    wsRef.current.send(event.data);
                }
            };

            // Start recording and output data chunks every 5000ms (5 seconds)
            // This is the core instruction to prevent memory blowout / ensure secure upload
            mediaRecorderRef.current.start(5000);
            setIsRecording(true);

        } catch (err) {
            setError('Microphone access denied or WebSocket failure.');
            console.error(err);
        }
    }, [webSocketUrl]);

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            // Stop all physical microphone tracks
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            setIsRecording(false);

            // Notify backend that the stream is complete
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'END_OF_STREAM' }));
                wsRef.current.close();
            }
        }
    }, [isRecording]);

    return {
        isRecording,
        startRecording,
        stopRecording,
        error
    };
};
