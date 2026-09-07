import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getMine } from '../api/data'
import { AppointmentCard } from '../components/AppointmentCard'

export function AppointmentsPage() {
  const navigate = useNavigate()
  const q = useQuery({ queryKey: ['mine'], queryFn: getMine })
  return <section><div className="section-heading"><div><div className="eyebrow">КЛИЕНТ</div><h1>Мои записи</h1></div><button className="ghost" onClick={() => navigate('/')}>Новая</button></div>{q.isLoading && <p className="muted">Загрузка…</p>}<div className="stack">{q.data?.map(a => <div key={a.id} className="clickable" role="button" tabIndex={0} onClick={() => navigate(`/appointments/${a.id}`)} onKeyDown={e => { if (e.key === 'Enter') navigate(`/appointments/${a.id}`) }}><AppointmentCard appointment={a} /></div>)}</div>{!q.isLoading && !q.data?.length && <div className="empty-page"><p>Записей пока нет.</p><button className="primary" onClick={() => navigate('/')}>Выбрать услугу</button></div>}</section>
}
