import React from 'react';
// Asegúrate de que CognitiveMapData en types.ts tenga todas las propiedades usadas abajo
import { CognitiveMapData } from '../types'; 
import { Brain, TrendingUp, Target, Award, BookOpen, AlertCircle, RotateCcw } from 'lucide-react';

interface CognitiveMapViewProps {
  data: CognitiveMapData;
  onBack: () => void;
}

const CognitiveMapView: React.FC<CognitiveMapViewProps> = ({ data, onBack }) => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
      
      {/* HEADER DEL MAPA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-4xl font-black text-slate-900 tracking-tighter uppercase italic">
            Mapa <span className="text-indigo-600">Cognitivo</span>
          </h2>
          <p className="text-slate-500 font-bold uppercase text-[10px] tracking-[0.2em] mt-1">
            Análisis de neurociencia aplicada a tu progreso
          </p>
        </div>
        <button 
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-3 bg-white border-2 border-slate-100 rounded-2xl font-black text-slate-600 hover:border-indigo-600 hover:text-indigo-600 transition-all shadow-sm active:scale-95"
        >
          <RotateCcw size={18} />
          VOLVER AL INICIO
        </button>
      </div>

      {/* STATS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-8 rounded-[2rem] border-2 border-slate-100 shadow-sm hover:shadow-xl transition-all">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 shadow-inner">
              <BookOpen size={24} />
            </div>
            <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Ejercicios</span>
          </div>
          <div className="text-5xl font-black text-slate-800 tracking-tighter">
            {data.totalExercises || 0}
          </div>
          <p className="text-[10px] font-bold text-indigo-500 uppercase mt-2 tracking-tighter italic">Entrenamientos completados</p>
        </div>

        <div className="bg-white p-8 rounded-[2rem] border-2 border-slate-100 shadow-sm hover:shadow-xl transition-all">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 shadow-inner">
              <Target size={24} />
            </div>
            <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Promedio</span>
          </div>
          <div className="text-5xl font-black text-slate-800 tracking-tighter">
            {(data.averageScore || 0).toFixed(1)}
          </div>
          <p className="text-[10px] font-bold text-emerald-500 uppercase mt-2 tracking-tighter italic">Nivel de efectividad</p>
        </div>

        <div className="bg-white p-8 rounded-[2rem] border-2 border-slate-100 shadow-sm hover:shadow-xl transition-all">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-600 shadow-inner">
              <Award size={24} />
            </div>
            <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Rango</span>
          </div>
          <div className="text-3xl font-black text-slate-800 uppercase italic">
            {(data.averageScore || 0) >= 8.5 ? 'Experto' : (data.averageScore || 0) >= 7 ? 'Avanzado' : 'En Proceso'}
          </div>
          <p className="text-[10px] font-bold text-amber-500 uppercase mt-2 tracking-tighter italic">Competencia actual</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* DOMINIOS */}
        <div className="bg-slate-900 p-8 rounded-[2.5rem] shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <Brain className="text-indigo-400" size={24} />
            <h3 className="font-black text-white uppercase tracking-widest italic">Conceptos Dominados</h3>
          </div>
          <div className="flex flex-wrap gap-3">
            {data.masteredConcepts && data.masteredConcepts.length > 0 ? (
              data.masteredConcepts.map((concept: string, i: number) => (
                <span key={i} className="px-4 py-2 bg-indigo-500/10 text-indigo-300 text-[10px] font-black rounded-xl border border-indigo-500/20 uppercase tracking-widest">
                  {concept}
                </span>
              ))
            ) : (
              <p className="text-sm text-slate-500 italic">Analizando patrones de éxito...</p>
            )}
          </div>
        </div>

        {/* ÁREAS DE MEJORA */}
        <div className="bg-white p-8 rounded-[2.5rem] border-2 border-slate-100">
          <div className="flex items-center gap-3 mb-6">
            <AlertCircle className="text-amber-500" size={24} />
            <h3 className="font-black text-slate-800 uppercase tracking-widest italic">Áreas de Mejora</h3>
          </div>
          <div className="flex flex-wrap gap-3">
            {data.weakAreas && data.weakAreas.length > 0 ? (
              data.weakAreas.map((area: string, i: number) => (
                <span key={i} className="px-4 py-2 bg-amber-50 text-amber-700 text-[10px] font-black rounded-xl border border-amber-100 uppercase tracking-widest">
                  {area}
                </span>
              ))
            ) : (
              <p className="text-sm text-slate-400 italic">No se registran puntos críticos.</p>
            )}
          </div>
        </div>
      </div>

      {/* EVOLUCIÓN VISUAL */}
      <div className="bg-white p-8 rounded-[2.5rem] border-2 border-slate-100 overflow-hidden">
        <div className="flex items-center gap-3 mb-8">
          <TrendingUp className="text-indigo-600" size={24} />
          <h3 className="font-black text-slate-800 uppercase tracking-widest italic">Evolución del Aprendizaje</h3>
        </div>
        
        {data.progressOverTime && data.progressOverTime.length > 1 ? (
          <div className="h-64 flex items-end gap-3 px-4 pb-8 border-b-2 border-slate-50">
            {data.progressOverTime.map((p: any, i: number) => (
              <div key={i} className="flex-1 flex flex-col items-center group relative">
                <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-all bg-slate-900 text-white text-[10px] font-black px-2 py-1 rounded mb-2">
                  {p.score.toFixed(1)}
                </div>
                <div 
                  className="w-full bg-indigo-600 rounded-t-xl transition-all duration-1000 group-hover:bg-indigo-400 shadow-lg" 
                  style={{ height: `${p.score * 10}%` }}
                ></div>
                <span className="text-[9px] text-slate-400 font-bold uppercase rotate-45 mt-6 origin-left">
                  {new Date(p.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center bg-slate-50 rounded-[2rem] border-2 border-dashed border-slate-200">
            <p className="text-xs font-black text-slate-400 uppercase tracking-widest">Se requieren más datos para proyectar tendencia</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CognitiveMapView;
