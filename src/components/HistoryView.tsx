import React from 'react';
import { HistoryEntry } from '../types';
import { 
  Clock, 
  CheckCircle, 
  FileText, 
  Music, 
  Share2, 
  HelpCircle, 
  AlertCircle,
  ChevronRight,
  RotateCcw
} from 'lucide-react';

interface HistoryViewProps {
  history: HistoryEntry[];
  onBack: () => void;
  onViewItem: (item: HistoryEntry) => void;
}

const HistoryView: React.FC<HistoryViewProps> = ({ history, onBack, onViewItem }) => {
  
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'EVALUATION': return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case 'CORRECTION': return <FileText className="w-5 h-5 text-indigo-500" />;
      case 'TECHNICAL_RAP': return <Music className="w-5 h-5 text-purple-500" />;
      case 'CONCEPTUAL_NETWORK': return <Share2 className="w-5 h-5 text-blue-500" />;
      case 'CONCEPT_EXPLAINER': return <HelpCircle className="w-5 h-5 text-amber-500" />;
      default: return <AlertCircle className="w-5 h-5 text-slate-400" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'EVALUATION': return 'Evaluación de Comprensión';
      case 'CORRECTION': return 'Corrección de Escritura';
      case 'PDF_EVALUATION': return 'Actividad de PDF';
      case 'SUMMARY_CORRECTION': return 'Corrección de Resumen';
      case 'TECHNICAL_RAP': return 'Rap Técnico';
      case 'CONCEPTUAL_NETWORK': return 'Red Conceptual';
      case 'CONCEPT_EXPLAINER': return 'Explicación de Concepto';
      default: return 'Actividad General';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
      
      {/* Encabezado del Historial */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-4xl font-black text-slate-900 tracking-tighter uppercase italic">
            Historial de <span className="text-indigo-600">Entrenamiento</span>
          </h2>
          <p className="text-slate-500 font-bold uppercase text-[10px] tracking-[0.2em] mt-1">
            Registro de tu evolución académica profesional
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

      {history.length === 0 ? (
        <div className="bg-white border-2 border-dashed border-slate-200 rounded-[2.5rem] p-16 text-center">
          <div className="w-20 h-20 bg-slate-50 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-inner">
            <Clock className="w-10 h-10 text-slate-300" />
          </div>
          <h3 className="text-2xl font-black text-slate-800 mb-2">Sin registros todavía</h3>
          <p className="text-slate-500 font-medium max-w-sm mx-auto">
            Tus ejercicios aparecerán aquí una vez que el Mentor evalúe tu primer informe técnico.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {history.slice().reverse().map((item) => (
            <div 
              key={item.id} 
              className="group bg-white border-2 border-slate-100 rounded-3xl p-6 hover:border-indigo-600 hover:shadow-2xl hover:shadow-indigo-100 transition-all cursor-pointer flex items-center gap-6"
              onClick={() => onViewItem(item)}
            >
              {/* Icono de Tipo con fondo dinámico */}
              <div className="hidden sm:flex w-14 h-14 bg-slate-50 rounded-2xl items-center justify-center group-hover:bg-indigo-50 transition-colors shadow-inner">
                {getTypeIcon(item.type)}
              </div>

              {/* Info de la Entrada */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-black text-indigo-600 uppercase tracking-widest bg-indigo-50 px-2 py-0.5 rounded">
                    {getTypeLabel(item.type)}
                  </span>
                  <span className="text-[10px] text-slate-400 font-bold uppercase">
                    • {new Date(item.date).toLocaleDateString()}
                  </span>
                </div>
                <h4 className="text-xl font-black text-slate-800 truncate leading-tight group-hover:text-indigo-600 transition-colors uppercase italic">
                  {item.title}
                </h4>
                
                {/* Score y Meta-info */}
                <div className="flex items-center gap-4 mt-2">
                  {item.score !== undefined && (
                    <div className="px-3 py-1 bg-slate-900 rounded-lg">
                      <span className="text-[10px] text-slate-400 font-bold uppercase mr-2">Puntaje</span>
                      <span className={`text-xs font-black ${item.score >= 7 ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {item.score.toFixed(1)}/10
                      </span>
                    </div>
                  )}
                  {item.status && (
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                      [{item.status}]
                    </span>
                  )}
                </div>
              </div>

              {/* Indicador de flecha */}
              <div className="text-slate-200 group-hover:text-indigo-600 transition-colors">
                <ChevronRight size={32} strokeWidth={3} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryView;
