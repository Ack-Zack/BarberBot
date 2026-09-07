import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getBusiness, getBarbers, getServices } from '../api/data'

export function HomePage() {
  const navigate = useNavigate()
  const business = useQuery({ queryKey: ['business'], queryFn: getBusiness })
  const services = useQuery({ queryKey: ['services'], queryFn: getServices })
  const barbers = useQuery({ queryKey: ['barbers'], queryFn: getBarbers })
  return (
    <section>
      <div className="hero hero-booking">
        <div className="eyebrow">{business.data?.name ?? 'BARBERSAAS'}</div>
        <h1>Запишитесь на удобное время</h1>
        <p className="muted">Выберите услугу — свободные слоты покажем автоматически.</p>
        {barbers.data && barbers.data.length > 1 && <p className="muted">Мастеров: {barbers.data.length}</p>}
      </div>
      <h2>Услуги</h2>
      {services.isLoading ? <p className="muted">Загрузка…</p> : services.isError ? <p className="error">{services.error.message}</p> : (
        <div className="stack">
          {services.data?.map(service => (
            <button className="card service" key={service.id} onClick={() => navigate(`/booking?service=${service.id}`)}>
              <div><b>{service.name}</b><p className="muted">{service.duration_minutes} мин</p></div>
              <b>{(service.price_minor / 100).toLocaleString('ru-RU')} ₽</b>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
