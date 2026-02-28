import { useRef, useState, useCallback } from 'react';

/**
 * Custom hook to manage the MediaRecorder with 5-second HTTP POST chunking.
 * Prevents catastrophic data loss if the browser/network dies during the speaking task.
 * Also replaces WebSockets to bypass Great Firewall throttling in China.
 */
export const useMediaRecorderChunking = (uploadUrl: string, questionId: string = 'unknown', sessionId: string = 'unknown') => {
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const chunkIndexRef = useRef(0);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Prefer Opus codec for ETS standardization
            const mimeType = 'audio/webm;codecs=opus';
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
            chunkIndexRef.current = 0; // Reset chunk index

            mediaRecorderRef.current.ondataavailable = async (event: BlobEvent) => {
                if (event.data && event.data.size > 0) {
                    const currentChunkIndex = chunkIndexRef.current++;

                    // Stream the 5-second chunk directly to the backend via HTTP POST
                    const formData = new FormData();
                    formData.append('audioFile', event.data, `chunk_${currentChunkIndex}.webm`);
                    formData.append('questionId', questionId);
                    formData.append('sessionId', sessionId);
                    formData.append('chunkIndex', currentChunkIndex.toString());

                    try {
                        const res = await fetch(uploadUrl, {
                            method: 'POST',
                            body: formData
                        });
                        if (!res.ok) {
                            console.error('Failed to upload audio chunk', currentChunkIndex);
                        }
                    } catch (err) {
                        console.error('Network error uploading audio chunk', err);
                    }
                }
            };

            // Start recording and output data chunks every 5000ms (5 seconds)
            mediaRecorderRef.current.start(5000);
            setIsRecording(true);

        } catch (err) {
            setError('Microphone access denied or network error.');
            console.error(err);
        }
    }, [uploadUrl, questionId, sessionId]);

    const stopRecording = useCallback(async () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            // Stop all physical microphone tracks
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            setIsRecording(false);
        }
    }, [isRecording]);

    return {
        isRecording,
        startRecording,
        stopRecording,
        error
    };
};
