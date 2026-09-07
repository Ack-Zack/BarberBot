export type Role = 'owner' | 'barber' | 'client'
export type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'

export interface Me {
  id: number
  telegram_id: number
  username?: string | null
  first_name: string
  last_name?: string | null
  role: Role
  business_id: number | null
  member_id: number | null
  display_name: string
  needs_business: boolean
  can_create_business: boolean
}

export interface Business {
  id: number
  name: string
  slug: string
  timezone: string
  created_at?: string | null
}

export interface OnboardingStatus {
  needs_business: boolean
  business_id: number | null
  business_name: string | null
  owner_member_id: number | null
  has_service: boolean
  has_working_hours: boolean
  complete: boolean
  booking_link: string | null
}

export interface Service {
  id: number
  name: string
  description?: string | null
  duration_minutes: number
  price_minor: number
  currency: string
  is_active: boolean
}

export interface Barber {
  id: number
  display_name: string
  role: 'owner' | 'barber'
  is_active: boolean
}

export interface Appointment {
  id: number
  barber_id: number
  client_id: number
  service_id: number
  starts_at: string
  ends_at: string
  status: AppointmentStatus | string
  price_minor: number
  duration_minutes: number
  cancelled_at?: string | null
  barber_name?: string | null
  client_name?: string | null
  service_name?: string | null
}

export interface WorkingInterval {
  id?: number
  weekday: number
  start_time: string
  end_time: string
}

export interface ScheduleBlock {
  id: number
  barber_id: number
  starts_at: string
  ends_at: string
  reason?: string | null
}

export interface Client {
  id: number
  user_id: number | null
  name: string
  phone?: string | null
  notes?: string | null
  appointments_count: number
  last_appointment_at?: string | null
}

export interface BarberInvite {
  url: string
  expires_at: string
}
