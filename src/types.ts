// src/types.ts

// 1. Estados de la Aplicación
export enum AppState {
  WELCOME = 'WELCOME',
  HISTORY = 'HISTORY',
  COGNITIVE_MAP = 'COGNITIVE_MAP',
  WRITING_CORRECTION_INPUT = 'WRITING_CORRECTION_INPUT'
}

// 2. Definición del Historial (Corrige errores en App y HistoryView)
export interface HistoryEntry {
  id: string;
  date: string;
  type: string;
  title: string;
  data: any;      // Esta es la propiedad que te falta en App.tsx(48,7)
  score?: number; // Esta es la que falta en App.tsx(58,47) y HistoryView
  status?: string; // Para HistoryView.tsx(116,25)
}

// 3. Definición del Mapa Cognitivo (Corrige TODOS los errores en CognitiveMapView)
export interface CognitiveMapData {
  totalExercises: number;
  averageScore: number;
  masteredConcepts: string[];
  weakAreas: string[];
  progressOverTime: { date: string; score: number }[];
  concepts: string[]; // Por compatibilidad
  connections: any[]; // Por compatibilidad
  areas: string[];    // Por compatibilidad
  activityDistribution?: any;
}

// 4. Inputs de Usuario
export interface WritingCorrectionInput {
  writing: string;
  materia: 'higiene' | 'politica' | 'alfabetizacion' | string;
}

// 5. Resultados de la IA
export interface WritingCorrectionResult {
  grade: number;
  performanceAnalysis: string;
  strengths: string[];
  weaknesses: string[];
  improvedVersion: string;
  status: string;
}

// 6. Estado General
export interface UserStats {
  logueado: boolean;
  restantes: number;
}
