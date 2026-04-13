// src/components/SummaryGenerationResultsView.tsx
import React from 'react';
import { SummaryGenerationResult } from '../types';
import { Target, Lightbulb, ArrowRight, RotateCcw } from 'lucide-react';

interface SummaryGenerationResultsViewProps {
  result: SummaryGenerationResult;
  onRestart: () => void;
}

const SummaryGenerationResultsView: React.FC<SummaryGenerationResultsViewProps> = ({ result, onRestart }) => {
  return (
    <div className="space-y-10 animate-in fade-in zoom-in-95 duration-700 max-w-4xl mx-auto w-full pb-20">
      
      {/* Cabecera del Resultado */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-100 text-emerald-700 text-[10px] font-black uppercase rounded-full border border-emerald-200 tracking-[0.2em]">
          <Target size={12} />
          SÍNTESIS FINALIZADA
        </div>
        <h3 className="text-4xl font-black text-slate-800 uppercase tracking-tighter italic leading-tight">
          {result.title}
        </h3>
      </div>

      <div className="bg-white rounded-[3rem] border-2 border-slate-100 shadow-2xl overflow-hidden shadow-emerald-100/20">
        
        {/* Cuerpo del Resumen */}
        <div className="p-8 md:p-12 space-y-10">
          
          <section className="space-y-4">
            <div className="flex items-center gap-2 text-emerald-600 border-b border-emerald-50 pb-2">
              <span className="text-[10px] font-black uppercase tracking-widest">Resumen Ejecutivo</span>
            </div>
            <p className="text-xl text-slate-700 leading-relaxed font-serif indent-10 italic">
              {result.executiveSummary}
            </p>
          </section>

          {/* Conceptos Clave en Grilla */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 text-indigo-600 border-b border-indigo-50 pb-2">
              <Lightbulb size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Conceptos Clave y Definiciones</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.keyConcepts.map((item, idx) => (
                <div key={idx} className="group p-5 bg-slate-50 rounded-2xl border-2 border-transparent hover:border-indigo-100 hover:bg-white transition-all duration-300">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                       <ArrowRight size={14} className="text-indigo-400 group-hover:translate-x-1 transition-transform" />
                    </div>
                    <div>
                      <span className="font-black text-slate-800 block mb-1 text-sm uppercase tracking-tight">
                        {item.concept}
                      </span>
                      <p className="text-xs text-slate-500 leading-relaxed font-medium">
                        {item.definition}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Conclusiones Finales */}
          <section className="pt-4">
            <div className="p-8 bg-slate-900 rounded-[2rem] text-white relative overflow-hidden">
               <div className="absolute top-0 right-0 p-4 opacity-10">
                 <Target size={80} strokeWidth={1} />
               </div>
               <h4 className="font-black text-emerald-400 text-xs uppercase mb-3 tracking-widest">Conclusiones del Mentor</h4>
               <p className="text-sm text-slate-300 leading-relaxed font-medium relative z-10">
                 {result.conclusions}
               </p>
            </div>
          </section>

        </div>
      </div>

      {/* Botón para volver a empezar */}
      <div className="flex justify-center">
        <button 
          onClick={onRestart}
          className="group px-10 py-5 bg-white border-2 border-slate-200 text-slate-800 font-black rounded-2xl hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-all shadow-xl active:scale-95 flex items-center gap-3 uppercase tracking-widest text-xs"
        >
          <RotateCcw size={18} className="group-hover:rotate-180 transition-transform duration-500" />
          Procesar otro Material
        </button>
      </div>
    </div>
  );
};

export default SummaryGenerationResultsView;
