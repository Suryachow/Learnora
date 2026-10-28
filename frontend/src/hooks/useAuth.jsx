import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import * as authApi from '../api/auth'
import { clearToken, getToken, setToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // 'loading' until we know whether the stored token is still good.
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      if (!getToken()) {
        setStatus('ready')
        return
      }
      try {
        const me = await authApi.fetchMe()
        if (!cancelled) setUser(me)
      } catch {
        clearToken()
      } finally {
        if (!cancelled) setStatus('ready')
      }
    }

    restoreSession()
    return () => {
      cancelled = true
    }
  }, [])

  const signIn = useCallback(async (credentials) => {
    const data = await authApi.login(credentials)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const signUp = useCallback(async (payload) => {
    const data = await authApi.register(payload)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const signOut = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const refresh = useCallback(async () => {
    const me = await authApi.fetchMe()
    setUser(me)
    return me
  }, [])

  const value = useMemo(
    () => ({ user, status, signIn, signUp, signOut, refresh }),
    [user, status, signIn, signUp, signOut, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return context
}
