// src/components/SummaryGenerationInputView.tsx
import React, { useState } from 'react';
import { ChevronLeft, BookOpen, Send } from 'lucide-react';

interface SummaryGenerationInputViewProps {
  onSubmit: (title: string, content: string) => void;
  onBack: () => void;
  loading: boolean;
}

const SummaryGenerationInputView: React.FC<SummaryGenerationInputViewProps> = ({ onSubmit, onBack, loading }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const handleProcess = () => {
    if (!content.trim()) {
      alert('Por favor proporciona un texto para resumir.');
      return;
    }
    onSubmit(title || 'Resumen de Texto Manual', content);
  };

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto w-full pb-10">
      
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
              Generación de Resumen
            </h3>
            <span className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.2em]">Sintetizador de Cátedra</span>
          </div>
        </div>
      </div>

      <div className="bg-white p-8 rounded-[2.5rem] border-2 border-slate-100 shadow-sm space-y-6">
        
        {/* Título del Material */}
        <div className="space-y-2">
          <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">
            Título del Material (Opcional)
          </label>
          <input 
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ej: Higiene y Seguridad Laboral - Unidad 1"
            className="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:border-emerald-500 outline-none transition-all font-bold text-slate-700"
          />
        </div>

        {/* Área de Texto Principal */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 ml-2 text-slate-400">
            <BookOpen size={14} />
            <label className="text-[10px] font-black uppercase tracking-widest">Contenido para Resumir</label>
          </div>
          <textarea 
            rows={12}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Pega aquí el texto académico que deseas sintetizar..."
            className="w-full px-6 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:border-emerald-500 outline-none resize-none font-medium leading-relaxed text-slate-700 text-lg"
          />
        </div>

        {/* Botón de Acción */}
        <button 
          onClick={handleProcess}
          disabled={loading || !content.trim()}
          className="group w-full bg-emerald-600 hover:bg-slate-900 text-white py-5 rounded-[2rem] font-black transition-all shadow-xl shadow-emerald-100 flex items-center justify-center gap-3 uppercase tracking-widest italic disabled:opacity-30 disabled:grayscale active:scale-95"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Procesando Síntesis...
            </span>
          ) : (
            <>
              Generar Resumen
              <Send size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </>
          )}
        </button>
      </div>

      <div className="bg-emerald-50 p-4 rounded-2xl border border-emerald-100 flex gap-3 mx-4">
        <p className="text-[9px] text-emerald-800 font-bold leading-tight uppercase tracking-tight text-center w-full">
          El Instructor identificará automáticamente los conceptos clave y las conclusiones más importantes del texto.
        </p>
      </div>
    </div>
  );
};

export default SummaryGenerationInputView;
