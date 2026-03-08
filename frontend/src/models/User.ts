// Roles must match backend UserRole enum in src/schema/models.py
export enum UserRole {
  ADMIN = 'admin',
  FINE_TUNER = 'fine_tuner',
  NORMAL = 'normal',
  UNAUTHORIZED = 'unauthorized',
}

export interface User {
  id: string;
  identifier: string;
  email: string | null;
  firstname: string | null;
  lastname: string | null;
  role: UserRole;
  createdAt: string;
}
