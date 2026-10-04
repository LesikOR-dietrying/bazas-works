import { useQuery } from '@tanstack/react-query'
import { Activity, RefreshCw } from 'lucide-react'
import { getJson } from '../../api/client'

async function getReadiness(signal: AbortSignal): Promise<{ status: 'ok' }> {
  const data = await getJson('/health/ready', signal)
  if (typeof data !== 'object' || data === null || !('status' in data) || data.status !== 'ok') {
    throw new Error('Unexpected readiness response')
  }
  return { status: 'ok' }
}

export function SystemStatus() {
  const query = useQuery({
    queryKey: ['system', 'readiness'],
    queryFn: ({ signal }) => getReadiness(signal),
    refetchInterval: 30_000,
  })
  const status = query.isPending ? 'Перевіряємо з’єднання…' : query.isError ? 'З’єднання недоступне' : 'Система доступна'

  return (
    <section className="system-status" aria-label="Стан системи">
      <Activity size={20} aria-hidden="true" />
      <div role="status">
        <strong>{status}</strong>
        <p>{query.isError ? 'Не вдалося підтвердити готовність сервера. Спробуйте ще раз.' : 'Стан підключення оновлюється автоматично.'}</p>
      </div>
      <button className="icon-button" onClick={() => void query.refetch()} disabled={query.isFetching} aria-label="Перевірити з’єднання">
        <RefreshCw size={17} className={query.isFetching ? 'animate-spin' : ''} />
      </button>
    </section>
  )
}
