/**
 * API service layer for communicating with the FastAPI backend.
 * Handles JWT token management and request authentication.
 */

const API_BASE = '/auth';
const ADMIN_BASE = '/admin';

// --- Token Management ---

export function getToken(): string | null {
  return localStorage.getItem('jwt_token');
}

export function setToken(token: string): void {
  localStorage.setItem('jwt_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('jwt_token');
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token
    ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
    : { 'Content-Type': 'application/json' };
}

// --- Auth API ---

export async function loginApi(
  username: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || 'Login failed');
  }

  return res.json();
}

export async function signupApi(data: {
  identifier: string;
  password: string;
  firstname?: string;
  lastname?: string;
  email?: string;
}): Promise<void> {
  const res = await fetch(`${API_BASE}/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || 'Signup failed');
  }
}

export async function getMeApi() {
  const res = await fetch(`${API_BASE}/me`, {
    headers: authHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to fetch user');
  }

  return res.json();
}

// --- Admin API ---

export async function getUsers() {
  const res = await fetch(`${ADMIN_BASE}/users/`, {
    headers: authHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to fetch users');
  }

  return res.json();
}

export async function updateUserRole(userId: string, role: string) {
  const res = await fetch(`${ADMIN_BASE}/users/${userId}`, {
    method: 'PUT',
    headers: authHeaders(),
    body: JSON.stringify({ role }),
  });

  if (!res.ok) {
    throw new Error('Failed to update user');
  }

  return res.json();
}

export async function deleteUser(userId: string) {
  const res = await fetch(`${ADMIN_BASE}/users/${userId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to delete user');
  }
}
