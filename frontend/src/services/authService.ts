import { apiClient } from "./apiClient"

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface SignupRequest {
  identifier: string
  firstname: string
  lastname: string
  email: string
  password: string
}

export interface User {
  identifier: string
  id: string
  role: string
  firstname: string
  lastname: string
  email: string
  createdAt: string
  langfuse_public_key?: string | null
  langfuse_secret_key_set?: boolean
}

/**
 * Logs in with username and password
 * Sends as application/x-www-form-urlencoded (required by OAuth2PasswordRequestForm)
 * The server will automatically set an HttpOnly cookie with the JWT
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  // Create URLSearchParams for form-encoded data
  const formData = new URLSearchParams()
  formData.append("username", credentials.username)
  formData.append("password", credentials.password)

  const response = await apiClient.post<LoginResponse>("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  })
  return response.data
}

/**
 * Signs up a new user
 * Sends: application/json with UserCreate data
 * Returns: void (201 Created on success)
 * Does not set authentication cookie (user must log in after)
 */
export async function signup(data: SignupRequest): Promise<void> {
  await apiClient.post("/auth/signup", data)
}

/**
 * Gets current authenticated user information
 * Sends: no body (GET request)
 * Returns: User object from authenticated cookie
 * Requires: valid auth_token cookie from login
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me")
  return response.data
}

/**
 * Logs out by clearing the auth_token cookie
 * Sends: no body (POST request)
 * Returns: void (200 OK on success)
 * Effect: Clears auth_token cookie on response
 */
export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout", {})
}


export async function updateLangfuseConfig(keys: { langfuse_public_key: string, langfuse_secret_key: string }) {
  const response = await apiClient.put("/auth/me/langfuse", keys);
  return response.data;
}