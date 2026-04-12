// src/types.ts

export interface StudentAnswers {
  mainIdeas: string;
  summary: string;
  schema: string;
  inferences: { a: string; b: string; c: string };
  vocabulary: string;
  opinion: string;
}

export interface FullEvaluation {
  grade: number;
  performanceAnalysis: string;
  strengths: string[];
  weaknesses: string[];
  improvementSuggestions: string[];
  suggestedRetry: string;
  sections: Record<string, any>;
  finalGrade?: number;
}

export interface HistoryEntry {
  id: string;
  date: string;
  title: string;
  type: string;
  grade?: number;
}

export interface CognitiveMapData {
  concepts: string[];
  connections: { from: string; to: string; label: string }[];
  areas: string[];
}

export interface WritingCorrectionResult {
  grade: number;
  status: string;
  performanceAnalysis: string;
  strengths: string[];
  weaknesses: string[];
  improvedVersion: string;
}

export interface TechnicalRapResult {
  title: string;
  verses: string[];
  evaluation: any;
}

export interface SummaryCorrectionResult {
  grade: number;
  performanceAnalysis: string;
  omissions: string[];
  improvedVersion: string;
}
