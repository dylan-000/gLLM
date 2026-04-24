export enum UserRole {
  ADMIN = 'admin',
  FINETUNER = 'finetuner',
  REGUSER = 'normal',
  RETIREDUSER = 'unauthorized',
}

export interface User {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
}