import React, { useState } from 'react';
import { AppState, WritingCorrectionInput } from './types';
import { Layout, BookOpen, PenTool, History, ChevronLeft } from 'lucide-react';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>(AppState.WELCOME);
  const [writingInput, setWritingInput] = useState<WritingCorrectionInput>({
    writing: '',
    materia: 'higiene'
  });

  // Función para volver al inicio
  const goBack = () => setState(AppState.WELCOME);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* NAVBAR DINÁMICA: Cambia según donde estés */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-indigo-600 rounded flex items-center justify-center text-white font-bold">M</div>
          <h1 className="font-bold text-slate-800 text-lg tracking-tight">Mentor IA</h1>
        </div>
        {state !== AppState.WELCOME && (
          <button 
            onClick={goBack}
            className="flex items-center gap-1 text-slate-500 hover:text-indigo-600 transition-colors text-sm font-medium"
          >
            <ChevronLeft size={18} /> Volver al Inicio
          </button>
        )}
      </header>

      {/* CONTENEDOR PRINCIPAL: Aquí es donde ocurre la magia */}
      <main className="flex-1 flex flex-col w-full max-w-7xl mx-auto overflow-hidden">
        
        {/* PANTALLA 1: BIENVENIDA (Dashboard Estilo Google) */}
        {state === AppState.WELCOME && (
          <div className="p-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
            <div className="col-span-full mb-4">
              <h2 className="text-2xl font-bold text-slate-800">¿Qué vamos a entrenar hoy, Seba?</h2>
              <p className="text-slate-500">Selecciona una herramienta para comenzar.</p>
            </div>
            
            <button 
              onClick={() => setState(AppState.WRITING_CORRECTION_INPUT)}
              className="bg-white p-6 rounded-xl border border-slate-200 hover:border-indigo-500 hover:shadow-lg transition-all text-left group"
            >
              <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center text-indigo-600 mb-4 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                <PenTool size={24} />
              </div>
              <h3 className="font-bold text-slate-800 text-lg">Corrección de Escritos</h3>
              <p className="text-sm text-slate-500 mt-2">Evaluación de informes de Higiene, Seguridad y Política con rigor académico.</p>
            </button>

            {/* Agregaremos más botones aquí luego... */}
          </div>
        )}

        {/* PANTALLA 2: ESCRITURA (INTERFAZ ANCHA Y LIMPIA) */}
        {state === AppState.WRITING_CORRECTION_INPUT && (
          <div className="flex-1 flex flex-col p-6 animate-fade-in h-full">
            <div className="mb-4">
              <h2 className="text-xl font-bold text-slate-800">Área de Redacción Académica</h2>
              <p className="text-sm text-slate-500">Escribe o pega tu informe completo aquí abajo.</p>
            </div>
            
            {/* ESTE ES EL CUADRO GIGANTE: Ocupa todo el espacio disponible */}
            <textarea 
              className="flex-1 w-full p-6 text-lg border-2 border-slate-200 rounded-2xl focus:border-indigo-500 focus:ring-0 resize-none shadow-inner bg-white"
              placeholder="Empieza a escribir..."
              value={writingInput.writing}
              onChange={(e) => setWritingInput({...writingInput, writing: e.target.value})}
            />

            <div className="mt-6 flex justify-end gap-4">
              <select className="bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm font-medium outline-none">
                <option value="higiene">Higiene y Seguridad</option>
                <option value="politica">Política</option>
                <option value="alfabetizacion">Alfabetización</option>
              </select>
              <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-2 rounded-lg font-bold transition-colors shadow-md">
                Enviar a Evaluación
              </button>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default App;
