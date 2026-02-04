/**
 * API Index - Single Export Point
 * 
 * All API functionality is in client.ts
 * This file provides backward compatibility
 */
export * from './client';
export { default as api } from './client';
