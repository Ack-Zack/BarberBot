import type { Appointment } from '../types/api'

const labels: Record<string, string> = { pending: 'Ожидает', confirmed: 'Подтверждено', completed: 'Завершено', cancelled: 'Отменено', no_show: 'Не пришёл' }

export function formatDateTime(value: string) {
  const date = new Date(value)
  return { date: date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }), time: date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) }
}

export function AppointmentCard({ appointment, onCancel, onComplete, onReschedule, staff = false }: { appointment: Appointment; onCancel?: () => void; onComplete?: () => void; onReschedule?: () => void; staff?: boolean }) {
  const dt = formatDateTime(appointment.starts_at)
  return <article className="card appointment-card"><div className="appointment-main"><div className="appointment-time">{dt.time}</div><div><b>{appointment.service_name ?? `Запись #${appointment.id}`}</b><p className="muted">{dt.date} · {appointment.duration_minutes} мин</p></div></div><div className="appointment-meta"><span className={`status status-${appointment.status}`}>{labels[appointment.status] ?? appointment.status}</span><span className="muted">{(appointment.price_minor / 100).toLocaleString('ru-RU')} ₽</span></div>{staff && appointment.client_name && <p className="muted">Клиент: {appointment.client_name}</p>}{!staff && appointment.barber_name && <p className="muted">Барбер: {appointment.barber_name}</p>}{staff && ['pending', 'confirmed'].includes(appointment.status) && <div className="button-row">{onReschedule && <button className="secondary-button compact" onClick={onReschedule}>Перенести</button>}{onComplete && <button className="secondary-button compact" onClick={onComplete}>Завершить</button>}{onCancel && <button className="secondary-button compact danger-button" onClick={onCancel}>Отменить</button>}</div>}{!staff && onCancel && ['pending', 'confirmed'].includes(appointment.status) && <button className="secondary-button compact danger-button" onClick={onCancel}>Отменить</button>}</article>
}
