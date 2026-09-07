import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMe } from '../../api/data'

export function MorePage() {
  const me = useQuery({ queryKey: ['me'], queryFn: getMe })
  const owner = me.data?.role === 'owner'
  return <section><div className="eyebrow">ПАНЕЛЬ</div><h1>Ещё</h1><div className="stack"><Link className="card link-row" to="/barber/services"><div><b>Услуги</b><span className="muted">Цены и длительность</span></div><span>›</span></Link><Link className="card link-row" to="/barber/schedule"><div><b>Рабочие часы</b><span className="muted">Регулярное расписание</span></div><span>›</span></Link>{owner && <><Link className="card link-row" to="/barber/team"><div><b>Мастера</b><span className="muted">Пригласить и отключить</span></div><span>›</span></Link><Link className="card link-row" to="/barber/settings"><div><b>Бизнес</b><span className="muted">Название, часовой пояс, ссылка</span></div><span>›</span></Link></>}</div></section>
}
