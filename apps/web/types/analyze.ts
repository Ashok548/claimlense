/**
 * Re-exports all types from the shared package.
 *
 * This file is kept so existing `@/types/analyze` imports in the web app
 * continue to work without any changes. All type definitions now live in
 * packages/shared/src/types/analyze.ts — the single source of truth.
 */
export * from "@claimlense/shared/types";
