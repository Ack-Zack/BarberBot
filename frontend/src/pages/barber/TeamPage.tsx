import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createBarberInvite, deactivateBarber, getBarbers } from '../../api/data'
import { useNavigate } from 'react-router-dom'

export function TeamPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['barbers'], queryFn: getBarbers })
  const [invite, setInvite] = useState<{ url: string; expires_at: string } | null>(null)
  const mutation = useMutation({ mutationFn: () => createBarberInvite(), onSuccess: setInvite })
  const remove = useMutation({ mutationFn: deactivateBarber, onSuccess: () => qc.invalidateQueries({ queryKey: ['barbers'] }) })
  return <section><button className="back" onClick={() => navigate('/barber/more')}>← Ещё</button><div className="section-heading"><div><div className="eyebrow">КОМАНДА</div><h1>Мастера</h1></div><button className="ghost" disabled={mutation.isPending} onClick={() => mutation.mutate()}>+ Пригласить</button></div>{invite && <div className="success-card"><b>Ссылка для мастера</b><p className="muted">Действует до {new Date(invite.expires_at).toLocaleDateString('ru-RU')}.</p><div className="share-link">{invite.url}</div><button className="primary" onClick={() => navigator.clipboard?.writeText(invite.url)}>Скопировать</button></div>}<div className="stack">{q.data?.map(barber => <div className="card list-row" key={barber.id}><div><b>{barber.display_name}</b><p className="muted">{barber.role === 'owner' ? 'Владелец' : 'Барбер'}</p></div><div className="button-row">{barber.role !== 'owner' && <button className="ghost small-danger" disabled={remove.isPending} onClick={() => remove.mutate(barber.id)}>Отключить</button>}<button className="ghost" onClick={() => navigate(`/barber/schedule?barber=${barber.id}`)}>График</button></div></div>)}</div>{!q.isLoading && !q.data?.length && <p className="muted">Мастеров нет.</p>}{mutation.error && <p className="error">{mutation.error.message}</p>}{remove.error && <p className="error">{remove.error.message}</p>}</section>
}
