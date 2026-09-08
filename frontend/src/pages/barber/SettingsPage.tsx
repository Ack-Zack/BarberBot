import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getBookingLink, getBusiness, updateBusiness } from '../../api/data'

export function SettingsPage() {
  const qc = useQueryClient()
  const business = useQuery({ queryKey: ['business'], queryFn: getBusiness })
  const link = useQuery({ queryKey: ['booking-link'], queryFn: getBookingLink })
  const [name, setName] = useState('')
  const [timezone, setTimezone] = useState('Europe/Moscow')
  useEffect(() => { if (business.data) { setName(business.data.name); setTimezone(business.data.timezone) } }, [business.data])
  const mutation = useMutation({ mutationFn: () => updateBusiness({ name: name.trim(), timezone }), onSuccess: () => qc.invalidateQueries({ queryKey: ['business'] }) })
  return <section><div className="eyebrow">БИЗНЕС</div><h1>Настройки</h1><div className="card stack"><label className="field"><span>Название</span><input value={name} onChange={e => setName(e.target.value)} /></label><label className="field"><span>Часовой пояс</span><select value={timezone} onChange={e => setTimezone(e.target.value)}><option value="Europe/Moscow">Москва · UTC+3</option><option value="Europe/Stockholm">Стокгольм</option><option value="Asia/Yekaterinburg">Екатеринбург</option><option value="Asia/Novosibirsk">Новосибирск</option></select></label><button className="primary" disabled={!name.trim() || mutation.isPending} onClick={() => mutation.mutate()}>{mutation.isPending ? 'Сохраняем…' : 'Сохранить'}</button>{mutation.isSuccess && <p className="success-text">Сохранено.</p>}{mutation.error && <p className="error">{mutation.error.message}</p>}</div><h2>Ссылка для записи</h2><div className="card">{link.data?.url ? <><div className="share-link">{link.data.url}</div><button className="primary" onClick={() => navigator.clipboard?.writeText(link.data!.url)}>Скопировать ссылку</button></> : <p className="muted">Настройте TELEGRAM_BOT_USERNAME.</p>}</div></section>
}
