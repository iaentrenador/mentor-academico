import React, { useState } from 'react';
import { UniversityText } from '../types';

interface Props {
  onSubmit: (input: UniversityText) => void;
  onBack: () => void;
}

const ConceptualNetworkInputView: React.FC<Props> = ({ onSubmit, onBack }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const handleProcess = () => {
    if (!content.trim()) {
      alert('Por favor proporciona un texto para analizar.');
      return;
    }
    // Enviamos los datos con el formato que espera el backend
    onSubmit({ 
      title: title || 'Análisis de Red Conceptual', 
      content,
      materia: 'higiene_upe', // Valor por defecto o el que manejes
      sourceType: 'manual'
    });
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
      <div className="text-center">
        <h3 className="text-2xl font-bold text-slate-800 tracking-tighter uppercase">Red Conceptual Automática</h3>
        <p className="text-slate-500 text-sm">Pega el contenido académico para visualizar sus relaciones lógicas.</p>
      </div>

      <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-xl max-w-3xl mx-auto space-y-6">
        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase mb-2 tracking-[0.2em]">Título del Material</label>
            <input 
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ej: Ley 19587 - Introducción"
              className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none font-bold text-slate-700 transition-all"
            />
          </div>

          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase mb-2 tracking-[0.2em]">Texto a Analizar</label>
            <textarea 
              rows={10}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Pega aquí los apuntes, leyes o definiciones..."
              className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-2 focus:ring-indigo-500 outline-none resize-none font-serif leading-relaxed text-slate-600"
            />
          </div>

          <div className="pt-4 flex gap-4">
            <button 
              onClick={onBack} 
              className="px-8 py-4 bg-slate-100 text-slate-500 font-black uppercase text-xs tracking-widest rounded-2xl hover:bg-slate-200 transition-all"
            >
              Cancelar
            </button>
            <button 
              onClick={handleProcess}
              className="flex-1 py-4 bg-indigo-600 text-white font-black uppercase text-xs tracking-widest rounded-2xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 flex items-center justify-center gap-2 active:scale-95"
            >
              <span>Generar Síntesis Visual</span>
              <span className="text-lg">🕸️</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConceptualNetworkInputView;
