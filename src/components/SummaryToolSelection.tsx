// src/components/SummaryToolSelection.tsx
import React from 'react';

interface SummaryToolSelectionProps {
  onBack: () => void;
  onStartCorrection: () => void;
  onStartAutomatic: () => void;
}

const SummaryToolSelection: React.FC<SummaryToolSelectionProps> = ({ onBack, onStartCorrection, onStartAutomatic }) => {
  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto w-full">
      <div className="text-center">
        <h3 className="text-3xl font-black text-slate-800 uppercase italic tracking-tighter italic">Módulo de Resúmenes</h3>
        <p className="text-slate-500 font-bold text-xs uppercase tracking-widest mt-1">¿Cómo deseas trabajar tus síntesis académicas hoy?</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Generación Automática */}
        <button 
          onClick={onStartAutomatic}
          className="flex flex-col items-center p-10 bg-white border-2 border-emerald-100 rounded-[2.5rem] hover:border-emerald-500 hover:bg-emerald-50 transition-all group shadow-sm text-center active:scale-95"
        >
          <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-4xl mb-6 group-hover:scale-110 transition-transform shadow-inner">
            🤖
          </div>
          <h4 className="font-black text-slate-800 text-xl uppercase tracking-tight">Generación Automática</h4>
          <p className="text-xs text-slate-500 mt-3 leading-relaxed font-medium">
            Sube un texto y el Instructor generará un resumen jerarquizado con conceptos clave y conclusiones analíticas.
          </p>
        </button>

        {/* Corrección de Mi Resumen */}
        <button 
          onClick={onStartCorrection}
          className="flex flex-col items-center p-10 bg-white border-2 border-indigo-100 rounded-[2.5rem] hover:border-indigo-500 hover:bg-indigo-50 transition-all group shadow-sm text-center active:scale-95"
        >
          <div className="w-20 h-20 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-4xl mb-6 group-hover:scale-110 transition-transform shadow-inner">
            🎓
          </div>
          <h4 className="font-black text-slate-800 text-xl uppercase tracking-tight">Corrección de Mi Resumen</h4>
          <p className="text-xs text-slate-500 mt-3 leading-relaxed font-medium">
            Pega tu resumen y el texto original. El Instructor evaluará tu capacidad de síntesis y sugerirá mejoras.
          </p>
        </button>
      </div>

      <div className="flex justify-center pt-4">
        <button 
          onClick={onBack} 
          className="text-slate-400 font-black text-[10px] uppercase tracking-[0.2em] hover:text-indigo-600 transition-colors border-b-2 border-transparent hover:border-indigo-600 pb-1"
        >
          Volver al Inicio
        </button>
      </div>
    </div>
  );
};

export default SummaryToolSelection;
