import React from 'react';
import { ConceptualNetworkResult } from '../types';

interface Props {
  result: ConceptualNetworkResult;
  onBack: () => void; // Cambiado de onRestart a onBack
}

const ConceptualNetworkView: React.FC<Props> = ({ result, onBack }) => {
  const coreNodes = result.nodes.filter(n => n.type === 'core');
  const mainNodes = result.nodes.filter(n => n.type === 'main');

  const getChildren = (parentId: string) => {
    const childrenIds = result.edges
      .filter(edge => edge.from === parentId)
      .map(edge => ({ toId: edge.to, label: edge.label }));
    return result.nodes.filter(n => childrenIds.some(c => c.toId === n.id));
  };

  const getEdgeLabel = (from: string, to: string) => {
    return result.edges.find(e => e.from === from && e.to === to)?.label || '';
  };

  return (
    <div className="space-y-12 animate-in fade-in zoom-in-95 duration-700 max-w-6xl mx-auto pb-20">
      {/* Encabezado */}
      <div className="text-center space-y-2">
        <span className="px-4 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-black uppercase rounded-full tracking-widest border border-indigo-100 shadow-sm">
          Arquitectura del Conocimiento
        </span>
        <h3 className="text-4xl font-black text-slate-800 uppercase tracking-tighter">Red Conceptual de Cátedra</h3>
        <p className="text-slate-500 text-sm max-w-lg mx-auto italic">
          Representación jerárquica: del núcleo a las derivaciones secundarias.
        </p>
      </div>

      {/* Análisis Estructural */}
      <div className="max-w-3xl mx-auto p-6 bg-white rounded-2xl border border-slate-200 shadow-sm text-center italic text-slate-600 font-serif leading-relaxed relative">
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white px-3 text-[9px] font-black text-slate-400 uppercase tracking-widest border border-slate-100 rounded">
          Análisis Estructural
        </div>
        "{result.summary}"
      </div>

      {/* Contenedor de la Red */}
      <div className="bg-slate-50/50 rounded-[3rem] p-12 border border-slate-200 shadow-inner overflow-x-auto min-h-[600px] flex flex-col items-center">
        
        {/* NIVEL 1: NÚCLEO */}
        <div className="flex flex-col items-center mb-16 relative">
          {coreNodes.map(node => (
            <div key={node.id} className="group relative">
              <div className="px-8 py-5 bg-indigo-600 text-white rounded-2xl shadow-2xl shadow-indigo-200 border-2 border-indigo-700 text-lg font-black tracking-tight transform group-hover:scale-105 transition-all text-center">
                {node.label}
              </div>
              <div className="absolute top-full left-1/2 -translate-x-1/2 w-0.5 h-16 bg-gradient-to-b from-indigo-500 to-slate-300"></div>
            </div>
          ))}
        </div>

        {/* NIVEL 2: CONCEPTOS PRINCIPALES */}
        <div className="flex flex-row justify-center gap-8 mb-16 relative w-full flex-wrap">
          {mainNodes.map(node => {
            const labelFromCore = getEdgeLabel(coreNodes[0]?.id || '', node.id);
            return (
              <div key={node.id} className="flex flex-col items-center group relative min-w-[220px]">
                {labelFromCore && (
                  <div className="absolute -top-10 bg-white px-2 py-0.5 border border-slate-100 rounded text-[9px] font-black text-indigo-500 uppercase tracking-tighter z-10 shadow-sm">
                    {labelFromCore}
                  </div>
                )}
                
                <div className="px-6 py-4 bg-white border-2 border-slate-800 rounded-xl shadow-lg text-slate-800 font-bold text-sm tracking-tight group-hover:border-indigo-500 transition-all text-center z-10">
                  {node.label}
                </div>

                {/* NIVEL 3: CONCEPTOS SECUNDARIOS */}
                <div className="flex flex-col items-center gap-3">
                  {getChildren(node.id).map(subNode => (
                    <div key={subNode.id} className="flex flex-col items-center group/sub relative">
                      <div className="w-0.5 h-6 bg-slate-200"></div>
                      <div className="px-4 py-2.5 bg-slate-100 border border-slate-200 border-dashed rounded-lg text-slate-500 text-xs font-medium hover:bg-white hover:border-indigo-300 hover:text-indigo-600 transition-all text-center">
                        <span className="block text-[8px] opacity-40 uppercase font-black mb-0.5 tracking-tighter">
                          {getEdgeLabel(node.id, subNode.id)}
                        </span>
                        {subNode.label}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Botón Reiniciar */}
      <div className="flex justify-center pt-8">
        <button 
          onClick={onBack}
          className="px-12 py-4 bg-slate-900 text-white font-bold rounded-2xl hover:bg-slate-800 transition-all shadow-xl active:scale-95 flex items-center gap-3"
        >
          <span>Analizar otro Material</span>
          <span>🕸️</span>
        </button>
      </div>
    </div>
  );
};

export default ConceptualNetworkView;
