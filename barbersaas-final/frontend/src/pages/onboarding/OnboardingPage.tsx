import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createBusiness, createService, getBookingLink, getMe, getOnboardingStatus, saveWorkingHours } from '../../api/data'
import type { Me } from '../../types/api'

const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
type Day = { enabled: boolean; start: string; end: string }
const defaults = dayNames.map((_, i) => ({ enabled: i < 5, start: '09:00', end: '18:00' }))

export function OnboardingPage({ user }: { user: Me }) {
  const qc = useQueryClient()
  const currentUser = useQuery({ queryKey: ['me'], queryFn: getMe })
  const me = currentUser.data ?? user
  const status = useQuery({ queryKey: ['onboarding'], queryFn: getOnboardingStatus })
  const share = useQuery({ queryKey: ['booking-link'], queryFn: getBookingLink, enabled: Boolean(status.data?.complete) })
  const [name, setName] = useState('')
  const [timezone, setTimezone] = useState('Europe/Moscow')
  const [serviceName, setServiceName] = useState('Мужская стрижка')
  const [duration, setDuration] = useState(60)
  const [price, setPrice] = useState('1500')
  const [days, setDays] = useState<Day[]>(defaults.map(x => ({ ...x })))
  const [step, setStep] = useState<number | null>(null)

  const createBusinessMutation = useMutation({
    mutationFn: () => createBusiness({ name: name.trim(), timezone }),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['me'] }); await qc.invalidateQueries({ queryKey: ['onboarding'] }) },
  })
  const createServiceMutation = useMutation({
    mutationFn: () => createService({ name: serviceName.trim(), duration_minutes: duration, price_minor: Math.round(Number(price) * 100), currency: 'RUB' }),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['onboarding'] }) },
  })
  const saveScheduleMutation = useMutation({
    mutationFn: () => saveWorkingHours(me.member_id!, days.flatMap((day, weekday) => day.enabled ? [{ weekday, start_time: day.start, end_time: day.end }] : [])),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['onboarding'] }); await qc.invalidateQueries({ queryKey: ['me'] }) },
  })

  useEffect(() => {
    if (!status.data) return
    if (status.data.complete) { setStep(4); return }
    if (!status.data.business_id) setStep(1)
    else if (!status.data.has_service) setStep(2)
    else if (!status.data.has_working_hours) setStep(3)
  }, [status.data])

  async function nextFromStep() {
    if (step === 1) { await createBusinessMutation.mutateAsync(); setStep(2) }
    else if (step === 2) { await createServiceMutation.mutateAsync(); setStep(3) }
    else if (step === 3) { await saveScheduleMutation.mutateAsync(); setStep(4) }
  }

  if (status.isLoading || currentUser.isLoading || step === null) return <div className="center"><div className="spinner" /><p>Готовим настройку…</p></div>

  const error = createBusinessMutation.error ?? createServiceMutation.error ?? saveScheduleMutation.error
  return (
    <section>
      <div className="eyebrow">BARBERSAAS • НАСТРОЙКА</div>
      <div className="progress"><span style={{ width: `${step * 25}%` }} /></div>
      <p className="step-label">Шаг {step} из 4</p>
      <h1>{['Ваш бизнес', 'Первая услуга', 'Рабочее время', 'Готово'][step - 1]}</h1>
      <p className="muted">Настройте только необходимое — остальное можно изменить позже.</p>

      {step === 1 && <div className="stack"><label className="field"><span>Название бизнеса</span><input value={name} onChange={e => setName(e.target.value)} placeholder="Black Beard" autoFocus /></label><label className="field"><span>Часовой пояс</span><select value={timezone} onChange={e => setTimezone(e.target.value)}><option value="Europe/Moscow">Москва · UTC+3</option><option value="Europe/Stockholm">Стокгольм · UTC+2/+1</option><option value="Asia/Yekaterinburg">Екатеринбург · UTC+5</option><option value="Asia/Novosibirsk">Новосибирск · UTC+7</option></select></label><button className="primary" disabled={!name.trim() || createBusinessMutation.isPending} onClick={nextFromStep}>Продолжить</button></div>}
      {step === 2 && <div className="stack"><label className="field"><span>Название услуги</span><input value={serviceName} onChange={e => setServiceName(e.target.value)} autoFocus /></label><div className="two-cols"><label className="field"><span>Длительность, мин</span><input type="number" min="15" max="480" step="15" value={duration} onChange={e => setDuration(Number(e.target.value))} /></label><label className="field"><span>Цена, ₽</span><input type="number" min="0" step="50" value={price} onChange={e => setPrice(e.target.value)} /></label></div><button className="primary" disabled={!serviceName.trim() || duration <= 0 || Number(price) < 0 || createServiceMutation.isPending} onClick={nextFromStep}>Добавить услугу</button></div>}
      {step === 3 && <div className="stack">{days.map((day, weekday) => <div className="day-row" key={weekday}><label className="day-toggle"><input type="checkbox" checked={day.enabled} onChange={e => setDays(current => current.map((x, i) => i === weekday ? { ...x, enabled: e.target.checked } : x))} /><span>{dayNames[weekday]}</span></label><input type="time" disabled={!day.enabled} value={day.start} onChange={e => setDays(current => current.map((x, i) => i === weekday ? { ...x, start: e.target.value } : x))} /><span>—</span><input type="time" disabled={!day.enabled} value={day.end} onChange={e => setDays(current => current.map((x, i) => i === weekday ? { ...x, end: e.target.value } : x))} /></div>)}<button className="primary" disabled={!days.some(x => x.enabled) || saveScheduleMutation.isPending || !me.member_id} onClick={nextFromStep}>Сохранить расписание</button></div>}
      {step === 4 && <div className="success-card"><div className="success-icon">✓</div><h2>Бизнес готов</h2><p className="muted">Отправьте ссылку клиентам. Она откроет ваш Telegram Mini App с нужным бизнесом.</p>{share.isLoading && <p className="muted">Готовим ссылку…</p>}{share.data?.url && <><div className="share-link">{share.data.url}</div><button className="primary" onClick={() => navigator.clipboard?.writeText(share.data!.url)}>Скопировать</button><a className="secondary-button" href={share.data.url} target="_blank" rel="noreferrer">Открыть</a></>}{!share.data?.url && !share.isLoading && <p className="muted">Настройте TELEGRAM_BOT_USERNAME в .env.</p>}</div>}
      {error && <p className="error">{error.message}</p>}
    </section>
  )
}
