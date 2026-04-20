import React, { useState } from 'react';
import { BookOpen, HelpCircle, Send, ArrowLeft } from 'lucide-react';

interface ConceptExplainerInputViewProps {
  onSubmit: (text: string, question: string, isLawyerMode: boolean) => void;
  onBack: () => void;
  initialText?: string;
  initialIsLawyerMode?: boolean;
}

const ConceptExplainerInputView: React.FC<ConceptExplainerInputViewProps> = ({ 
  onSubmit, 
  onBack, 
  initialText = '',
  initialIsLawyerMode = false
}) => {
  const [text, setText] = useState(initialText);
  const [question, setQuestion] = useState('');
  const [isLawyerMode, setIsLawyerMode] = useState(initialIsLawyerMode);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && question.trim()) {
      onSubmit(text, question, isLawyerMode);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-3xl mx-auto">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600 shadow-sm">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-800 tracking-tighter uppercase italic">Explicador de Conceptos</h2>
            <p className="text-slate-500 text-sm font-medium">Resolvé tus dudas con ejemplos claros</p>
          </div>
        </div>
        <button 
          onClick={onBack}
          className="p-2 text-slate-400 hover:text-indigo-600 transition-colors"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
      </div>

      {/* NOTA DE ADVERTENCIA */}
      <div className="bg-amber-50 border border-amber-200 p-4 rounded-2xl flex items-start gap-3 shadow-sm shadow-amber-100/50">
        <HelpCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <p className="text-sm text-amber-800 leading-relaxed">
          <strong className="font-black uppercase text-[10px] block mb-1">Importante:</strong> 
          Si pegás una consigna, el Mentor no la resolverá por vos. Te explicará los conceptos y dará ejemplos similares para que lo resuelvas solo.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white p-6 rounded-[2rem] border border-slate-200 shadow-xl shadow-slate-100/40 space-y-4">
          {/* ÁREA DE TEXTO: CONTEXTO */}
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1 flex items-center gap-2">
              <BookOpen className="w-3 h-3 text-indigo-500" />
              Texto o Tema de Estudio
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Pegá aquí el fragmento del apunte o describí el tema..."
              className="w-full h-40 p-5 bg-slate-50 border-2 border-slate-100 rounded-[1.5rem] focus:ring-0 focus:border-indigo-500 outline-none transition-all text-slate-700 resize-none font-medium text-sm"
              required
            />
          </div>

          {/* INPUT: PREGUNTA */}
          <div>
            <label className="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 ml-1 flex items-center gap-2">
              <HelpCircle className="w-3 h-3 text-indigo-500" />
              ¿Qué necesitás comprender?
            </label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ej: ¿Qué significa este riesgo en el contexto legal?"
              className="w-full p-5 bg-slate-50 border-2 border-slate-100 rounded-[1.2rem] focus:ring-0 focus:border-indigo-500 outline-none transition-all text-slate-700 font-medium text-sm"
              required
            />
          </div>

          {/* TOGGLE MODO ESPECIALIZADO */}
          <div className="flex items-center gap-3 p-4 bg-slate-50 border border-slate-200 rounded-[1.2rem] mt-4">
            <div className="flex-1">
              <p className="text-xs font-black text-slate-800 uppercase tracking-tight">Modo Normativo Especializado</p>
              <p className="text-[10px] text-slate-500 font-bold uppercase">Aplica legislación y planes de estudio específicos</p>
            </div>
            <button 
              type="button"
              onClick={() => setIsLawyerMode(!isLawyerMode)}
              className={`w-12 h-6 rounded-full transition-colors relative flex items-center ${isLawyerMode ? 'bg-indigo-600' : 'bg-slate-300'}`}
            >
              <div className={`absolute w-4 h-4 bg-white rounded-full transition-all shadow-sm ${isLawyerMode ? 'left-7' : 'left-1'}`}></div>
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={!text.trim() || !question.trim()}
          className="w-full py-5 bg-indigo-600 text-white rounded-[1.5rem] font-black uppercase tracking-[0.2em] text-xs shadow-xl shadow-indigo-100 hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center justify-center gap-3"
        >
          <Send className="w-4 h-4" />
          SOLICITAR EXPLICACIÓN
        </button>
      </form>
    </div>
  );
};

export default ConceptExplainerInputView;
