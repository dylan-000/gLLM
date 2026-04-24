import type { AuthUser } from '../contexts/AuthContext';

export interface ContainerStatus {
  vllm: { status: 'up' | 'down' };
  unsloth: { status: 'up' | 'down' };
}

export const adminService = {
  getContainerStatus: async (): Promise<ContainerStatus> => {
    const res = await fetch('/admin/containers/status');
    if (!res.ok) throw new Error('Failed to fetch container status');
    return res.json();
  },

  startContainer: async (serviceName: 'vllm' | 'unsloth'): Promise<{ message: string }> => {
    const res = await fetch(`/admin/containers/${serviceName}/start`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to start ${serviceName}`);
    return res.json();
  },

  stopContainer: async (serviceName: 'vllm' | 'unsloth'): Promise<{ message: string }> => {
    const res = await fetch(`/admin/containers/${serviceName}/stop`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to stop ${serviceName}`);
    return res.json();
  },

  getUsers: async (): Promise<AuthUser[]> => {
    const res = await fetch('/admin/users/');
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  },

  updateUserRole: async (userId: string, role: string): Promise<AuthUser> => {
    const res = await fetch(`/admin/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role })
    });
    if (!res.ok) throw new Error('Failed to update user role');
    return res.json();
  }
};
