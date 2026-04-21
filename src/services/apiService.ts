// src/services/apiService.ts
import { WritingCorrectionInput, WritingCorrectionResult, UserStats } from '../types';

const API_BASE = "/api";

/**
 * Helper para manejar las peticiones fetch de forma centralizada
 * Asegura que las cookies de sesión (credenciales) viajen siempre al servidor.
 */
async function fetchWithConfig(url: string, options: RequestInit = {}) {
  const config = {
    ...options,
    credentials: ("include" as RequestCredentials), // Crucial para la sesión de Flask
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Error del servidor: ${response.status}`);
  }

  return response.json();
}

export const apiService = {
  // Tarea: corregir_escrito (Informe UPE)
  async corregirEscrito(input: WritingCorrectionInput): Promise<WritingCorrectionResult> {
    try {
      const data = await fetchWithConfig(`${API_BASE}/corregir_escrito`, {
        method: "POST",
        body: JSON.stringify(input),
      });

      // Protección contra datos malformados: si 'resultado' no existe, lanzamos error
      // para evitar la pantalla en blanco en el componente.
      if (!data || !data.resultado) {
        throw new Error("El Mentor devolvió un formato de respuesta inválido.");
      }

      return data.resultado;
    } catch (error) {
      console.error("Error en corregirEscrito:", error);
      throw error;
    }
  },

  // Tarea: obtener datos de usuario (Créditos, Email, etc.)
  async getUsuario(): Promise<UserStats> {
    try {
      const data = await fetchWithConfig(`${API_BASE}/usuario`);
      
      // Estructura por defecto para evitar errores de renderizado inicial
      return {
        logueado: data.logueado || false,
        email: data.email || "",
        restantes: data.restantes ?? 0,
        url_ad: data.url_ad || "https://google.com",
        bloques_ad: data.bloques_ad || 0,
        total_hoy: data.total_hoy || 4
      };
    } catch (error) {
      console.error("Error al obtener usuario:", error);
      // Retornamos un estado seguro en lugar de romper la app
      return { 
        logueado: false, 
        email: "", 
        restantes: 0, 
        url_ad: "", 
        bloques_ad: 0, 
        total_hoy: 4 
      };
    }
  }
};
