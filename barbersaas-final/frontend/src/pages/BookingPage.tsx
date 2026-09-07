import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMemo, useState } from 'react'
import { createAppointment, getAvailability, getBarbers, getBusiness, getServices } from '../api/data'
import { Notice } from '../components/Notice'

function todayString() {
  return new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
}

export function BookingPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const serviceId = Number(params.get('service'))
  const [date, setDate] = useState(todayString())
  const [barberId, setBarberId] = useState<number | null>(null)
  const [slot, setSlot] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const services = useQuery({ queryKey: ['services'], queryFn: getServices })
  const barbers = useQuery({ queryKey: ['barbers'], queryFn: getBarbers })
  const business = useQuery({ queryKey: ['business'], queryFn: getBusiness })
  const service = services.data?.find(x => x.id === serviceId)
  const activeBarber = barberId ?? barbers.data?.[0]?.id ?? 0
  const availability = useQuery({
    queryKey: ['availability', activeBarber, serviceId, date],
    queryFn: () => getAvailability(activeBarber, serviceId, date),
    enabled: Boolean(activeBarber && serviceId && date),
  })
  const minDate = todayString()
  const maxDate = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() + 90)
    return new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(d)
  }, [])

  async function submit() {
    if (!slot || !service || !activeBarber) return
    setSaving(true)
    try {
      await createAppointment({
        barber_id: activeBarber,
        service_id: service.id,
        // Backend interprets a naive datetime in the business timezone.
        starts_at: `${date}T${slot}:00`,
      })
      navigate('/appointments')
    } catch (e) {
      availability.refetch()
      alert(e instanceof Error ? e.message : 'Не удалось создать запись')
    } finally {
      setSaving(false)
    }
  }

  if (serviceId === 0 || (!services.isLoading && !service)) return <div className="center-card"><h1>Услуга не найдена</h1><button className="secondary-button" onClick={() => navigate('/')}>Вернуться</button></div>

  return (
    <section>
      <button className="back" onClick={() => navigate(-1)}>← Назад</button>
      <div className="eyebrow">НОВАЯ ЗАПИСЬ</div>
      <h1>{service?.name ?? 'Загрузка…'}</h1>
      {service && <div className="card summary"><div><b>{(service.price_minor / 100).toLocaleString('ru-RU')} ₽</b><p className="muted">{service.duration_minutes} мин</p></div><span>{business.data?.name}</span></div>}

      <div className="stack">
        <label className="field"><span>Барбер</span><select value={activeBarber} onChange={e => { setBarberId(Number(e.target.value)); setSlot(null) }}>{barbers.data?.map(b => <option key={b.id} value={b.id}>{b.display_name}</option>)}</select></label>
        <label className="field"><span>Дата</span><input type="date" min={minDate} max={maxDate} value={date} onChange={e => { setDate(e.target.value); setSlot(null) }} /></label>
      </div>

      <div className="section-heading compact-heading"><h2>Свободное время</h2><span className="muted">{availability.data?.timezone ?? business.data?.timezone}</span></div>
      {availability.isError ? <Notice>Не удалось получить свободные слоты.</Notice> : <div className="slots">{availability.isLoading ? <span className="muted">Ищем…</span> : availability.data?.slots.map(s => <button key={s} className={slot === s ? 'slot selected' : 'slot'} onClick={() => setSlot(s)}>{s}</button>)}</div>}
      {!availability.isLoading && availability.data?.slots.length === 0 && <Notice>На эту дату свободных окон нет. Выберите другой день.</Notice>}
      <button className="primary" disabled={!slot || saving} onClick={submit}>{saving ? 'Создаём…' : 'Подтвердить запись'}</button>
    </section>
  )
}
