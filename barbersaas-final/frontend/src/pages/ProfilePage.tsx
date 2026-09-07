import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/data'

export function ProfilePage() {
  const q = useQuery({ queryKey: ['me'], queryFn: getMe })
  const user = q.data
  return <section><div className="eyebrow">АККАУНТ</div><h1>Профиль</h1><div className="card profile-card"><div className="avatar">{user?.first_name?.[0]?.toUpperCase() ?? '?'}</div><div><b>{user?.display_name}</b><p className="muted">{user?.username ? '@' + user.username : 'Telegram'}</p></div></div></section>
}
