"use client";
import React, { useEffect, useRef, useState } from 'react';

interface MicVisualizerProps {
    isRecording: boolean;
    color?: string;
}

export default function MicVisualizer({ isRecording, color = '#D93A30' }: MicVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const rafRef = useRef<number | null>(null);
    const [hasPermission, setHasPermission] = useState<boolean | null>(null);

    useEffect(() => {
        if (!isRecording) {
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            if (audioCtxRef.current) {
                audioCtxRef.current.close();
                audioCtxRef.current = null;
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
                streamRef.current = null;
            }
            return;
        }

        const initMic = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                setHasPermission(true);
                streamRef.current = stream;

                const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
                const audioCtx = new AudioContext();
                audioCtxRef.current = audioCtx;

                const analyser = audioCtx.createAnalyser();
                analyser.fftSize = 256;
                analyserRef.current = analyser;

                const source = audioCtx.createMediaStreamSource(stream);
                source.connect(analyser);

                draw();
            } catch (err) {
                console.error("Mic access denied:", err);
                setHasPermission(false);
            }
        };

        const draw = () => {
            if (!canvasRef.current || !analyserRef.current) return;
            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            const bufferLength = analyserRef.current.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            analyserRef.current.getByteFrequencyData(dataArray);

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;

            // Draw a simple volume bar that scales with the average volume
            const width = 120;
            const height = 12;

            // Background bar (light grey)
            ctx.fillStyle = '#E0E0E0';
            ctx.fillRect(0, 0, width, height);

            // Foreground bar (volume level)
            const mapVolume = Math.min(100, (average / 128) * 100); // 0 to 100
            const activeWidth = (mapVolume / 100) * width;

            ctx.fillStyle = color;
            ctx.fillRect(0, 0, activeWidth, height);

            rafRef.current = requestAnimationFrame(draw);
        };

        initMic();

        return () => {
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            if (audioCtxRef.current) audioCtxRef.current.close().catch(e => console.error(e));
            if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop());
        };
    }, [isRecording, color]);

    if (!isRecording) return null;

    if (hasPermission === false) {
        return <div style={{ color: color, fontSize: 12 }}>Microphone permission denied</div>;
    }

    return (
        <canvas
            ref={canvasRef}
            width={120}
            height={12}
            style={{ display: 'block', margin: '8px auto 0', opacity: 0.9 }}
        />
    );
}
