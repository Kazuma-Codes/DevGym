import React, { useState, useRef } from 'react';
import { Mic, Square, Upload, Brain, Activity } from 'lucide-react';
import { InterviewMode, VoiceStats } from './types';
import axios from 'axios';

export default function App() {
  const [mode, setMode] = useState<InterviewMode>('SUBJECT');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQ, setCurrentQ] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [voiceStats, setVoiceStats] = useState<VoiceStats | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);

  const startInterview = async () => {
    // 1. Upload dummy profile for demo
    const prof = await axios.post('http://localhost:8000/api/profile', { resume: "React Dev" });
    // 2. Start Session
    const res = await axios.post('http://localhost:8000/api/start', { 
      profile_id: prof.data.profile_id, mode 
    });
    setSessionId(res.data.session_id);
    setCurrentQ(res.data.question);
  };

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    chunks.current = [];
    mediaRecorder.current.ondataavailable = (e) => chunks.current.push(e.data);
    mediaRecorder.current.onstop = async () => {
      const blob = new Blob(chunks.current, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('audio', blob, 'ans.webm');
      formData.append('question', currentQ);
      
      const res = await axios.post(`http://localhost:8000/api/answer/${sessionId}`, formData);
      setVoiceStats(res.data.voice);
      setCurrentQ(res.data.next_question || "Interview Complete!");
    };
    mediaRecorder.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    setIsRecording(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="flex justify-between items-center mb-12 border-b border-slate-800 pb-6">
          <h1 className="text-3xl font-bold flex items-center gap-3"><Brain className="text-blue-500"/> AI Interview Platform</h1>
          <select value={mode} onChange={(e) => setMode(e.target.value as InterviewMode)} className="bg-slate-900 border border-slate-700 rounded-lg p-2">
            <option value="SUBJECT">Standard Technical</option>
            <option value="PROJECT_GRILL">Project Grill Mode</option>
            <option value="BEHAVIORAL">STAR Behavioral</option>
            <option value="JD_MATCH">JD Matcher</option>
          </select>
        </header>

        {!sessionId ? (
          <button onClick={startInterview} className="w-full py-4 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold text-lg transition">
            Initialize {mode.replace('_', ' ')} Interview
          </button>
        ) : (
          <div className="space-y-8">
            <div className="bg-slate-900 p-8 rounded-2xl border-l-4 border-blue-500 shadow-2xl">
              <p className="text-sm text-blue-400 uppercase tracking-wider mb-2">Current Question</p>
              <h2 className="text-2xl font-medium">{currentQ}</h2>
            </div>

            <div className="flex flex-col items-center gap-4">
              <button 
                onClick={isRecording ? stopRecording : startRecording}
                className={`w-32 h-32 rounded-full flex items-center justify-center transition-all shadow-lg ${
                  isRecording ? 'bg-red-600 animate-pulse' : 'bg-slate-800 hover:bg-slate-700'
                }`}
              >
                {isRecording ? <Square size={48}/> : <Mic size={48}/>}
              </button>
              <p className="text-slate-400">{isRecording ? "Recording... Speak clearly." : "Click to answer"}</p>
            </div>

            {voiceStats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-in fade-in slide-in-from-bottom-4">
                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 text-center">
                  <p className="text-4xl font-bold text-blue-400">{voiceStats.wpm}</p>
                  <p className="text-slate-500 text-sm mt-1">Words / Min</p>
                </div>
                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 text-center">
                  <p className="text-4xl font-bold text-yellow-400">{voiceStats.filler_count}</p>
                  <p className="text-slate-500 text-sm mt-1">Filler Words</p>
                </div>
                <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 text-center">
                  <p className="text-4xl font-bold text-purple-400">{voiceStats.max_pause}s</p>
                  <p className="text-slate-500 text-sm mt-1">Max Pause</p>
                </div>
                <div className="col-span-full bg-slate-900 p-6 rounded-xl border border-green-500/30">
                  <div className="flex items-center gap-2 text-green-400 mb-2"><Activity size={18}/> Delivery Coach</div>
                  <p className="text-slate-300">{voiceStats.feedback}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}