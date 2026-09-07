import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getBarbers, getWorkingHours, saveWorkingHours } from '../../api/data'
import { authenticate } from '../../api/auth'
import { useSearchParams } from 'react-router-dom'

const names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
type Day = { enabled: boolean; start: string; end: string }
const emptyWeek = names.map(() => ({ enabled: false, start: '09:00', end: '18:00' }))

export function SchedulePage() {
  const [params, setParams] = useSearchParams()
  const qc = useQueryClient()
  const me = useQuery({ queryKey: ['me'], queryFn: authenticate })
  const isOwner = me.data?.role === 'owner'
  const barbers = useQuery({ queryKey: ['barbers'], queryFn: getBarbers, enabled: isOwner })
  const selectedParam = Number(params.get('barber')) || 0
  const barberId = isOwner ? (selectedParam || barbers.data?.[0]?.id) : me.data?.member_id
  const query = useQuery({ queryKey: ['working-hours', barberId], queryFn: () => getWorkingHours(barberId!), enabled: Boolean(barberId) })
  const [days, setDays] = useState<Day[]>(emptyWeek.map(x => ({ ...x })))
  const mutation = useMutation({ mutationFn: () => saveWorkingHours(barberId!, days.flatMap((day, weekday) => day.enabled ? [{ weekday, start_time: day.start, end_time: day.end }] : [])), onSuccess: () => qc.invalidateQueries({ queryKey: ['working-hours', barberId] }) })
  useEffect(() => { if (!query.data) return; const next = emptyWeek.map(day => ({ ...day })); for (const interval of query.data) next[interval.weekday] = { enabled: true, start: interval.start_time, end: interval.end_time }; setDays(next) }, [query.data])
  const selected = barbers.data?.find(b => b.id === barberId)
  return <section><div className="eyebrow">РАСПИСАНИЕ</div><div className="section-heading"><div><h1>{selected?.display_name ?? (isOwner ? 'График' : 'Рабочие часы')}</h1><p className="muted">Регулярные часы работы.</p></div>{isOwner && <select className="compact-select" value={barberId ?? ''} onChange={e => setParams({ barber: e.target.value })}>{barbers.data?.map(b => <option key={b.id} value={b.id}>{b.display_name}</option>)}</select>}</div><div className="stack">{days.map((day, weekday) => <div className="day-row" key={weekday}><label className="day-toggle"><input type="checkbox" checked={day.enabled} onChange={e => setDays(current => current.map((x, i) => i === weekday ? { ...x, enabled: e.target.checked } : x))} /><span>{names[weekday]}</span></label><input type="time" disabled={!day.enabled} value={day.start} onChange={e => setDays(current => current.map((x, i) => i === weekday ? { ...x, start: e.target.value } : x))} /><span>—</span><input type="time" disabled={!day.enabled} value={day.end} onChange={e => setDays(current => current.map((x, i) => i === weekday ? { ...x, end: e.target.value } : x))} /></div>)}</div><button className="primary" disabled={mutation.isPending || !days.some(x => x.enabled) || !barberId} onClick={() => mutation.mutate()}>{mutation.isPending ? 'Сохраняем…' : 'Сохранить расписание'}</button>{mutation.isSuccess && <p className="success-text">Расписание сохранено.</p>}{mutation.error && <p className="error">{mutation.error.message}</p>}</section>
}
