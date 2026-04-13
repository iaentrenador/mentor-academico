import React, { useState } from 'react';
import { Send, BookOpen, AlertCircle, ChevronLeft, Info } from 'lucide-react';

interface DataEntryViewProps {
  activityId: string;
  activityTitle: string;
  onBack: () => void;
  onSubmit: (data: { text: string; query?: string; profile: string }) => void;
  loading: boolean;
}

const DataEntryView: React.FC<DataEntryViewProps> = ({ 
  activityId, 
  activityTitle, 
  onBack, 
  onSubmit,
  loading 
}) => {
  const [text, setText] = useState('');
  const [query, setQuery] = useState('');
  const [profile, setProfile] = useState('higiene_upe');

  const isExplainer = activityId === 'EXPLAINER';
  const charLimit = 15000;

  const handleSubmit = () => {
    if (!text.trim()) return;
    // Si es explicador, validamos que haya una pregunta
    if (isExplainer && !query.trim()) return;
    
    onSubmit({ text, query, profile });
  };

  return (
    <div className="flex-1 flex flex-col gap-6 animate-in slide-in-from-bottom-4 duration-500 max-w-5xl mx-auto w-full pb-10">
      
      {/* Encabezado */}
      <div className="flex justify-between items-center border-b-2 border-slate-100 pb-4">
        <div className="flex items-center gap-4">
          <button 
            onClick={onBack} 
            className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400"
          >
            <ChevronLeft size={28} />
          </button>
          <div>
            <h3 className="text-2xl font-black text-slate-800 uppercase italic tracking-tighter leading-none">
              {activityTitle}
            </h3>
            <span className="text-[10px] font-black text-indigo-500 uppercase tracking-[0.2em]">Configuración de Entrada</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Lado Izquierdo: El Texto de Estudio (Principal) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-white rounded-[2.5rem] p-1 border-2 border-slate-100 shadow-sm focus-within:border-indigo-500 transition-all">
            <div className="flex items-center gap-2 px-6 pt-4 text-slate-400">
              <BookOpen size={16} />
              <span className="text-[10px] font-black uppercase tracking-widest">Material de Cátedra</span>
            </div>
            <textarea 
              className="w-full h-96 p-6 text-lg text-slate-700 outline-none bg-transparent resize-none font-medium leading-relaxed"
              placeholder="Pega aquí el contenido que estás leyendo..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="px-6 pb-4 flex justify-between items-center">
              <div className="flex gap-2">
                 <div className={`h-1.5 w-1.5 rounded-full ${text.length > charLimit * 0.9 ? 'bg-rose-500' : 'bg-emerald-500'}`} />
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                   {text.length.toLocaleString()} / {charLimit.toLocaleString()} chars
                 </span>
              </div>
            </div>
          </div>

          {/* Input extra solo para el Explicador */}
          {isExplainer && (
            <div className="bg-indigo-50/50 rounded-3xl p-6 border-2 border-indigo-100 space-y-3 animate-in fade-in zoom-in-95 duration-300">
              <div className="flex items-center gap-2 text-indigo-600">
                <Info size={16} />
                <label className="text-[10px] font-black uppercase tracking-[0.15em]">¿Qué duda específica tenés?</label>
              </div>
              <input 
                type="text"
                className="w-full p-4 bg-white border-2 border-indigo-200 rounded-2xl outline-none focus:border-indigo-600 font-bold text-slate-800 placeholder:text-slate-300 transition-all"
                placeholder="Ej: No entiendo cómo se relaciona la Ley 19.587 con este párrafo..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          )}
        </div>

        {/* Lado Derecho: Controles y Perfiles */}
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-[2rem] border-2 border-slate-100 shadow-sm">
            <h4 className="font-black text-slate-800 text-[10px] uppercase mb-4 tracking-widest flex items-center gap-2">
              <div className="w-2 h-2 bg-indigo-500 rounded-full" /> Perfil de Cátedra
            </h4>
            
            <div className="grid grid-cols-1 gap-2">
              {[
                { id: 'higiene_upe', label: 'Seguridad e Higiene (UPE)', color: 'bg-emerald-500' },
                { id: 'politica_upe', label: 'Política y Sociedad (UPE)', color: 'bg-blue-500' },
                { id: 'alfabetizacion_upe', label: 'Alfabetización (UPE)', color: 'bg-orange-500' },
                { id: 'abogacia_unlz', label: 'Abogacía (UNLZ)', color: 'bg-rose-500' }
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => setProfile(p.id)}
                  className={`relative p-3 rounded-xl border-2 text-left text-[11px] font-black transition-all overflow-hidden ${
                    profile === p.id 
                    ? 'border-slate-800 bg-slate-800 text-white shadow-lg' 
                    : 'border-slate-50 bg-slate-50 text-slate-400 hover:border-slate-200'
                  }`}
                >
                  <div className={`absolute left-0 top-0 bottom-0 w-1 ${p.color}`} />
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-amber-50 p-4 rounded-2xl border border-amber-100 flex gap-3">
            <AlertCircle className="text-amber-500 shrink-0" size={18} />
            <p className="text-[9px] text-amber-800 font-bold leading-tight uppercase tracking-tight">
              Asegúrate de copiar el texto lo más limpio posible para evitar errores.
            </p>
          </div>

          <button 
            onClick={handleSubmit}
            disabled={loading || !text.trim() || (isExplainer && !query.trim())}
            className="group w-full bg-indigo-600 hover:bg-slate-900 text-white py-5 rounded-[2rem] font-black transition-all shadow-xl shadow-indigo-200 flex items-center justify-center gap-3 uppercase tracking-widest italic disabled:opacity-30 disabled:grayscale active:scale-95"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Procesando...
              </span>
            ) : (
              <>
                Analizar Material
                <Send size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataEntryView;
