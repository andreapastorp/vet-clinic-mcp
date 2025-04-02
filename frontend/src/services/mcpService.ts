import { useState, useEffect } from 'react';

// Types
export interface MCPToolResponse {
  type: 'text' | 'tool' | 'error';
  content: string;
  name?: string;
  args?: Record<string, any>;
  result?: string;
}

export interface Patient {
  id: string;
  name: string;
  species: string;
  breed: string;
  gender?: string;
  birthDate?: string;
  microchipNumber?: string;
  appointments?: Appointment[];
  weightHistory?: WeightRecord[];
  vaccinations?: Vaccination[];
}

export interface Appointment {
  date: string;
  status: string;
  notes: string;
  appointmentType: string;
}

export interface WeightRecord {
  weight: number;
  date: string;
  note: string;
}

export interface Vaccination {
  type: string;
  date: string;
  expirationDate: string;
}

const API_BASE_URL = '/api';

// Generic API call function
async function apiCall<T>(endpoint: string, method = 'GET', data: any = null): Promise<T> {
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json'
    }
  };

  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json() as T;
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

// MCP Chat API
export const useMCPChat = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (message: string): Promise<MCPToolResponse[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiCall<MCPToolResponse[]>('/chat', 'POST', { message });
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  return { sendMessage, isLoading, error };
};

// Patient API
export const usePatientsAPI = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPatients = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiCall<Patient[]>('/patients');
      setPatients(result);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  const getPatient = async (id: string): Promise<Patient | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiCall<Patient>(`/patients/${id}`);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const createPatient = async (patientData: Partial<Patient>): Promise<string> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await apiCall<{message: string}>('/patients', 'POST', patientData);
      fetchPatients(); // Refresh the list
      return result.message;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return 'Error creating patient';
    } finally {
      setIsLoading(false);
    }
  };

  // Load patients on initial render
  useEffect(() => {
    fetchPatients();
  }, []);

  return { 
    patients, 
    fetchPatients, 
    getPatient, 
    createPatient, 
    isLoading, 
    error 
  };
};

export default {
  useMCPChat,
  usePatientsAPI
};
