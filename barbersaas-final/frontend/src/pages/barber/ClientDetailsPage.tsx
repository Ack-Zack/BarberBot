import { useQuery } from '@tanstack/react-query'
import { getClientHistory } from '../../api/data'
import type { Client } from '../../types/api'
import { AppointmentCard } from '../../components/AppointmentCard'

export function ClientDetailsPage({ client, onBack }: { client: Client; onBack: () => void }) {
  const history = useQuery({ queryKey: ['client-history', client.id], queryFn: () => getClientHistory(client.id) })
  return <section><button className="back" onClick={onBack}>← Клиенты</button><div className="eyebrow">КЛИЕНТ</div><h1>{client.name}</h1><div className="card profile-lines"><p><span className="muted">Телефон</span><b>{client.phone || 'Не указан'}</b></p><p><span className="muted">Посещений</span><b>{client.appointments_count}</b></p><p><span className="muted">Последняя запись</span><b>{client.last_appointment_at ? new Date(client.last_appointment_at).toLocaleDateString('ru-RU') : '—'}</b></p>{client.notes && <p><span className="muted">Заметки</span><b>{client.notes}</b></p>}</div><h2>История</h2><div className="stack">{history.data?.map(a => <AppointmentCard key={a.id} appointment={a} staff />)}</div>{history.isLoading && <p className="muted">Загрузка…</p>}</section>
}
