'use client';

import { InterviewUI } from '../../../../components/InterviewUI';

// This sandbox demonstrates how a sliced "Take an Interview" task works
export default function InterviewSandbox() {
    return (
        <div style={{ padding: '40px', backgroundColor: '#F4F5F7', minHeight: '100vh' }}>
            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
                <h1 style={{
                    color: '#005587',
                    borderBottom: '2px solid #005587',
                    paddingBottom: '10px',
                    fontFamily: 'Arial, sans-serif',
                    marginBottom: '30px'
                }}>
                    Take an Interview (Unified Component Demo)
                </h1>

                {/* We are reusing the exact same component built in InterviewUI.tsx */}
                <div style={{ backgroundColor: '#fff', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                    <InterviewUI
                        promptVideoUrl="/legacy_idle_loop.mp4"
                        maxRecordTimeSeconds={45}
                        websocketUrl="ws://localhost:8000/ws/audio"
                    />
                </div>

                <div style={{ marginTop: '40px', padding: '20px', borderLeft: '4px solid #005587', backgroundColor: '#eef6fb', fontFamily: 'Arial, sans-serif' }}>
                    <h3 style={{ margin: '0 0 10px 0' }}>About this Component</h3>
                    <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.5 }}>
                        This page is using the <code>InterviewUI</code> component.
                        In a real test, the <code>TestSequencer</code> would automatically
                        render this component whenever the backend delivers an interview-type task.
                    </p>
                </div>
            </div>
        </div>
    );
}
