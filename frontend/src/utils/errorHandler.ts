/**
 * Error handling utilities for consistent error extraction and display.
 *
 * This module provides centralized error handling to reduce code duplication
 * and ensure consistent error messages across the application.
 */

import axios, { AxiosError } from 'axios';

/**
 * API error response structure from FastAPI.
 */
interface APIErrorResponse {
  detail: string | Record<string, unknown>;
}

/**
 * Validation error structure from FastAPI (422).
 */
interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

interface ValidationErrorResponse {
  detail: ValidationError[];
}

/**
 * Extract error message from unknown error object.
 *
 * Handles various error types:
 * - Axios errors with API response
 * - Axios errors without response (network errors)
 * - Standard Error objects
 * - String errors
 * - Unknown error types
 *
 * @param err - Error object (type unknown)
 * @param defaultMsg - Default message if error cannot be extracted
 * @returns Human-readable error message
 *
 * @example
 * ```typescript
 * try {
 *   await api.createTicket(data);
 * } catch (err) {
 *   const message = extractErrorMessage(err, 'Failed to create ticket');
 *   setError(message);
 * }
 * ```
 */
export function extractErrorMessage(
  err: unknown,
  defaultMsg: string = 'An error occurred'
): string {
  // Handle Axios errors
  if (axios.isAxiosError(err)) {
    const axiosError = err as AxiosError<APIErrorResponse>;

    // API returned error response
    if (axiosError.response?.data?.detail) {
      const detail = axiosError.response.data.detail;

      // Detail is a string (most common)
      if (typeof detail === 'string') {
        return detail;
      }

      // Detail is an object (complex error)
      if (typeof detail === 'object') {
        return JSON.stringify(detail);
      }
    }

    // Network error (no response)
    if (axiosError.message) {
      return axiosError.message;
    }

    // Fallback for axios errors
    return defaultMsg;
  }

  // Handle standard Error objects
  if (err instanceof Error) {
    return err.message;
  }

  // Handle string errors
  if (typeof err === 'string') {
    return err;
  }

  // Unknown error type
  return defaultMsg;
}

/**
 * Extract validation errors from 422 response.
 *
 * Formats validation errors into human-readable messages.
 *
 * @param err - Error object
 * @returns Array of validation error messages
 *
 * @example
 * ```typescript
 * try {
 *   await api.createUser(data);
 * } catch (err) {
 *   const errors = extractValidationErrors(err);
 *   if (errors.length > 0) {
 *     setFieldErrors(errors);
 *   }
 * }
 * ```
 */
export function extractValidationErrors(err: unknown): string[] {
  if (!axios.isAxiosError(err)) {
    return [];
  }

  const axiosError = err as AxiosError<ValidationErrorResponse>;

  if (axiosError.response?.status !== 422) {
    return [];
  }

  const detail = axiosError.response.data?.detail;

  if (!Array.isArray(detail)) {
    return [];
  }

  return detail.map((error: ValidationError) => {
    const field = error.loc.slice(1).join('.');
    return `${field}: ${error.msg}`;
  });
}

/**
 * Get HTTP status code from error.
 *
 * @param err - Error object
 * @returns HTTP status code or null
 *
 * @example
 * ```typescript
 * const statusCode = getErrorStatusCode(err);
 * if (statusCode === 401) {
 *   // Redirect to login
 * }
 * ```
 */
export function getErrorStatusCode(err: unknown): number | null {
  if (axios.isAxiosError(err)) {
    return err.response?.status ?? null;
  }
  return null;
}

/**
 * Check if error is a specific HTTP status code.
 *
 * @param err - Error object
 * @param statusCode - HTTP status code to check
 * @returns True if error matches status code
 *
 * @example
 * ```typescript
 * if (isErrorStatus(err, 404)) {
 *   setMessage('Resource not found');
 * }
 * ```
 */
export function isErrorStatus(err: unknown, statusCode: number): boolean {
  return getErrorStatusCode(err) === statusCode;
}

/**
 * Check if error is authentication-related (401 or 403).
 *
 * @param err - Error object
 * @returns True if authentication error
 *
 * @example
 * ```typescript
 * if (isAuthError(err)) {
 *   logout();
 *   navigate('/login');
 * }
 * ```
 */
export function isAuthError(err: unknown): boolean {
  const status = getErrorStatusCode(err);
  return status === 401 || status === 403;
}

/**
 * Check if error is a network error (no response from server).
 *
 * @param err - Error object
 * @returns True if network error
 *
 * @example
 * ```typescript
 * if (isNetworkError(err)) {
 *   setMessage('Network error. Please check your connection.');
 * }
 * ```
 */
export function isNetworkError(err: unknown): boolean {
  if (axios.isAxiosError(err)) {
    return !err.response && !!err.request;
  }
  return false;
}

/**
 * Format error for user display.
 *
 * Provides user-friendly error messages based on status code.
 *
 * @param err - Error object
 * @param context - Context for error (e.g., "creating ticket")
 * @returns Formatted error message
 *
 * @example
 * ```typescript
 * const message = formatErrorForUser(err, 'creating ticket');
 * toast.error(message);
 * ```
 */
export function formatErrorForUser(
  err: unknown,
  context: string = 'performing this action'
): string {
  const status = getErrorStatusCode(err);

  // Map common status codes to user-friendly messages
  switch (status) {
    case 400:
      return `Invalid request while ${context}. Please check your input.`;
    case 401:
      return 'Your session has expired. Please log in again.';
    case 403:
      return `You don't have permission to perform this action.`;
    case 404:
      return `The requested resource was not found.`;
    case 409:
      return `A conflict occurred while ${context}. The resource may already exist.`;
    case 422:
      return `Validation error while ${context}. Please check your input.`;
    case 429:
      return 'Too many requests. Please try again later.';
    case 500:
      return `Server error while ${context}. Please try again later.`;
    case 503:
      return 'Service temporarily unavailable. Please try again later.';
    default: {
      // Try to extract specific error message
      const message = extractErrorMessage(err);
      if (message && message !== 'An error occurred') {
        return message;
      }

      // Generic fallback
      return `An error occurred while ${context}. Please try again.`;
    }
  }
}

/**
 * Log error to console (development only).
 *
 * @param err - Error object
 * @param context - Context for error
 *
 * @example
 * ```typescript
 * try {
 *   await api.fetchData();
 * } catch (err) {
 *   logError(err, 'fetching data');
 *   throw err;
 * }
 * ```
 */
export function logError(err: unknown, context?: string): void {
  if (import.meta.env.DEV) {
    console.error(context ? `Error ${context}:` : 'Error:', err);

    if (axios.isAxiosError(err)) {
      console.error('Response data:', err.response?.data);
      console.error('Status code:', err.response?.status);
    }
  }
}

/**
 * Error handler for async operations with toast notifications.
 *
 * Provides a higher-order function for consistent error handling.
 *
 * @param operation - Async operation to execute
 * @param context - Context for error messages
 * @param onError - Optional custom error handler
 * @returns Result of operation or undefined on error
 *
 * @example
 * ```typescript
 * const handleSubmit = async (data: FormData) => {
 *   return withErrorHandling(
 *     () => api.createTicket(data),
 *     'creating ticket',
 *     (err) => setFormError(extractErrorMessage(err))
 *   );
 * };
 * ```
 */
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  context: string,
  onError?: (err: unknown) => void
): Promise<T | undefined> {
  try {
    return await operation();
  } catch (err) {
    logError(err, context);

    if (onError) {
      onError(err);
    }

    return undefined;
  }
}
