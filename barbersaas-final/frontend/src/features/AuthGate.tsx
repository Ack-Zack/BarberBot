import { useEffect, useState, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { authenticate, getBarberInviteTokenFromStartParam, getBusinessSlugFromStartParam, joinFromStartParam } from '../api/auth'
import type { Me } from '../types/api'

export function AuthGate({ children, onUser }: { children: ReactNode; onUser: (user: Me) => void }) {
  const queryClient = useQueryClient()
  const [joining, setJoining] = useState(false)
  const [joinAttempted, setJoinAttempted] = useState(false)
  const query = useQuery({ queryKey: ['me'], queryFn: authenticate, retry: false })

  useEffect(() => {
    if (!query.data) return
    onUser(query.data)

    const hasInvite = Boolean(getBusinessSlugFromStartParam() || getBarberInviteTokenFromStartParam())
    if (!hasInvite || query.data.business_id || joining || joinAttempted) return

    setJoinAttempted(true)
    setJoining(true)
    joinFromStartParam()
      .then((user) => {
        if (user) {
          onUser(user)
          queryClient.setQueryData(['me'], user)
          queryClient.invalidateQueries({ queryKey: ['onboarding'] })
        }
      })
      .catch(() => undefined)
      .finally(() => setJoining(false))
  }, [query.data, onUser, joining, joinAttempted, queryClient])

  if (query.isLoading || joining) return <div className="center"><div><div className="spinner" /><p>Подключаем аккаунт…</p></div></div>
  if (query.isError) return <div className="center error-screen"><h1>Не удалось войти</h1><p>{query.error.message}</p><button className="primary compact" onClick={() => window.location.reload()}>Повторить</button></div>
  return <>{children}</>
}
