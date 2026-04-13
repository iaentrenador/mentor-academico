// src/components/SummaryCorrectionInputView.tsx
import React, { useState } from 'react';
import { ChevronLeft, AlignLeft, FileText, Send } from 'lucide-react';

interface SummaryCorrectionInputViewProps {
  onSubmit: (sourceText: string, userSummary: string) => void;
  onBack: () => void;
  loading: boolean;
}

const SummaryCorrectionInputView: React.FC<SummaryCorrectionInputViewProps> = ({ onSubmit, onBack, loading }) => {
  const [source, setSource] = useState('');
  const [summary, setSummary] = useState('');

  const handleProcess = () => {
    if (!source.trim() || !summary.trim()) {
      alert('Debes proporcionar tanto el texto original como tu resumen.');
      return;
    }
    onSubmit(source, summary);
  };

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500 max-w-5xl mx-auto w-full pb-10">
      
      {/* Encabezado */}
      <div className="flex justify-between items-center border-b-2 border-slate-100 pb-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={onBack} 
            className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400"
          >
            <ChevronLeft size={28} />
          </button>
          <div>
            <h3 className="text-2xl font-black text-slate-800 uppercase italic tracking-tighter leading-none">
              Corrección Analítica
            </h3>
            <span className="text-[10px] font-black text-indigo-500 uppercase tracking-[0.2em]">Evaluación de Síntesis</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Columna 1: Fuente Original */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 ml-2 text-slate-400">
            <AlignLeft size={14} />
            <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Texto Original / Fuente</label>
          </div>
          <textarea 
            rows={12}
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="Pega aquí el contenido completo de la cátedra..."
            className="w-full p-6 bg-white border-2 border-slate-100 rounded-[2rem] outline-none focus:border-slate-400 transition-all font-medium text-slate-600 text-sm leading-relaxed resize-none shadow-sm"
          />
        </div>

        {/* Columna 2: Tu Resumen */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 ml-2 text-indigo-500">
            <FileText size={14} />
            <label className="text-[10px] font-black uppercase tracking-widest text-indigo-500">Tu Resumen para Evaluar</label>
          </div>
          <textarea 
            rows={12}
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Pega aquí la síntesis que realizaste tú..."
            className="w-full p-6 bg-indigo-50/30 border-2 border-indigo-100 rounded-[2rem] outline-none focus:border-indigo-500 transition-all font-bold text-slate-700 text-sm leading-relaxed resize-none shadow-sm"
          />
        </div>
      </div>

      {/* Botón de Acción Inferior */}
      <div className="max-w-2xl mx-auto w-full pt-4">
        <button 
          onClick={handleProcess}
          disabled={loading || !source.trim() || !summary.trim()}
          className="group w-full bg-indigo-600 hover:bg-slate-900 text-white py-5 rounded-[2rem] font-black transition-all shadow-xl shadow-indigo-100 flex items-center justify-center gap-3 uppercase tracking-widest italic disabled:opacity-30 disabled:grayscale active:scale-95"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Comparando Textos...
            </span>
          ) : (
            <>
              Evaluar mi Resumen
              <Send size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </>
          )}
        </button>
      </div>

      <div className="bg-amber-50 p-4 rounded-2xl border border-amber-100 flex gap-3 mx-auto max-w-lg">
        <p className="text-[9px] text-amber-800 font-bold leading-tight uppercase tracking-tight text-center w-full">
          El análisis comparativo detectará ideas omitidas y calificará tu capacidad de jerarquización de contenidos.
        </p>
      </div>
    </div>
  );
};

export default SummaryCorrectionInputView;
