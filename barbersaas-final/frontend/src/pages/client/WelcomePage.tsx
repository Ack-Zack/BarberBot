import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getOnboardingStatus } from '../../api/data'

export function WelcomePage({ canCreateBusiness }: { canCreateBusiness: boolean }) {
  const navigate = useNavigate()
  const status = useQuery({ queryKey: ['onboarding'], queryFn: getOnboardingStatus, enabled: canCreateBusiness })
  return (
    <section className="center-card">
      <div className="eyebrow">BARBERSAAS</div>
      <h1>Запись без переписки</h1>
      <p className="muted">Для записи откройте ссылку от вашего барбера. Владелец может настроить свой бизнес прямо в Mini App.</p>
      {canCreateBusiness && (
        <button className="primary" disabled={status.isLoading} onClick={() => navigate('/onboarding')}>
          Создать бизнес
        </button>
      )}
    </section>
  )
}
