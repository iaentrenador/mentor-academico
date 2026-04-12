import React from 'react';
import { 
  FileText, 
  Lightbulb, 
  AlignLeft, 
  Share2, 
  FileCheck, 
  Mic2, 
  Binary, 
  ClipboardCheck, 
  Zap, 
  Globe, 
  Type 
} from 'lucide-react';

interface Activity {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  badge?: string;
}

interface ActivitySelectionProps {
  onSelect: (activityId: string) => void;
}

const activities: Activity[] = [
  { id: 'PDF', title: 'Analizar PDF / Word', description: 'Sube tus apuntes para evaluación de cátedra.', icon: <FileText />, color: 'text-blue-600 bg-blue-50' },
  { id: 'EXPLAINER', title: 'Explicador de Conceptos', description: 'Dudas específicas con ejemplos didácticos.', icon: <Lightbulb />, color: 'text-amber-600 bg-amber-50' },
  { id: 'SUMMARY', title: 'Gestión de Resúmenes', description: 'Genera o corrige resúmenes profesionales.', icon: <AlignLeft />, color: 'text-emerald-600 bg-emerald-50' },
  { id: 'NETWORK', title: 'Red Conceptual', description: 'Visualiza relaciones jerárquicas al instante.', icon: <Share2 />, color: 'text-indigo-600 bg-indigo-50' },
  { id: 'CORRECTION', title: 'Corregir Escrito', description: 'Evaluación de ensayos con rigor académico.', icon: <FileCheck />, color: 'text-rose-600 bg-rose-50' },
  { id: 'RAP', title: 'Rap Técnico Académico', description: 'Mnemotecnia auditiva: rimas memorables.', icon: <Mic2 />, color: 'text-slate-900 bg-slate-100' },
  { id: 'MATH', title: 'Módulo de Matemáticas', description: 'Corrección y explicaciones de ejercicios.', icon: <Binary />, color: 'text-cyan-600 bg-cyan-50' },
  { id: 'EXAM', title: 'Examen Parcial', description: 'Simulacro personalizado (Choice/Desarrollo).', icon: <ClipboardCheck />, color: 'text-purple-600 bg-purple-50' },
  { id: 'MASTER', title: 'Sintetizador Maestro', description: 'Resumen y Red en un solo paso.', icon: <Zap />, color: 'text-orange-600 bg-orange-50', badge: 'NUEVO' },
  { id: 'CHALLENGE', title: 'Desafío Aleatorio', description: 'Investigación web y texto complejo original.', icon: <Globe />, color: 'text-sky-600 bg-sky-50' },
  { id: 'MANUAL', title: 'Pegar Texto Manual', description: 'Analiza contenido del portapapeles.', icon: <Type />, color: 'text-slate-600 bg-slate-100' },
];

const ActivitySelection: React.FC<ActivitySelectionProps> = ({ onSelect }) => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-2">
        <h2 className="text-4xl font-black text-slate-900 tracking-tighter uppercase italic">
          Selección de <span className="text-indigo-600">Actividad</span>
        </h2>
        <p className="text-slate-500 font-bold uppercase text-[10px] tracking-[0.2em]">
          ¿Qué material analizaremos hoy?
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {activities.map((activity) => (
          <button
            key={activity.id}
            onClick={() => onSelect(activity.id)}
            className="group relative bg-white p-6 rounded-[2rem] border-2 border-slate-100 hover:border-indigo-600 transition-all duration-300 shadow-sm hover:shadow-xl text-left active:scale-95 overflow-hidden"
          >
            {activity.badge && (
              <span className="absolute top-4 right-4 bg-orange-500 text-white text-[8px] font-black px-2 py-1 rounded-full animate-pulse">
                {activity.badge}
              </span>
            )}
            
            <div className={`w-12 h-12 ${activity.color} rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              {React.cloneElement(activity.icon as React.ReactElement, { size: 24 })}
            </div>
            
            <h3 className="font-black text-slate-800 uppercase text-sm tracking-tight mb-1 group-hover:text-indigo-600 transition-colors">
              {activity.title}
            </h3>
            <p className="text-slate-500 text-xs font-medium leading-relaxed">
              {activity.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ActivitySelection;
