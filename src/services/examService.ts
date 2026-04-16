import { ExamData, ExamEvaluation, ExamQuestionType } from '../types';

export const examService = {
  /**
   * Genera las preguntas del examen enviando el material de estudio al backend.
   */
  generateExam: async (
    material: string, 
    count: number, 
    types: ExamQuestionType[],
    profile: string = "UPE_Seguridad_Higiene"
  ): Promise<ExamData> => {
    const response = await fetch('/api/exam/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ material, count, types, profile })
    });

    if (!response.ok) {
      // Si el servidor responde 403, lanzamos un error específico que App.tsx sepa leer
      if (response.status === 403) {
        throw new Error('CREDITS_EXHAUSTED');
      }
      const errorData = await response.json();
      throw new Error(errorData.error || 'Error al generar el examen');
    }

    const data = await response.json();
    return data.resultado;
  },

  /**
   * Envía las respuestas del usuario para ser evaluadas por la IA.
   */
  evaluateExam: async (
    answers: Record<string, string>, 
    material: string
  ): Promise<ExamEvaluation> => {
    const response = await fetch('/api/exam/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers, material })
    });

    if (!response.ok) {
      // También validamos créditos aquí por seguridad
      if (response.status === 403) {
        throw new Error('CREDITS_EXHAUSTED');
      }
      const errorData = await response.json();
      throw new Error(errorData.error || 'Error al evaluar el examen');
    }

    const data = await response.json();
    return data.resultado;
  }
};
