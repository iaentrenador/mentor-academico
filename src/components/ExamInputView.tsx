import React, { useState } from 'react';
import { ExamQuestionType } from '../types';

interface ExamInputViewProps {
  onStart: (material: string, count: number, types: ExamQuestionType[]) => void;
  onBack: () => void;
  isLoading: boolean;
}

const ExamInputView: React.FC<ExamInputViewProps> = ({ onStart, onBack, isLoading }) => {
  const [material, setMaterial] = useState('');
  const [count, setCount] = useState(5);
  // FIX: Se asegura la asignación inicial con el tipo correcto
  const [types, setTypes] = useState<ExamQuestionType[]>(['multiple-choice' as ExamQuestionType]);

  const toggleType = (type: ExamQuestionType) => {
    if (types.includes(type)) {
      if (types.length > 1) setTypes(types.filter(t => t !== type));
    } else {
      setTypes([...types, type]);
    }
  };

  const handleStart = () => {
    if (!material.trim()) {
      alert("Por favor, ingresa el material de estudio.");
      return;
    }
    onStart(material, count, types);
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-800">Simulacro de Examen Parcial</h2>
        <p className="text-slate-500">Configura tu examen basado en el material de la UPE.</p>
      </div>

      <div className="space-y-6">
        {/* Área de Texto */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Material de Estudio (Apuntes, Leyes, Textos)
          </label>
          <textarea
            className="w-full h-64 p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none transition-all"
            placeholder="Pega aquí el contenido para el examen..."
            value={material}
            onChange={(e) => setMaterial(e.target.value)}
          />
        </div>

        {/* Configuración */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Cantidad de Preguntas: <span className="text-indigo-600 font-bold">{count}</span>
            </label>
            <input
              type="range"
              min="3"
              max="20"
              step="1"
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Tipos de Preguntas</label>
            <div className="flex flex-wrap gap-2">
              {/* FIX: Se mapea usando las claves que TypeScript ahora reconoce en types.ts */}
              {(['multiple-choice', 'development', 'justification'] as ExamQuestionType[]).map(type => (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleType(type)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                    types.includes(type)
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                      : 'bg-white border-slate-200 text-slate-600'
                  }`}
                >
                  {type === ('multiple-choice' as ExamQuestionType) ? 'Opción Múltiple' : 
                   type === ('development' as ExamQuestionType) ? 'Desarrollo' : 'Justificación'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Acciones */}
        <div className="flex gap-4 pt-4">
          <button
            onClick={onBack}
            className="flex-1 py-3 px-6 rounded-xl font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleStart}
            disabled={isLoading}
            className={`flex-[2] py-3 px-6 rounded-xl font-semibold text-white transition-all shadow-md ${
              isLoading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98]'
            }`}
          >
            {isLoading ? 'Generando Examen...' : 'Comenzar Simulacro'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExamInputView;
