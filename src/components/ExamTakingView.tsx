import React, { useState } from 'react';
import { ExamQuestion, ExamData } from '../types';

interface ExamTakingViewProps {
  examData: ExamData;
  onSubmit: (answers: Record<string, string>) => void;
  isLoading: boolean;
}

const ExamTakingView: React.FC<ExamTakingViewProps> = ({ examData, onSubmit, isLoading }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const currentQuestion = examData.questions[currentIndex];
  const totalQuestions = examData.questions.length;
  const progress = ((currentIndex + 1) / totalQuestions) * 100;

  const handleAnswerChange = (value: string) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
  };

  const handleNext = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const isLastQuestion = currentIndex === totalQuestions - 1;
  const allAnswered = Object.keys(answers).length === totalQuestions;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header & Progress */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-slate-500">
            Pregunta {currentIndex + 1} de {totalQuestions}
          </span>
          <span className="text-sm font-bold text-indigo-600">
            {Math.round(progress)}% completado
          </span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div 
            className="bg-indigo-600 h-full transition-all duration-300" 
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 min-h-[400px] flex flex-col">
        <div className="mb-6">
          <span className="inline-block px-3 py-1 bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase tracking-wider rounded-lg mb-4">
            {currentQuestion.type.replace('-', ' ')}
          </span>
          <h3 className="text-xl font-semibold text-slate-800 leading-snug">
            {currentQuestion.question}
          </h3>
        </div>

        <div className="flex-grow">
          {currentQuestion.type === 'multiple-choice' ? (
            <div className="space-y-3">
              {currentQuestion.options?.map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAnswerChange(option)}
                  className={`w-full p-4 text-left rounded-xl border transition-all ${
                    answers[currentQuestion.id] === option
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-800 ring-1 ring-indigo-600'
                      : 'border-slate-200 hover:border-slate-300 text-slate-600'
                  }`}
                >
                  <span className="font-bold mr-3">{String.fromCharCode(65 + idx)})</span>
                  {option}
                </button>
              ))}
            </div>
          ) : (
            <textarea
              className="w-full h-48 p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              placeholder="Escribe tu respuesta fundamentada aquí..."
              value={answers[currentQuestion.id] || ''}
              onChange={(e) => handleAnswerChange(e.target.value)}
            />
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t border-slate-100">
          <button
            onClick={handlePrev}
            disabled={currentIndex === 0}
            className="px-6 py-2 font-medium text-slate-400 hover:text-slate-600 disabled:opacity-0 transition-all"
          >
            Anterior
          </button>
          
          {isLastQuestion ? (
            <button
              onClick={() => onSubmit(answers)}
              disabled={!allAnswered || isLoading}
              className={`px-8 py-3 rounded-xl font-bold text-white shadow-lg transition-all ${
                allAnswered && !isLoading 
                ? 'bg-emerald-600 hover:bg-emerald-700 hover:scale-105' 
                : 'bg-slate-300 cursor-not-allowed'
              }`}
            >
              {isLoading ? 'Corrigiendo...' : 'Finalizar Examen'}
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-8 py-3 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold transition-all"
            >
              Siguiente
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExamTakingView;
