import axios from "axios"

const API_BASE_URL = "http://localhost:8001"

/**
 * Axios instance with pre-configured settings for API requests.
 *
 * Features:
 * - Automatic inclusion of credentials (cookies)
 * - JSON content type by default
 * - Centralized error handling
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Include cookies in all requests
})

/**
 * Response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Extract error message from response
    if (error.response?.data?.detail) {
      error.message = error.response.data.detail
    }
    return Promise.reject(error)
  }
)

export default apiClient
