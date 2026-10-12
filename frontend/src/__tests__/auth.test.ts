import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authService } from '../services/auth';

describe('authService', () => {
  beforeEach(() => {
    authService.logout();
    vi.restoreAllMocks();
  });

  it('stores access token in memory only and handles role checks', () => {
    expect(authService.getToken()).toBeNull();
    authService.setToken('test-mem-token');
    expect(authService.getToken()).toBe('test-mem-token');

    authService.setCurrentUser({
      user_id: 'u1',
      username: 'analyst-1',
      roles: ['analyst'],
      is_demo: true,
    });

    expect(authService.hasRole('analyst')).toBe(true);
    expect(authService.hasRole('admin')).toBe(false);

    authService.logout();
    expect(authService.getToken()).toBeNull();
    expect(authService.getCurrentUser()).toBeNull();
  });

  it('admin role grants access to any role requirement', () => {
    authService.setCurrentUser({
      user_id: 'u-admin',
      username: 'admin-1',
      roles: ['admin'],
      is_demo: true,
    });
    expect(authService.hasRole('viewer')).toBe(true);
    expect(authService.hasRole('analyst')).toBe(true);
    expect(authService.hasRole('operator')).toBe(true);
  });
});
