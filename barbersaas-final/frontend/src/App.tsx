import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { AuthGate } from './features/AuthGate'
import { BottomNav } from './components/BottomNav'
import { HomePage } from './pages/HomePage'
import { BookingPage } from './pages/BookingPage'
import { AppointmentsPage } from './pages/AppointmentsPage'
import { AppointmentDetailsPage } from './pages/client/AppointmentDetailsPage'
import { ProfilePage } from './pages/ProfilePage'
import { WelcomePage } from './pages/client/WelcomePage'
import { OnboardingPage } from './pages/onboarding/OnboardingPage'
import { DashboardPage } from './pages/barber/DashboardPage'
import { SchedulePage } from './pages/barber/SchedulePage'
import { ClientsPage } from './pages/barber/ClientsPage'
import { ServicesPage } from './pages/barber/ServicesPage'
import { MorePage } from './pages/barber/MorePage'
import { TeamPage } from './pages/barber/TeamPage'
import { SettingsPage } from './pages/barber/SettingsPage'
import { getMe, getOnboardingStatus } from './api/data'
import { getStartParam } from './api/auth'
import type { Me } from './types/api'

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 15_000, retry: 1 } } })

function Shell({ user }: { user: Me }) {
  const meQuery = useQuery({ queryKey: ['me'], queryFn: getMe })
  const currentUser = meQuery.data ?? user
  const barber = currentUser.role === 'owner' || currentUser.role === 'barber'
  const onboarding = useQuery({ queryKey: ['onboarding'], queryFn: getOnboardingStatus, enabled: currentUser.can_create_business })
  const mode = new URLSearchParams(window.location.search).get('mode')
  const startParam = getStartParam()

  useEffect(() => {
    const webApp = window.Telegram?.WebApp
    webApp?.ready?.()
    webApp?.expand?.()
  }, [])

  if (currentUser.business_id === null && currentUser.can_create_business && mode === 'onboarding') {
    return <main className="shell"><div className="content"><OnboardingPage user={currentUser} /></div></main>
  }

  if (currentUser.business_id === null && !startParam && mode !== 'onboarding') {
    return <main className="shell"><div className="content"><WelcomePage canCreateBusiness={currentUser.can_create_business} /></div></main>
  }

  if (currentUser.can_create_business && onboarding.data && !onboarding.data.complete) {
    return <main className="shell"><div className="content"><OnboardingPage user={currentUser} /></div></main>
  }

  return (
    <main className="shell">
      <div className="content">
        <Routes>
          <Route path="/" element={barber ? <DashboardPage /> : <HomePage />} />
          <Route path="/booking" element={!barber ? <BookingPage /> : <Navigate to="/barber" replace />} />
          <Route path="/appointments" element={!barber ? <AppointmentsPage /> : <Navigate to="/barber" replace />} />
          <Route path="/appointments/:id" element={!barber ? <AppointmentDetailsPage /> : <Navigate to="/barber" replace />} />
          <Route path="/profile" element={!barber ? <ProfilePage /> : <Navigate to="/barber" replace />} />
          <Route path="/barber" element={barber ? <DashboardPage /> : <Navigate to="/" replace />} />
          <Route path="/barber/schedule" element={barber ? <SchedulePage /> : <Navigate to="/" replace />} />
          <Route path="/barber/clients" element={barber ? <ClientsPage /> : <Navigate to="/" replace />} />
          <Route path="/barber/services" element={barber ? <ServicesPage /> : <Navigate to="/" replace />} />
          <Route path="/barber/more" element={barber ? <MorePage /> : <Navigate to="/" replace />} />
          <Route path="/barber/team" element={currentUser.role === 'owner' ? <TeamPage /> : <Navigate to="/barber" replace />} />
          <Route path="/barber/settings" element={currentUser.role === 'owner' ? <SettingsPage /> : <Navigate to="/barber" replace />} />
          <Route path="/onboarding" element={currentUser.can_create_business ? <OnboardingPage user={currentUser} /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
      <BottomNav barber={barber} />
    </main>
  )
}

export default function App() {
  const [user, setUser] = useState<Me | null>(null)
  const handleUser = useCallback((nextUser: Me) => setUser(nextUser), [])
  return <QueryClientProvider client={queryClient}><BrowserRouter><AuthGate onUser={handleUser}>{user ? <Shell user={user} /> : <div className="center"><div className="spinner" /><p>Загружаем приложение…</p></div>}</AuthGate></BrowserRouter></QueryClientProvider>
}
