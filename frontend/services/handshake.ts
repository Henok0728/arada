import axios from 'axios';
import CryptoJS from 'crypto-js';
import { getReferral, markAsVerifiedLocally } from '../lib/db';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface VerificationResult {
  success: boolean;
  message: string;
  isOffline?: boolean;
}

export const verifyHandshake = async (
  referralId: string,
  code: string
): Promise<VerificationResult> => {
  // Check network status
  if (!navigator.onLine) {
    return verifyOffline(referralId, code);
  }

  try {
    const response = await axios.post(`${API_BASE_URL}/v1/handshake/verify`, {
      referral_id: referralId,
      code: code,
    });
    
    return {
      success: response.data.status === 'COMPLETED',
      message: response.data.message || 'Verification successful',
    };
  } catch (error: any) {
    // If API call fails due to network (even if navigator.onLine was true)
    if (!error.response) {
      return verifyOffline(referralId, code);
    }
    
    return {
      success: false,
      message: error.response?.data?.detail || 'Verification failed',
    };
  }
};

const verifyOffline = async (
  referralId: string,
  code: string
): Promise<VerificationResult> => {
  const referral = await getReferral(referralId);
  
  if (!referral) {
    return {
      success: false,
      message: 'Referral not found in offline cache',
      isOffline: true,
    };
  }

  // Hash the entered code
  const enteredHash = CryptoJS.SHA256(code).toString();
  
  if (enteredHash === referral.handshake_code_hash) {
    await markAsVerifiedLocally(referralId);
    return {
      success: true,
      message: 'Verified locally (Offline)',
      isOffline: true,
    };
  }

  return {
    success: false,
    message: 'Invalid code',
    isOffline: true,
  };
};
