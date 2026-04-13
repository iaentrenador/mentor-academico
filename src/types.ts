// src/types.ts

// 1. Estados de la Aplicación
export enum AppState {
  WELCOME = 'WELCOME',
  HISTORY = 'HISTORY',
  COGNITIVE_MAP = 'COGNITIVE_MAP',
  WRITING_CORRECTION_INPUT = 'WRITING_CORRECTION_INPUT',
  ACTIVITY_SELECTION = 'ACTIVITY_SELECTION', 
  TEXT_DISPLAY = 'TEXT_DISPLAY',
  // Nuevos estados para el Módulo de Resúmenes
  SUMMARY_SELECTION = 'SUMMARY_SELECTION',
  SUMMARY_GENERATION_INPUT = 'SUMMARY_GENERATION_INPUT',
  SUMMARY_CORRECTION_INPUT = 'SUMMARY_CORRECTION_INPUT',
  SUMMARY_GENERATION_RESULTS = 'SUMMARY_GENERATION_RESULTS',
  SUMMARY_CORRECTION_RESULTS = 'SUMMARY_CORRECTION_RESULTS'
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

// 5. Inputs de Usuario (CORREGIDO: activityType y activityTitle son obligatorios)
export interface WritingCorrectionInput {
  writing: string;
  materia: string;
  activityType: string;  
  activityTitle: string; 
  query?: string;        
}

// 6. Resultados de la IA
export interface WritingCorrectionResult {
  grade: string | number;
  performanceAnalysis: string;
  strengths?: string[];
  weaknesses?: string[];
  improvedVersion?: string;
  status?: string;
  rapLyrics?: string;    
  conceptualMap?: any;   
}

// 6.1 Interfaz para el resultado de Generación Automática de Resúmenes
export interface SummaryGenerationResult {
  title: string;
  executiveSummary: string;
  keyConcepts: { concept: string; definition: string }[];
  conclusions: string;
}

// 6.2 Interfaz para el resultado de Corrección de Resúmenes
export interface SummaryCorrectionResult {
  grade: number;
  status: 'Excelente' | 'Satisfactorio' | 'Insuficiente';
  performanceAnalysis: string;
  strengths: string[];
  weaknesses: string[];
  omissions: string[];
  improvementSuggestions: string[];
  suggestedRetry: string;
  improvedVersion: string;
}

// 7. Estado General
export interface UserStats {
  logueado: boolean;
  restantes: number;
}
