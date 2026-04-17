import React from 'react';
import { Target, BookOpen, Rocket, PenTool, History, Map, Zap, LogIn } from 'lucide-react';

// Definimos qué datos necesita recibir este componente
interface WelcomeProps {
  onStart: () => void;
  onViewHistory: () => void;
  onViewCognitiveMap: () => void;
  restantes: number; // Esto viene de tu app.py
}

const Welcome: React.FC<WelcomeProps> = ({ 
  onStart, 
  onViewHistory, 
  onViewCognitiveMap, 
  restantes 
}) => {
  // Verificamos si el usuario tiene acceso (más de 0 consultas)
  const tieneConsultas = restantes > 0;

  return (
    <div className="text-center space-y-8 animate-in fade-in zoom-in-95 duration-700 py-10">
      
      {/* Badge de Créditos Disponibles */}
      <div className="flex justify-center">
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full border shadow-sm transition-all duration-500 ${
          tieneConsultas 
          ? 'bg-emerald-50 border-emerald-100 text-emerald-700' 
          : 'bg-amber-50 border-amber-100 text-amber-700'
        }`}>
          <Zap size={14} className={tieneConsultas ? 'fill-emerald-500' : 'fill-amber-500'} />
          <span className="text-xs font-black uppercase tracking-widest">
            {tieneConsultas ? `${restantes} Entrenamientos disponibles` : 'Identifícate para comenzar'}
          </span>
        </div>
      </div>

      {/* Cabecera Principal */}
      <div className="space-y-4">
        <span className="inline-block px-3 py-1 bg-indigo-50 text-indigo-700 text-sm font-bold rounded-full border border-indigo-100 uppercase tracking-wider">
          Comprensión de Nivel Superior
        </span>
        <h2 className="text-4xl md:text-6xl font-black text-slate-900 leading-tight tracking-tighter">
          Domina los Textos <br />
          <span className="text-indigo-600">Académicos Complejos</span>
        </h2>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Soy tu entrenador personal de lectura universitaria. Mi objetivo es que dejes de "leer" y comiences a 
          <span className="font-bold text-slate-800"> analizar, sintetizar y deconstruir </span> 
          el conocimiento de forma profesional.
        </p>
      </div>

      {/* Grid de Pilares Metodológicos */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto pt-8 px-4">
        {[
          { title: "Riguroso", desc: "Evaluación detallada de cada respuesta.", icon: <Target className="text-indigo-600" size={24}/> },
          { title: "Metódico", desc: "Sigue pasos probados de comprensión lectora.", icon: <BookOpen className="text-indigo-600" size={24}/> },
          { title: "Motivador", desc: "Plan de acción para elevar tu nivel.", icon: <Rocket className="text-indigo-600" size={24}/> }
        ].map((item, i) => (
          <div key={i} className="p-6 bg-white rounded-3xl border border-slate-100 shadow-sm hover:shadow-xl transition-all text-left group">
            <div className="mb-3 p-2 bg-slate-50 w-fit rounded-xl group-hover:bg-indigo-50 transition-colors">
              {item.icon}
            </div>
            <h3 className="font-black text-slate-800 mb-1">{item.title}</h3>
            <p className="text-sm text-slate-500 font-medium">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* Botonera de Acciones */}
      <div className="pt-8 flex flex-col sm:flex-row items-center justify-center gap-4 px-6">
        <button 
          onClick={onStart}
          className={`w-full sm:w-auto px-10 py-5 font-black rounded-2xl shadow-xl transform transition active:scale-95 text-lg flex items-center justify-center gap-3 ${
            tieneConsultas 
            ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200' 
            : 'bg-slate-800 hover:bg-slate-900 text-white shadow-slate-200'
          }`}
        >
          {tieneConsultas ? <PenTool size={22} /> : <LogIn size={22} />}
          {tieneConsultas ? 'Comenzar Entrenamiento' : 'Ingresar con Google'}
        </button>
        
        <div className="flex gap-4 w-full sm:w-auto">
          <button 
            onClick={onViewHistory}
            className="flex-1 sm:flex-none px-6 py-5 bg-white border-2 border-slate-100 text-slate-700 font-bold rounded-2xl hover:bg-slate-50 transition active:scale-95 flex items-center gap-2"
          >
            <History size={20} />
            Historial
          </button>
          <button 
            onClick={onViewCognitiveMap}
            className="flex-1 sm:flex-none px-6 py-5 bg-white border-2 border-slate-100 text-slate-700 font-bold rounded-2xl hover:bg-slate-50 transition active:scale-95 flex items-center gap-2"
          >
            <Map size={20} />
            Mapa
          </button>
        </div>
      </div>

      {/* Créditos Dinámicos (ADN app.py) */}
      <div className="flex flex-col items-center justify-center gap-2">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full animate-pulse ${tieneConsultas ? 'bg-emerald-500' : 'bg-amber-500'}`}></div>
          <p className="text-[10px] text-slate-400 font-black uppercase tracking-[0.2em]">
            Estado del sistema: {tieneConsultas ? 'Operativo' : 'Sesión requerida'}
          </p>
        </div>
        {!tieneConsultas && (
          <p className="text-[9px] text-indigo-500 font-bold uppercase tracking-widest">
            Inicia sesión para recibir tus 4 consultas diarias gratuitas
          </p>
        )}
      </div>
    </div>
  );
};

export default Welcome;