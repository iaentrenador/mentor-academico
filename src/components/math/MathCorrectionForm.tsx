import React, { useState } from 'react';
import { MathCorrectionInput } from '../../types';
import { CheckCircle2, Upload, FileText, Send, X } from 'lucide-react';

interface MathCorrectionFormProps {
  onSubmit: (input: MathCorrectionInput) => void;
  onBack: () => void;
}

const MathCorrectionForm: React.FC<MathCorrectionFormProps> = ({ onSubmit, onBack }) => {
  const [exercisePrompt, setExercisePrompt] = useState('');
  const [studentAnswer, setStudentAnswer] = useState('');
  const [referenceMaterial, setReferenceMaterial] = useState('');
  const [file, setFile] = useState<{ base64: string; name: string } | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFile({
          base64: reader.result as string,
          name: selectedFile.name
        });
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleSubmit = () => {
    if (!exercisePrompt.trim() || !studentAnswer.trim()) {
      alert('Por favor, ingresa la consigna y tu resolución.');
      return;
    }
    onSubmit({
      exercisePrompt,
      studentAnswer,
      referenceMaterial: referenceMaterial || undefined,
      referenceFile: file ? { base64: file.base64, mimeType: 'application/pdf' } : undefined
    });
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto p-4 animate-in slide-in-from-bottom-4">
      <div className="text-center">
        <h3 className="text-2xl font-bold text-slate-800">Corrector de Ejercicios</h3>
        <p className="text-slate-500 font-medium">Evaluación detallada paso a paso</p>
      </div>

      <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-xl space-y-6">
        {/* Consigna */}
        <div>
          <label className="block text-xs font-bold text-blue-600 uppercase mb-2 tracking-widest">1. Consigna del Problema</label>
          <textarea 
            rows={3}
            value={exercisePrompt}
            onChange={(e) => setExercisePrompt(e.target.value)}
            placeholder="¿Cuál es el ejercicio a resolver?"
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none text-sm"
          />
        </div>

        {/* Resolución del Alumno */}
        <div>
          <label className="block text-xs font-bold text-blue-600 uppercase mb-2 tracking-widest">2. Tu Resolución</label>
          <textarea 
            rows={6}
            value={studentAnswer}
            onChange={(e) => setStudentAnswer(e.target.value)}
            placeholder="Describe aquí tu procedimiento y resultado final..."
            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-none font-mono text-sm"
          />
        </div>

        {/* Material de Referencia / Archivos */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2 tracking-widest italic">Material de Apoyo (Opcional)</label>
            <input 
              type="text"
              value={referenceMaterial}
              onChange={(e) => setReferenceMaterial(e.target.value)}
              placeholder="Ej: Apunte de cátedra..."
              className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs outline-none"
            />
          </div>
          
          <div className="relative">
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-2 tracking-widest italic">Adjuntar PDF/Foto</label>
            {!file ? (
              <label className="flex items-center justify-center w-full h-10 border-2 border-dashed border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                <Upload className="w-4 h-4 text-slate-400 mr-2" />
                <span className="text-xs text-slate-500">Subir archivo</span>
                <input type="file" className="hidden" onChange={handleFileChange} accept=".pdf,image/*" />
              </label>
            ) : (
              <div className="flex items-center justify-between w-full h-10 px-3 bg-blue-50 border border-blue-100 rounded-lg">
                <div className="flex items-center truncate">
                  <FileText className="w-4 h-4 text-blue-600 mr-2 shrink-0" />
                  <span className="text-xs text-blue-700 truncate">{file.name}</span>
                </div>
                <button onClick={() => setFile(null)} className="text-blue-400 hover:text-blue-600">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Botones */}
        <div className="pt-4 flex gap-4">
          <button onClick={onBack} className="px-8 py-4 bg-slate-100 text-slate-600 font-bold rounded-xl hover:bg-slate-200">Atrás</button>
          <button 
            onClick={handleSubmit}
            className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 shadow-lg flex items-center justify-center gap-2"
          >
            <span>Corregir Ejercicio</span>
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default MathCorrectionForm;
