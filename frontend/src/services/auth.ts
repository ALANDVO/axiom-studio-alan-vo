/**
 * Secure OIDC client handling in-memory access tokens and PKCE authentication.
 */
import { TokenResponse, UserProfile } from '../types';

let inMemoryToken: string | null = null;
let currentUserProfile: UserProfile | null = null;

export const authService = {
  getToken(): string | null {
    return inMemoryToken;
  },

  setToken(token: string | null): void {
    inMemoryToken = token;
  },

  getCurrentUser(): UserProfile | null {
    return currentUserProfile;
  },

  setCurrentUser(profile: UserProfile | null): void {
    currentUserProfile = profile;
  },

  hasRole(role: string): boolean {
    if (!currentUserProfile) return false;
    if (currentUserProfile.roles.includes('admin')) return true;
    return currentUserProfile.roles.includes(role);
  },

  async loginDemo(role: 'viewer' | 'analyst' | 'admin' = 'analyst'): Promise<TokenResponse> {
    const res = await fetch('/api/auth/demo-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, username: `analyst-${role}` }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to demo login' }));
      throw new Error(err.detail || 'Demo login failed');
    }

    const data: TokenResponse = await res.json();
    inMemoryToken = data.access_token;
    currentUserProfile = {
      user_id: `user-${data.username}`,
      username: data.username,
      roles: data.roles,
      is_demo: data.is_demo,
    };
    return data;
  },

  logout(): void {
    inMemoryToken = null;
    currentUserProfile = null;
    sessionStorage.removeItem('pkce_verifier');
    sessionStorage.removeItem('oauth_state');
  },
};
