export enum UserRole {
  ADMIN = 'admin',
  FINETUNER = 'finetuner',
  REGUSER = 'reguser',
  RETIREDUSER = 'retireduser',
}

export interface User {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
}