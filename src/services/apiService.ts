// src/services/apiService.ts
import { 
  StudentAnswers, 
  FullEvaluation, 
  WritingCorrectionResult,
  TechnicalRapResult,
  SummaryCorrectionResult
} from "../types";

// En Render, la URL base suele ser relativa si el frontend y backend conviven, 
// o la URL de tu servicio.
const API_BASE = "/api";

export const apiService = {
  /**
   * Envía un escrito para corrección académica (Modo Higiene/Abogacía)
   */
  async corregirEscrito(writing: string, materia: string, prompt: string): Promise<WritingCorrectionResult> {
    const response = await fetch(`${API_BASE}/corregir_escrito`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ writing, materia, prompt })
    });
    const data = await response.json();
    return data.resultado; // Retornamos el objeto JSON que Groq generó
  },

  /**
   * Genera un Rap Técnico basado en el material cargado
   */
  async generarRap(texto: string): Promise<TechnicalRapResult> {
    const response = await fetch(`${API_BASE}/generar_rap`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto })
    });
    const data = await response.json();
    return data.resultado;
  },

  /**
   * Evalúa un resumen comparándolo con el material de estudio
   */
  async corregirResumen(texto: string): Promise<SummaryCorrectionResult> {
    const response = await fetch(`${API_BASE}/corregir_resumen`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto })
    });
    const data = await response.json();
    return data.resultado;
  },

  /**
   * Envía las respuestas del ExerciseForm (los 6 pasos)
   */
  async evaluarRespuestas(answers: StudentAnswers, materia: string): Promise<FullEvaluation> {
    // Aquí aplanamos las respuestas para que el backend las reciba como un solo texto
    const textoEvaluacion = `
      Ideas: ${answers.mainIdeas}
      Resumen: ${answers.summary}
      Esquema: ${answers.schema}
      Inferencias: ${JSON.stringify(answers.inferences)}
      Vocabulario: ${answers.vocabulary}
      Opinión: ${answers.opinion}
    `;

    const response = await fetch(`${API_BASE}/evaluar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: textoEvaluacion, materia })
    });
    const data = await response.json();
    return data.resultado;
  }
};

