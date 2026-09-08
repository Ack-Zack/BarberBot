import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createService, getServices, updateService } from '../../api/data'
import type { Service } from '../../types/api'

export function ServicesPage() {
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['services'], queryFn: getServices })
  const [editing, setEditing] = useState<Service | null>(null)
  const [creating, setCreating] = useState(false)
  const [name, setName] = useState('')
  const [duration, setDuration] = useState(60)
  const [price, setPrice] = useState('1500')
  const [active, setActive] = useState(true)
  const reset = () => { setEditing(null); setCreating(false); setName(''); setDuration(60); setPrice('1500'); setActive(true) }
  const createMutation = useMutation({ mutationFn: () => createService({ name: name.trim(), duration_minutes: duration, price_minor: Math.round(Number(price) * 100), currency: 'RUB' }), onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['services'] }); reset() } })
  const editMutation = useMutation({ mutationFn: () => updateService(editing!.id, { name: name.trim(), duration_minutes: duration, price_minor: Math.round(Number(price) * 100), currency: editing!.currency, is_active: active }), onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['services'] }); reset() } })
  const openEdit = (service: Service) => { setEditing(service); setName(service.name); setDuration(service.duration_minutes); setPrice(String(service.price_minor / 100)); setActive(service.is_active) }
  const form = (title: string, submit: () => void, loading: boolean) => <div className="card stack"><div className="section-heading"><h2>{title}</h2><button className="ghost" onClick={reset}>×</button></div><label className="field"><span>Название</span><input value={name} onChange={e => setName(e.target.value)} autoFocus /></label><div className="two-cols"><label className="field"><span>Минуты</span><input type="number" min="15" max="480" step="15" value={duration} onChange={e => setDuration(Number(e.target.value))} /></label><label className="field"><span>Цена, ₽</span><input type="number" min="0" step="50" value={price} onChange={e => setPrice(e.target.value)} /></label></div>{editing && <label className="day-toggle"><input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} /><span>Услуга активна</span></label>}<button className="primary" disabled={!name.trim() || duration <= 0 || Number(price) < 0 || loading} onClick={submit}>{loading ? 'Сохраняем…' : 'Сохранить'}</button></div>
  return <section><div className="section-heading"><div><div className="eyebrow">КАТАЛОГ</div><h1>Услуги</h1></div><button className="ghost" onClick={() => { reset(); setCreating(true) }}>+ Добавить</button></div>{(creating || editing) && form(editing ? 'Редактировать услугу' : 'Новая услуга', editing ? () => editMutation.mutate() : () => createMutation.mutate(), createMutation.isPending || editMutation.isPending)}<div className="stack">{q.data?.map(s => <button className="card list-row" key={s.id} onClick={() => openEdit(s)}><div><b>{s.name}</b><p className="muted">{s.duration_minutes} мин · {(s.price_minor / 100).toLocaleString('ru-RU')} ₽{!s.is_active && ' · выключена'}</p></div><span>›</span></button>)}</div></section>
}
