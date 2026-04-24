import { apiClient } from "./apiClient";

export interface FineTuneRequestCreate {
  domain: string;
  description: string;
  necessity: string;
}

export interface FineTuneRequestResponse {
  id: string;
  userId: string;
  domain: string;
  description: string;
  necessity: string;
  status: string;
  createdAt: string;
  user_identifier: string | null;
}

export const finetuneService = {
  submitRequest: async (data: FineTuneRequestCreate): Promise<FineTuneRequestResponse> => {
    const response = await apiClient.post<FineTuneRequestResponse>("/finetune/requests", data);
    return response.data;
  },

  getAllRequests: async (): Promise<FineTuneRequestResponse[]> => {
    const response = await apiClient.get<FineTuneRequestResponse[]>("/finetune/requests");
    return response.data;
  },

  updateRequestStatus: async (requestId: string, status: string): Promise<FineTuneRequestResponse> => {
    const response = await apiClient.put<FineTuneRequestResponse>(`/finetune/requests/${requestId}`, { status });
    return response.data;
  }
};
