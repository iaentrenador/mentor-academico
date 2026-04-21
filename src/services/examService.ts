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
      credentials: 'include', // Asegura el envío de cookies de sesión
      body: JSON.stringify({ material, count, types, profile })
    });

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('CREDITS_EXHAUSTED');
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Error al generar el examen');
    }

    const data = await response.json();
    
    // Sincronización: El backend devuelve directamente el objeto con { preguntas: [...] }
    // Si no existe 'questions' o 'preguntas', devolvemos el objeto completo para evitar undefined.
    return data.questions ? data : { questions: data.preguntas || [] };
  },

  /**
   * Envía las respuestas del usuario para ser evaluadas por la IA.
   */
  evaluateExam: async (
    answers: Record<string, string>, 
    material: string
  ): Promise<ExamEvaluation> => {
    const response = await fetch('/api/corregir_escrito', { // Usamos la ruta disponible en app.py para evaluación
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Asegura el envío de cookies de sesión
      body: JSON.stringify({ writing: JSON.stringify(answers), sourceText: material, activityType: 'EXAM' })
    });

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('CREDITS_EXHAUSTED');
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Error al evaluar el examen');
    }

    const data = await response.json();
    
    // Sincronización: Si el backend envuelve el resultado en 'resultado', lo extraemos.
    return data.resultado || data;
  }
};
