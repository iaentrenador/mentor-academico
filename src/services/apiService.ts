// src/services/apiService.ts
import { WritingCorrectionInput, WritingCorrectionResult } from '../types';

const API_BASE = "/api";

export const apiService = {
  // Tarea: corregir_escrito (La principal para tus informes de la UPE)
  async corregirEscrito(input: WritingCorrectionInput): Promise<WritingCorrectionResult> {
    const response = await fetch(`${API_BASE}/corregir_escrito`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input)
    });
    
    if (!response.ok) {
      throw new Error("Error en la comunicación con el Mentor");
    }
    
    const data = await response.json();
    return data.resultado;
  },

  // Tarea: obtener datos de usuario
  async getUsuario() {
    const response = await fetch(`${API_BASE}/usuario`);
    return await response.json();
  }
};
