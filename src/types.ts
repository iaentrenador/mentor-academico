// src/types.ts

// 1. Estados de la Aplicación (Añadimos SELECTION para el nuevo menú)
export enum AppState {
  WELCOME = 'WELCOME',
  HISTORY = 'HISTORY',
  COGNITIVE_MAP = 'COGNITIVE_MAP',
  WRITING_CORRECTION_INPUT = 'WRITING_CORRECTION_INPUT',
  ACTIVITY_SELECTION = 'ACTIVITY_SELECTION', // El menú de las tarjetas
  TEXT_DISPLAY = 'TEXT_DISPLAY'               // La pantalla de lectura que me pasaste
}

// 2. Definición del Historial
export interface HistoryEntry {
  id: string;
  date: string;
  type: string; 
  title: string;
  data: any;      
  score?: number; 
  status?: string; 
}

// 3. Definición del Mapa Cognitivo
export interface CognitiveMapData {
  totalExercises: number;
  averageScore: number;
  masteredConcepts: string[];
  weakAreas: string[];
  progressOverTime: { date: string; score: number }[];
  concepts: string[]; 
  connections: any[]; 
  areas: string[];    
  activityDistribution?: any;
}

// 4. NUEVO: Estructura de Texto Universitario
export interface UniversityText {
  id?: string;
  title: string;
  content: string;
  materia: string;
  sourceType: 'manual' | 'pdf' | 'web';
}

// 5. Inputs de Usuario (Evolucionado para soportar más actividades)
export interface WritingCorrectionInput {
  writing: string;
  materia: string;
  activityType?: string; // Para saber si es Rap, Resumen, etc.
}

// 6. Resultados de la IA
export interface WritingCorrectionResult {
  grade: string | number;
  performanceAnalysis: string;
  strengths?: string[];
  weaknesses?: string[];
  improvedVersion?: string;
  status?: string;
  rapLyrics?: string;    // Específico para el modo Rap
  conceptualMap?: any;   // Específico para Redes
}

// 7. Estado General
export interface UserStats {
  logueado: boolean;
  restantes: number;
}
