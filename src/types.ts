 // src/types.ts

// 1. Estados de la Aplicación
export enum AppState {
  WELCOME = 'WELCOME',
  HISTORY = 'HISTORY',
  COGNITIVE_MAP = 'COGNITIVE_MAP',
  WRITING_CORRECTION_INPUT = 'WRITING_CORRECTION_INPUT',
  WRITING_CORRECTION_RESULTS = 'WRITING_CORRECTION_RESULTS', 
  ACTIVITY_SELECTION = 'ACTIVITY_SELECTION', 
  TEXT_DISPLAY = 'TEXT_DISPLAY',
  CONCEPTUAL_NETWORK_RESULTS = 'CONCEPTUAL_NETWORK_RESULTS', // <--- ESTADO AGREGADO
  // Estados para el Módulo de Resúmenes
  SUMMARY_SELECTION = 'SUMMARY_SELECTION',
  SUMMARY_GENERATION_INPUT = 'SUMMARY_GENERATION_INPUT',
  SUMMARY_CORRECTION_INPUT = 'SUMMARY_CORRECTION_INPUT',
  SUMMARY_GENERATION_RESULTS = 'SUMMARY_GENERATION_RESULTS',
  SUMMARY_CORRECTION_RESULTS = 'SUMMARY_CORRECTION_RESULTS',
  // --- NUEVOS ESTADOS MÓDULO MATEMÁTICAS ---
  MATH_SELECTION = 'MATH_SELECTION',
  MATH_EXPLAINER_INPUT = 'MATH_EXPLAINER_INPUT',
  MATH_EXPLAINER_RESULTS = 'MATH_EXPLAINER_RESULTS',
  MATH_CORRECTION_INPUT = 'MATH_CORRECTION_INPUT',
  MATH_CORRECTION_RESULTS = 'MATH_CORRECTION_RESULTS',
  // --- NUEVOS ESTADOS SIMULACRO DE EXAMEN ---
  EXAM_INPUT = 'EXAM_INPUT',
  EXAM_TAKING = 'EXAM_TAKING',
  EXAM_RESULTS = 'EXAM_RESULTS',
  // --- ESTADOS EXPLICADOR DE CONCEPTOS ---
  CONCEPT_EXPLAINER_INPUT = 'CONCEPT_EXPLAINER_INPUT',
  CONCEPT_EXPLAINER_RESULTS = 'CONCEPT_EXPLAINER_RESULTS'
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

// 4. Estructura de Texto Universitario
export interface UniversityText {
  id?: string;
  title: string;
  content: string;
  materia: string;
  sourceType: 'manual' | 'pdf' | 'web'; 
}

// 5. Inputs de Usuario
export interface WritingCorrectionInput {
  writing: string;       
  prompt: string;        
  sourceText?: string;   
  materia: string;
  activityType: string;  
  activityTitle: string; 
  query?: string;        
}

// 6. Resultados de la IA
export interface SectionEvaluation {
  score: number;
  feedback: string;
}

export interface WritingCorrectionResult {
  grade: number;
  status: string;
  performanceAnalysis: string;
  strengths: string[];
  weaknesses: string[];
  improvementSuggestions: string[];
  improvedVersion?: string;
  suggestedRetry?: string;
  criteria?: {
    understanding: SectionEvaluation;
    promptAdequacy: SectionEvaluation;
    coherence: SectionEvaluation;
    vocabulary: SectionEvaluation;
    fundamentation: SectionEvaluation;
  };
  qualitative?: {
    strengths: string[];
    weaknesses: string[];
    conceptualErrors: string[];
  };
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
  status: 'Excelente' | 'Satisfactorio' | 'Insúficiente';
  performanceAnalysis: string;
  strengths: string[];
  weaknesses: string[];
  omissions: string[];
  improvementSuggestions: string[];
  suggestedRetry: string;
  improvedVersion: string;
}

// 6.3 Interfaz para el resultado de Red Conceptual
export interface ConceptualNode {
  id: string;
  label: string;
  type: 'core' | 'main' | 'secondary';
}

export interface ConceptualEdge {
  from: string;
  to: string;
  label: string;
}

export interface ConceptualNetworkResult {
  title: string;
  summary: string;
  nodes: ConceptualNode[];
  edges: ConceptualEdge[];
}

// --- 6.4 INTERFACES MÓDULO MATEMÁTICAS ---

export interface MathExplainerInput {
  topic: string;
  specificExercise: string;
}

export interface MathExplainerResult {
  theoreticalContext: string;
  similarExample: {
    problem: string;
    solutionSteps: string[];
    finalResult: string;
    explanation: string;
  };
  keyFormulas: string[];
  tips: string[];
}

export interface MathCorrectionInput {
  exercisePrompt: string;
  studentAnswer: string;
  referenceMaterial?: string;
  referenceFile?: { base64: string; mimeType: string };
}

export interface MathCorrectionResult {
  grade: number;
  status: 'Excelente' | 'Satisfactorio' | 'Insuficiente' | 'Aprobado' | 'No aprobado';
  performanceAnalysis: string;
  stepByStepCorrection: {
    step: string;
    isCorrect: boolean;
    feedback: string;
    correction?: string;
  }[];
  conceptualErrors: string[];
  finalVerdict: string;
  improvementSuggestions: string[];
}

// --- 6.5 INTERFACES SIMULACRO DE EXAMEN ---

export type ExamQuestionType = 'multiple-choice' | 'development' | 'justification';

export interface ExamQuestion {
  id: string;
  question: string;
  type: ExamQuestionType;
  options?: string[]; 
}

export interface ExamData {
  questions: ExamQuestion[];
}

export interface ExamEvaluation {
  grade: number;
  status: string;
  totalScore: number;
  maxScore: number;
  performanceAnalysis: string;
  suggestedRetry: string;
  questionEvaluations: {
    questionId: string;
    isCorrect: boolean;
    score: number;
    feedback: string;
  }[];
}

// 7. Estado General
export interface UserStats {
  logueado: boolean;
  restantes: number;
}
