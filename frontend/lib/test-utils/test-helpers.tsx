/**
 * Test Utilities and Helpers
 * 
 * Provides common utilities for testing React components, API routes, and integration tests.
 */

import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

/**
 * Create a test QueryClient with default options
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

/**
 * Custom render function that includes providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  const queryClient = createTestQueryClient()

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...options })
}

/**
 * Mock environment variables for testing
 */
export function mockEnv(overrides: Record<string, string> = {}) {
  const originalEnv = process.env

  beforeEach(() => {
    process.env = {
      ...originalEnv,
      ...overrides,
    }
  })

  afterEach(() => {
    process.env = originalEnv
  })
}

/**
 * Wait for async operations to complete
 */
export async function waitForAsync() {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

/**
 * Mock Supabase client for testing
 */
export function createMockSupabaseClient() {
  return {
    auth: {
      getUser: jest.fn(),
      signInWithPassword: jest.fn(),
      signOut: jest.fn(),
      onAuthStateChange: jest.fn(() => ({
        data: { subscription: null },
        unsubscribe: jest.fn(),
      })),
    },
    from: jest.fn(() => ({
      select: jest.fn().mockReturnThis(),
      insert: jest.fn().mockReturnThis(),
      update: jest.fn().mockReturnThis(),
      delete: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      single: jest.fn(),
    })),
  }
}

/**
 * Create mock API response
 */
export function createMockResponse<T>(data: T, status: number = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers(),
  } as Response
}

/**
 * Mock fetch for API testing
 */
export function mockFetch(response: unknown, status: number = 200) {
  global.fetch = jest.fn(() =>
    Promise.resolve(createMockResponse(response, status))
  ) as jest.Mock
}

/**
 * Reset all mocks
 */
export function resetMocks() {
  jest.clearAllMocks()
  jest.resetAllMocks()
}

// Re-export everything from testing-library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
