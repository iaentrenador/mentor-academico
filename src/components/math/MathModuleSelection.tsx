import React from 'react';
import { Calculator, CheckCircle, HelpCircle, ArrowLeft } from 'lucide-react';

interface MathModuleSelectionProps {
  onSelectCorrection: () => void;
  onSelectExplainer: () => void;
  onBack: () => void;
}

const MathModuleSelection: React.FC<MathModuleSelectionProps> = ({ 
  onSelectCorrection, 
  onSelectExplainer, 
  onBack 
}) => {
  return (
    <div className="space-y-8 max-w-4xl mx-auto p-4">
      {/* Encabezado */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center">
            <Calculator className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-slate-800">Módulo de Matemáticas</h2>
            <p className="text-slate-500">Tutoría para Higiene y Seguridad - UPE</p>
          </div>
        </div>
        <button onClick={onBack} className="p-2 text-slate-400 hover:text-slate-600">
          <ArrowLeft className="w-6 h-6" />
        </button>
      </div>

      {/* Botones de Selección */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <button 
          onClick={onSelectCorrection}
          className="p-8 bg-white border-2 border-blue-500 rounded-3xl hover:bg-blue-50 transition-all text-center shadow-sm"
        >
          <CheckCircle className="w-12 h-12 text-blue-600 mx-auto mb-4" />
          <h4 className="font-bold text-xl mb-2">Corrección de Ejercicios</h4>
          <p className="text-sm text-slate-500">Evaluación paso a paso de tu resolución.</p>
        </button>

        <button 
          onClick={onSelectExplainer}
          className="p-8 bg-white border-2 border-amber-500 rounded-3xl hover:bg-amber-50 transition-all text-center shadow-sm"
        >
          <HelpCircle className="w-12 h-12 text-amber-600 mx-auto mb-4" />
          <h4 className="font-bold text-xl mb-2">Explicador de Ejercicios</h4>
          <p className="text-sm text-slate-500">Aprende con ejemplos similares.</p>
        </button>
      </div>
    </div>
  );
};

export default MathModuleSelection;
      
