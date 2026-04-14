import React, { useState } from 'react';
import { MathExplainerInput } from '../../types';
import { HelpCircle, BookOpen, Zap } from 'lucide-react';

interface MathExplainerFormProps {
  onSubmit: (input: MathExplainerInput) => void;
  onBack: () => void;
}

const MathExplainerForm: React.FC<MathExplainerFormProps> = ({ onSubmit, onBack }) => {
  const [topic, setTopic] = useState('');
  const [specificExercise, setSpecificExercise] = useState('');

  const handleSubmit = () => {
    if (!topic.trim() || !specificExercise.trim()) {
      alert('Por favor indica el tema y el ejercicio que te genera dudas.');
      return;
    }
    onSubmit({ topic, specificExercise });
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto p-4 animate-in slide-in-from-bottom-4">
      <div className="text-center">
        <h3 className="text-2xl font-bold text-slate-800">Explicador Matemático</h3>
        <p className="text-slate-500 font-medium">UPE - Ciclo Propedéutico</p>
      </div>

      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xl space-y-6">
        <div>
          <label className="flex items-center gap-2 text-xs font-bold text-amber-600 uppercase mb-2 tracking-widest">
            <span className="w-5 h-5 bg-amber-50 rounded flex items-center justify-center italic">1</span>
            Tema o Concepto (Ej: Derivadas)
          </label>
          <input 
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Ej: Integrales, Límites..."
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 outline-none"
          />
        </div>

        <div>
          <label className="flex items-center gap-2 text-xs font-bold text-amber-600 uppercase mb-2 tracking-widest">
            <span className="w-5 h-5 bg-amber-50 rounded flex items-center justify-center italic">2</span>
            Ejercicio con el que tenés dudas
          </label>
          <textarea 
            rows={5}
            value={specificExercise}
            onChange={(e) => setSpecificExercise(e.target.value)}
            placeholder="Escribe o pega el ejercicio aquí..."
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 outline-none resize-none font-mono text-sm"
          />
        </div>

        <div className="pt-4 flex gap-4">
          <button 
            onClick={onBack}
            className="px-8 py-4 bg-slate-100 text-slate-600 font-bold rounded-xl hover:bg-slate-200"
          >
            Atrás
          </button>
          <button 
            onClick={handleSubmit}
            className="flex-1 py-4 bg-amber-600 text-white font-bold rounded-xl hover:bg-amber-700 shadow-lg flex items-center justify-center gap-2"
          >
            <span>Pedir Explicación</span>
            <Zap className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default MathExplainerForm;
