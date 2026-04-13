import React, { useState } from 'react';
import { WritingCorrectionInput } from '../types';
import { BookOpen, Target, FileText, Send } from 'lucide-react';

interface Props {
  onSubmit: (input: WritingCorrectionInput) => void;
  isLoading: boolean;
}

const WritingCorrectionForm: React.FC<Props> = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [writing, setWriting] = useState('');
  const [materia, setMateria] = useState('higiene_upe');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !writing.trim()) {
      alert("Por favor, completa la consigna y tu escrito.");
      return;
    }
    onSubmit({
      prompt,
      sourceText,
      writing,
      materia,
      activityType: 'corregir_escrito',
      activityTitle: 'Corrección de Escrito Académico'
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6 animate-in fade-in duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-slate-800">Corrección Universitaria</h2>
        <p className="text-slate-500 text-sm">Carga los datos para una evaluación docente detallada.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Selector de Materia */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <label className="block text-xs font-black text-indigo-600 uppercase tracking-widest mb-3">
            Perfil de Evaluación
          </label>
          <select 
            value={materia}
            onChange={(e) => setMateria(e.target.value)}
            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-indigo-500 outline-none"
          >
            <option value="higiene_upe">Higiene y Seguridad (UPE)</option>
            <option value="politica_upe">Política y Sociedad (UPE)</option>
            <option value="alfabetizacion_upe">Alfabetización Académica (UPE)</option>
            <option value="abogacia_unlz">Derecho (UNLZ)</option>
            <option value="general">Mentor Académico General</option>
          </select>
        </div>

        {/* Campo 1: Consigna */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <label className="flex items-center gap-2 text-xs font-black text-slate-700 uppercase tracking-widest">
            <Target className="w-4 h-4 text-indigo-500" />
            1. Consigna del Profesor
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="¿Qué te pidió el profesor? (Ej: Realice un informe sobre riesgos eléctricos...)"
            className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm min-h-[100px] focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
          />
        </div>

        {/* Campo 2: Material (Opcional) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <label className="flex items-center gap-2 text-xs font-black text-slate-700 uppercase tracking-widest text-slate-400">
            <BookOpen className="w-4 h-4" />
            2. Material de Consulta (Opcional)
          </label>
          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Pega aquí el texto de referencia o bibliografía para una corrección más precisa..."
            className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm min-h-[150px] focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
          />
        </div>

        {/* Campo 3: El Escrito */}
        <div className="bg-white p-5 rounded-2xl border border-indigo-100 shadow-md space-y-3 ring-2 ring-indigo-500/5">
          <label className="flex items-center gap-2 text-xs font-black text-indigo-600 uppercase tracking-widest">
            <FileText className="w-4 h-4" />
            3. Tu Producción / Respuesta
          </label>
          <textarea
            value={writing}
            onChange={(e) => setWriting(e.target.value)}
            placeholder="Escribe o pega aquí tu trabajo..."
            className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm min-h-[250px] focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-4 rounded-2xl font-bold text-white shadow-lg flex items-center justify-center gap-3 transition-all active:scale-95 ${
            isLoading ? 'bg-slate-400' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200'
          }`}
        >
          {isLoading ? (
            <div className="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <>
              <span>Enviar para Corrección</span>
              <Send className="w-5 h-5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default WritingCorrectionForm;
