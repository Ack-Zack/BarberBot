import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createClient, getClients } from '../../api/data'
import type { Client } from '../../types/api'
import { ClientDetailsPage } from './ClientDetailsPage'

export function ClientsPage() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['clients'], queryFn: getClients })
  const [selected, setSelected] = useState<Client | null>(null)
  const [adding, setAdding] = useState(false)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const mutation = useMutation({ mutationFn: () => createClient({ name: name.trim(), phone: phone.trim() || undefined }), onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['clients'] }); setAdding(false); setName(''); setPhone('') } })
  if (selected) return <ClientDetailsPage client={selected} onBack={() => setSelected(null)} />
  return <section><div className="section-heading"><div><div className="eyebrow">БАЗА</div><h1>Клиенты</h1></div><button className="ghost" onClick={() => setAdding(true)}>+ Добавить</button></div>{adding && <div className="card stack"><label className="field"><span>Имя</span><input value={name} onChange={e => setName(e.target.value)} autoFocus /></label><label className="field"><span>Телефон</span><input value={phone} onChange={e => setPhone(e.target.value)} /></label><div className="two-cols"><button className="secondary-button" onClick={() => setAdding(false)}>Отмена</button><button className="primary" disabled={!name.trim() || mutation.isPending} onClick={() => mutation.mutate()}>{mutation.isPending ? 'Сохраняем…' : 'Сохранить'}</button></div>{mutation.error && <p className="error">{mutation.error.message}</p>}</div>}<div className="stack">{q.isLoading && <p className="muted">Загрузка…</p>}{q.data?.map(c => <button className="card list-row" key={c.id} onClick={() => setSelected(c)}><div><b>{c.name}</b><p className="muted">{c.phone || 'Telegram'} · {c.appointments_count} записей</p></div><span>›</span></button>)}</div>{!q.isLoading && !q.data?.length && <p className="muted">Клиентов пока нет.</p>}</section>
}
