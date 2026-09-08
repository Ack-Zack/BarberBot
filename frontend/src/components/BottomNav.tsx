import { NavLink } from 'react-router-dom'

export function BottomNav({ barber }: { barber: boolean }) {
  const items = barber
    ? [['/barber', 'Сегодня'], ['/barber/schedule', 'Расписание'], ['/barber/clients', 'Клиенты'], ['/barber/more', 'Ещё']]
    : [['/', 'Главная'], ['/appointments', 'Записи'], ['/profile', 'Профиль']]

  return (
    <nav className="bottom-nav">
      {items.map(([to, label]) => (
        <NavLink key={to} to={to} end={to === '/barber' || to === '/'} className={({ isActive }) => isActive ? 'nav active' : 'nav'}>
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
