import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAuthStore } from '../../stores/authStore'
import type { User } from '../../types'

describe('authStore', () => {
  beforeEach(() => {
    // Reset store before each test
    const { clearAuth } = useAuthStore.getState()
    clearAuth()
  })

  it('initializes with default values', () => {
    const { result } = renderHook(() => useAuthStore())

    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('sets auth data correctly', () => {
    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    }
    const mockToken = 'mock-jwt-token'

    const { result } = renderHook(() => useAuthStore())

    act(() => {
      result.current.setAuth(mockUser, mockToken)
    })

    expect(result.current.user).toEqual(mockUser)
    expect(result.current.token).toBe(mockToken)
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('clears auth data correctly', () => {
    const mockUser: User = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    }
    const mockToken = 'mock-jwt-token'

    const { result } = renderHook(() => useAuthStore())

    act(() => {
      result.current.setAuth(mockUser, mockToken)
    })

    expect(result.current.isAuthenticated).toBe(true)

    act(() => {
      result.current.clearAuth()
    })

    expect(result.current.user).toBeNull()
    expect(result.current.token).toBeNull()
    expect(result.current.isAuthenticated).toBe(false)
  })
})
