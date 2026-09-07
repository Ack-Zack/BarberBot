import { apiFetch } from './client'
import type { Appointment, Barber, BarberInvite, Business, Client, Me, OnboardingStatus, ScheduleBlock, Service, WorkingInterval } from '../types/api'

export const getMe = () => apiFetch<Me>('/auth/me')
export const getBusiness = () => apiFetch<Business>('/businesses/me')
export const createBusiness = (payload: { name: string; timezone: string }) =>
  apiFetch<Business>('/businesses', { method: 'POST', body: JSON.stringify(payload) })
export const updateBusiness = (payload: { name?: string; timezone?: string }) =>
  apiFetch<Business>('/businesses/me', { method: 'PATCH', body: JSON.stringify(payload) })
export const getOnboardingStatus = () => apiFetch<OnboardingStatus>('/onboarding/status')
export const getBookingLink = () => apiFetch<{ url: string }>('/businesses/me/booking-link')

export const getServices = () => apiFetch<Service[]>('/services')
export const createService = (payload: { name: string; description?: string; duration_minutes: number; price_minor: number; currency: string }) =>
  apiFetch<Service>('/services', { method: 'POST', body: JSON.stringify(payload) })
export const updateService = (id: number, payload: Partial<{ name: string; description: string; duration_minutes: number; price_minor: number; currency: string; is_active: boolean }>) =>
  apiFetch<Service>(`/services/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const getBarbers = () => apiFetch<Barber[]>('/barbers')
export const createBarberInvite = (expires_in_days = 7) =>
  apiFetch<BarberInvite>('/barbers/invites', { method: 'POST', body: JSON.stringify({ expires_in_days }) })
export const updateBarber = (id: number, display_name: string) =>
  apiFetch<Barber>(`/barbers/${id}?display_name=${encodeURIComponent(display_name)}`, { method: 'PATCH' })
export const deactivateBarber = (id: number) => apiFetch<void>(`/barbers/${id}`, { method: 'DELETE' })

export const getMine = () => apiFetch<Appointment[]>('/appointments/mine')
export const getAllAppointments = (date?: string, barberId?: number) => {
  const params = new URLSearchParams()
  if (date) params.set('date', date)
  if (barberId) params.set('barber_id', String(barberId))
  return apiFetch<Appointment[]>(`/appointments${params.toString() ? `?${params}` : ''}`)
}
export const createAppointment = (payload: { barber_id: number; service_id: number; starts_at: string; client_id?: number; client_name?: string; client_phone?: string }) =>
  apiFetch<Appointment>('/appointments', { method: 'POST', body: JSON.stringify(payload) })
export const cancelAppointment = (id: number) => apiFetch<Appointment>(`/appointments/${id}/cancel`, { method: 'POST' })
export const updateAppointment = (id: number, payload: { starts_at?: string; status?: string }) =>
  apiFetch<Appointment>(`/appointments/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })

export const getClients = () => apiFetch<Client[]>('/clients')
export const createClient = (payload: { name: string; phone?: string; notes?: string }) =>
  apiFetch<Client>('/clients', { method: 'POST', body: JSON.stringify(payload) })
export const getClientHistory = (id: number) => apiFetch<Appointment[]>(`/clients/${id}/appointments`)

export const getWorkingHours = (barberId: number) => apiFetch<WorkingInterval[]>(`/schedule/working-hours/${barberId}`)
export const saveWorkingHours = (barberId: number, intervals: Omit<WorkingInterval, 'id'>[]) =>
  apiFetch<{ status: string; count: number }>(`/schedule/working-hours/${barberId}`, {
    method: 'PUT',
    body: JSON.stringify({ intervals }),
  })
export const getBlocks = (barberId?: number, date?: string) => {
  const params = new URLSearchParams()
  if (barberId) params.set('barber_id', String(barberId))
  if (date) params.set('date', date)
  return apiFetch<ScheduleBlock[]>(`/schedule/blocks${params.toString() ? `?${params}` : ''}`)
}
export const createBlock = (payload: { barber_id: number; starts_at: string; ends_at: string; reason?: string }) =>
  apiFetch<ScheduleBlock>('/schedule/blocks', { method: 'POST', body: JSON.stringify(payload) })
export const deleteBlock = (id: number) => apiFetch<void>(`/schedule/blocks/${id}`, { method: 'DELETE' })

export const getAvailability = (barberId: number, serviceId: number, date: string) =>
  apiFetch<{ date: string; timezone: string; slots: string[] }>(`/availability?barber_id=${barberId}&service_id=${serviceId}&date=${date}`)
