/**
 * Lodge-Link typed API client.
 * ALL API calls go through this file — no page should call fetch() directly.
 * Token management, 401 handling, and error normalisation are centralised here.
 */

let BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
if (!BASE.startsWith('http')) {
  BASE = `https://${BASE}`;
}

if (typeof window !== 'undefined') {
  console.log('[Lodge-Link] API Base URL:', BASE);
}

// ── TypeScript Interfaces ──────────────────────────────────────────────────

export interface Hotel {
  id: string;
  name: string;
  slug: string;
  city: string;
  address: string;
  phone_number: string;
  email: string;
  country_code: string;
  category: 'BUDGET' | 'STANDARD' | 'PREMIUM' | 'LUXURY';
  status: 'PENDING_KYC' | 'SANDBOX' | 'ACTIVE' | 'SUSPENDED';
  is_referral_eligible: boolean;
  created_at: string;
}

export interface RegisterPayload {
  hotel_name: string;
  hotel_slug: string;
  city: string;
  address: string;
  phone_number: string;
  country_code?: string;
  latitude?: number;
  longitude?: number;
  admin_email: string;
  admin_full_name: string;
  admin_password: string;
}

export interface RegisterResponse {
  hotel_id: string;
  user_id: string;
  api_key: string;
  api_key_prefix: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  message: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RoomAvailability {
  room_type: 'SINGLE' | 'DOUBLE' | 'TWIN' | 'SUITE' | 'FAMILY' | 'DORMITORY';
  available_count: number;
}

export interface HotelAvailabilityResult {
  hotel_id: string;
  updated_at: string;
  availability: RoomAvailability[];
}

export interface FanoutRequest {
  origin_hotel_id: string;
  guest_name: string;
  guest_phone: string;
  room_type?: string;
  party_size?: number;
  check_in_date?: string;
  check_out_date?: string;
  special_requests?: string;
  origin_longitude: number;
  origin_latitude: number;
  radius_metres?: number;
  idempotency_key?: string;
}

export interface FanoutResponse {
  session_id: string;
  notified_hotels: number;
  status: string;
  message: string;
}

export interface ReferralLeg {
  referral_id: string;
  session_id: string;
  destination_hotel_id: string | null;
  status: 'PENDING' | 'ACCEPTED' | 'DECLINED' | 'COMPLETED' | 'EXPIRED' | 'CANCELLED';
  handshake_code_hint: string | null;
  accepted_at: string | null;
  completed_at: string | null;
  expired_at: string | null;
}

export interface SessionStatus {
  session_id: string;
  guest_name: string;
  referrals: ReferralLeg[];
  accepted_count: number;
  pending_count: number;
}

export interface AcceptResponse {
  referral_id: string;
  status: string;
  message: string;
}

export interface HandshakeValidateResponse {
  success: boolean;
  message: string;
}

export interface SystemStatus {
  status: string;
  database?: string;
  cache?: string;
  version?: string;
}

export interface ApiError {
  error: string;
  status?: number;
}

// ── Token helpers ──────────────────────────────────────────────────────────

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('ll_token');
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('ll_token', token);
}

export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('ll_token');
  localStorage.removeItem('ll_hotel_type');
  localStorage.removeItem('ll_hotel_id');
}

// ── Core fetch wrapper ─────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  requireAuth = true,
  isFormData = false
): Promise<T | ApiError> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  if (requireAuth) {
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const res = await fetch(`${BASE}${path}`, { ...options, headers });

    if (res.status === 401) {
      clearAuth();
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
      return { error: 'Unauthorized — please log in again.', status: 401 };
    }

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        detail = body.detail || body.message || detail;
        if (typeof detail === 'object') {
          detail = JSON.stringify(detail);
        }
      } catch {}
      return { error: String(detail), status: res.status };
    }

    if (res.status === 204) return {} as T;
    return (await res.json()) as T;
  } catch (e) {
    return { error: 'Network unavailable — please check your connection.' };
  }
}

// ── Auth ───────────────────────────────────────────────────────────────────

export async function loginHotel(email: string, password: string): Promise<TokenResponse | ApiError> {
  const result = await apiFetch<TokenResponse>('/v1/auth/token', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }, false);

  if ('access_token' in result) {
    setToken(result.access_token);
  }
  return result;
}

export async function registerHotel(payload: RegisterPayload): Promise<RegisterResponse | ApiError> {
  const result = await apiFetch<RegisterResponse>('/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, false);

  if ('access_token' in result) {
    setToken(result.access_token);
  }
  return result;
}

// ── Availability ───────────────────────────────────────────────────────────

export async function updateAvailability(
  hotelId: string,
  rooms: RoomAvailability[],
): Promise<HotelAvailabilityResult | ApiError> {
  return apiFetch<HotelAvailabilityResult>(`/v1/hotels/${hotelId}/availability`, {
    method: 'POST',
    body: JSON.stringify({ availability: rooms }),
  });
}

export async function getAvailability(params: {
  longitude: number;
  latitude: number;
  radius_metres?: number;
}): Promise<HotelAvailabilityResult[] | ApiError> {
  const q = new URLSearchParams({
    longitude: String(params.longitude),
    latitude: String(params.latitude),
    radius_metres: String(params.radius_metres ?? 5000),
  });
  return apiFetch<HotelAvailabilityResult[]>(`/v1/hotels?${q}`);
}

export async function getHotelAvailability(hotelId: string): Promise<HotelAvailabilityResult | ApiError> {
  return apiFetch<HotelAvailabilityResult>(`/v1/hotels/${hotelId}/availability`);
}

// ── Referrals ─────────────────────────────────────────────────────────────

export async function getIncomingReferrals(): Promise<any[] | ApiError> {
  const hotelId = typeof window !== 'undefined' ? localStorage.getItem('ll_hotel_id') : null;
  return apiFetch<any[]>('/v1/referrals/incoming', {
    headers: hotelId ? { 'll_hotel_id': hotelId } : {}
  });
}

export async function createReferral(payload: FanoutRequest): Promise<FanoutResponse | ApiError> {
  return apiFetch<FanoutResponse>('/v1/referrals', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getReferralSession(sessionId: string): Promise<SessionStatus | ApiError> {
  return apiFetch<SessionStatus>(`/v1/referrals/${sessionId}`);
}

export async function acceptReferral(referralId: string): Promise<AcceptResponse | ApiError> {
  return apiFetch<AcceptResponse>(`/v1/referrals/${referralId}/accept`, { method: 'POST' });
}

export async function declineReferral(referralId: string, reason?: string): Promise<AcceptResponse | ApiError> {
  return apiFetch<AcceptResponse>(`/v1/referrals/${referralId}/decline`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function validateHandshake(
  referralId: string,
  code: string,
): Promise<HandshakeValidateResponse | ApiError> {
  return apiFetch<HandshakeValidateResponse>(
    `/v1/referrals/${referralId}/handshake?code=${encodeURIComponent(code)}`,
  );
}

// ── System ─────────────────────────────────────────────────────────────────

export async function getSystemStatus(): Promise<SystemStatus | ApiError> {
  return apiFetch<SystemStatus>('/status', {}, false);
}

export async function getHealth(): Promise<SystemStatus | ApiError> {
  return apiFetch<SystemStatus>('/health', {}, false);
}

// ── Helpers ────────────────────────────────────────────────────────────────

export function isApiError(r: unknown): r is ApiError {
  return typeof r === 'object' && r !== null && 'error' in r;
}

export const apiCall = async (
  path: string, 
  options: RequestInit = {}, 
  isFormData: boolean = false,
  requireAuth: boolean = true
) => {
  const result = await apiFetch<any>(path, options, requireAuth, isFormData);
  if (isApiError(result)) {
    const errorMsg = typeof result.error === 'string' ? result.error : JSON.stringify(result.error);
    throw new Error(errorMsg);
  }
  return result;
};
