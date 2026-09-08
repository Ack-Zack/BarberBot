import { apiFetch } from './client'
import type { Me } from '../types/api'

export function getStartParam(): string | null {
  return (
    window.Telegram?.WebApp?.initDataUnsafe?.start_param ??
    new URLSearchParams(window.location.search).get('startapp')
  )
}

export function getBusinessSlugFromStartParam(): string | null {
  const value = getStartParam()
  return value?.startsWith('b_') ? value.slice(2) : null
}

export function getBarberInviteTokenFromStartParam(): string | null {
  const value = getStartParam()
  return value?.startsWith('i_') ? value.slice(2) : null
}

export async function authenticate(): Promise<Me> {
  const mode = new URLSearchParams(window.location.search).get('mode')
  const tgInitData = window.Telegram?.WebApp?.initData ?? ''
  const role = mode === 'barber'
    ? 'barber'
    : mode === 'onboarding'
      ? 'onboarding'
      : mode === 'visitor'
        ? 'visitor'
        : 'client'

  const auth = tgInitData
    ? await apiFetch<{ access_token: string }>('/auth/telegram', {
        method: 'POST',
        body: JSON.stringify({ init_data: tgInitData }),
      })
    : await apiFetch<{ access_token: string }>(`/auth/dev?role=${role}`, { method: 'POST' })

  localStorage.setItem('barbersaas_token', auth.access_token)
  return apiFetch<Me>('/auth/me')
}

export async function joinFromStartParam(): Promise<Me | null> {
  const businessSlug = getBusinessSlugFromStartParam()
  const inviteToken = getBarberInviteTokenFromStartParam()

  if (businessSlug) {
    await apiFetch(`/businesses/join/${encodeURIComponent(businessSlug)}`, { method: 'POST' })
    return apiFetch<Me>('/auth/me')
  }

  if (inviteToken) {
    await apiFetch(`/barbers/invites/join?token=${encodeURIComponent(inviteToken)}`, { method: 'POST' })
    return apiFetch<Me>('/auth/me')
  }

  return null
}
