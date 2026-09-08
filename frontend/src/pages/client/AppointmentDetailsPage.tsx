import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { cancelAppointment, getMine } from '../../api/data'
import { AppointmentCard } from '../../components/AppointmentCard'

export function AppointmentDetailsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const query = useQuery({ queryKey: ['mine'], queryFn: getMine })
  const mutation = useMutation({ mutationFn: () => cancelAppointment(Number(id)), onSuccess: async () => { await qc.invalidateQueries({ queryKey: ['mine'] }); navigate('/appointments') } })
  const appointment = query.data?.find(x => x.id === Number(id))
  if (query.isLoading) return <p className="muted">Загрузка…</p>
  if (!appointment) return <section><button className="back" onClick={() => navigate(-1)}>← Назад</button><h1>Запись не найдена</h1></section>
  return <section><button className="back" onClick={() => navigate(-1)}>← Назад</button><h1>Моя запись</h1><AppointmentCard appointment={appointment} onCancel={() => mutation.mutate()} /><button className="secondary-button" onClick={() => navigate('/appointments')}>К моим записям</button>{mutation.isError && <p className="error">{mutation.error.message}</p>}</section>
}
