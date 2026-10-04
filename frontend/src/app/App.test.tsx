import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

const employee = { id: 'c870dc54-5a78-4d52-8978-7b3b83040ed4', username: 'employee', full_name: 'Test Employee', email: 'employee@example.com', role: 'EMPLOYEE', roles: [], capabilities: [], is_active: true, created_at: '2026-09-30T00:00:00Z', updated_at: '2026-09-30T00:00:00Z' }
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status })
const summary = { active: 3, overdue: 1, blocked: 2, completed_recently: 4 }
const dashboard = { my_tasks: { ...summary, total: 5, completed: 2 }, active_projects: [], blocked_tasks: [], engineering: null }
const fixture = (path: string) => path.endsWith('/auth/me') ? employee : path.endsWith('/dashboard') ? dashboard : path.includes('/tasks/summary') ? summary : { status: 'ok' }

function renderApp(path = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>)
}

beforeEach(() => vi.stubGlobal('fetch', vi.fn(async (path: string) => response(fixture(path)))))
afterEach(() => vi.unstubAllGlobals())

describe('authenticated shell', () => {
  it('shows real component records and labelled motor specifications to engineers', async () => {
    const engineer = { ...employee, role: 'ENGINEER', roles: ['ENGINEER', 'RND_ENGINEER'], capabilities: ['VIEW_ALL_PROJECTS', 'MANAGE_TASKS', 'VIEW_ENGINEERING', 'MANAGE_ENGINEERING', 'VIEW_RND_DASHBOARD'] }
    const component = { id: '82cd83f9-f27f-48fd-a0ea-c4133a8d8f67', category: 'MOTOR', manufacturer: 'Acme', model: 'M1', name: 'Тестовий двигун', description: '', specifications: { kv: 900 }, datasheet_url: null, notes: '', created_at: '2026-09-30T00:00:00Z', updated_at: '2026-09-30T00:00:00Z' }
    vi.stubGlobal('fetch', vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(engineer) : path.includes('/components?') ? response({ items: [component], total: 1, page: 1, page_size: 20 }) : path.endsWith(`/components/${component.id}`) ? response(component) : response({ status: 'ok' })))
    renderApp('/components')
    fireEvent.click(await screen.findByRole('link', { name: 'Тестовий двигун' }))
    expect(await screen.findByText('KV (об/хв/В)')).toBeInTheDocument()
    expect(screen.getByText('900')).toBeInTheDocument()
  })
  it('hides engineering navigation from employees and denies direct routes', async () => {
    renderApp('/setups')
    expect(await screen.findByRole('alert')).toHaveTextContent('Конфігурації доступні')
    expect(screen.getByRole('link', { name: 'R&D' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Admin Settings' })).not.toBeInTheDocument()
  })
  it('shows persisted tests to engineers and filters the API by status', async () => {
    const engineer = { ...employee, role: 'ENGINEER', roles: ['ENGINEER', 'RND_ENGINEER'], capabilities: ['VIEW_ALL_PROJECTS', 'MANAGE_TASKS', 'VIEW_ENGINEERING', 'MANAGE_ENGINEERING', 'VIEW_RND_DASHBOARD'] }
    const test = { id: 'eef2acb0-6765-47f7-8e81-43efea590739', name: 'Стенд двигуна', test_type: 'MOTOR_BENCH', status: 'PLANNED', project_id: null, setup_id: null, component_id: null, firmware_revision_id: null, performed_by_id: null, test_date: null, description: '', conditions: {}, result_summary: {}, conclusion: '', created_at: '2026-09-30T00:00:00Z', updated_at: '2026-09-30T00:00:00Z' }
    const fetchMock = vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(engineer) : path.includes('/tests?') ? response({ items: [test], total: 1, page: 1, page_size: 20 }) : response({ status: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/tests')
    expect(await screen.findByRole('link', { name: 'Стенд двигуна' })).toBeInTheDocument()
    fireEvent.change(screen.getByRole('combobox', { name: 'Статус випробування' }), { target: { value: 'PLANNED' } })
    await waitFor(() => expect(fetchMock.mock.calls.some(([path]) => path.includes('/tests?') && path.includes('status=PLANNED'))).toBe(true))
  })
  it('requires a setup before creating a flight test', async () => {
    const engineer = { ...employee, role: 'ENGINEER', roles: ['ENGINEER', 'RND_ENGINEER'], capabilities: ['VIEW_ALL_PROJECTS', 'MANAGE_TASKS', 'VIEW_ENGINEERING', 'MANAGE_ENGINEERING', 'VIEW_RND_DASHBOARD'] }
    let posted = false
    const fetchMock = vi.fn(async (path: string, options?: RequestInit) => { if (options?.method === 'POST') posted = true; return path.endsWith('/auth/me') ? response(engineer) : response([]) })
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/tests/new?test_type=FLIGHT')
    fireEvent.change(await screen.findByLabelText('Назва'), { target: { value: 'Пробний політ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Зберегти випробування' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Для польоту оберіть сетап')
    expect(posted).toBe(false)
  })
  it('keeps navigation on unknown routes', async () => {
    renderApp('/unknown')
    expect(await screen.findByRole('heading', { name: 'Сторінку не знайдено' })).toBeInTheDocument()
    expect(screen.getByRole('navigation')).toBeInTheDocument()
  })
  it('reports API readiness', async () => {
    renderApp()
    expect(await screen.findByText('Система доступна')).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /Активні задачі/ })).toHaveTextContent('3')
    expect(screen.getByRole('link', { name: /Заблоковані/ })).toHaveTextContent('2')
  })
  it('submits customer and order creation from Production', async () => {
    const administrator = { ...employee, role: 'ADMIN', roles: ['ADMINISTRATOR'], capabilities: ['VIEW_PRODUCTION', 'MANAGE_ORDERS', 'MANAGE_PROCUREMENT'] }
    const customerId = '91c7b840-d713-4aac-a220-7bfc7909cfd6'
    const orderId = 'd41c1e54-2cf7-4bc4-85ef-d9756558f8ab'
    const customers: unknown[] = []
    const orders: unknown[] = []
    const posts: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (path: string, options?: RequestInit) => {
      if (path.endsWith('/auth/me')) return response(administrator)
      if (path.endsWith('/orders/customers') && options?.method === 'POST') {
        posts.push(path)
        const customer = { id: customerId, name: 'ТОВ Тест', contact_details: '+380000000000', notes: '', created_at: '2026-10-03T00:00:00Z', updated_at: '2026-10-03T00:00:00Z' }
        customers.push(customer)
        return response(customer, 201)
      }
      if (path.endsWith('/orders/customers')) return response(customers)
      if (path.endsWith('/orders') && options?.method === 'POST') {
        posts.push(path)
        const order = { id: orderId, order_number: 'ORD-001', customer_id: customerId, customer_name: 'ТОВ Тест', recipient: '', destination: '', order_date: '2026-10-03', deadline: null, notes: '', status: 'DRAFT', created_by_id: employee.id, created_at: '2026-10-03T00:00:00Z', updated_at: '2026-10-03T00:00:00Z' }
        orders.push(order)
        return response(order, 201)
      }
      if (path.includes('/orders?')) return response({ items: orders, total: orders.length, page: 1, page_size: 100 })
      if (path.includes('/procurement?')) return response({ items: [], total: 0, page: 1, page_size: 100 })
      if (path.endsWith('/procurement/suppliers') || path.endsWith('/components/options')) return response([])
      return response({ status: 'ok' })
    }))
    renderApp('/production')
    fireEvent.click(await screen.findByRole('button', { name: 'Новий замовник' }))
    fireEvent.change(screen.getByLabelText('Назва замовника'), { target: { value: 'ТОВ Тест' } })
    fireEvent.click(screen.getByRole('button', { name: 'Створити замовника' }))
    await waitFor(() => expect(posts).toContain('/api/orders/customers'))
    fireEvent.click(screen.getByRole('button', { name: 'Нове замовлення' }))
    fireEvent.change(await screen.findByLabelText('Номер'), { target: { value: 'ORD-001' } })
    fireEvent.click(screen.getByRole('button', { name: /^Створити$/ }))
    await waitFor(() => expect(posts).toContain('/api/orders'))
    expect(await screen.findByRole('link', { name: 'ORD-001' })).toBeInTheDocument()
  })
  it('retries an unavailable backend', async () => {
    let healthy = false
    vi.stubGlobal('fetch', vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(employee) : healthy ? response(fixture(path)) : response({}, 503)))
    renderApp()
    expect(await screen.findByText('З’єднання недоступне')).toBeInTheDocument()
    healthy = true
    fireEvent.click(screen.getByRole('button', { name: 'Перевірити з’єднання' }))
    expect(await screen.findByText('Система доступна')).toBeInTheDocument()
  })
  it('redirects unauthenticated visitors to login', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ detail: 'Unauthorized' }, 401)))
    renderApp('/projects')
    expect(await screen.findByRole('heading', { name: 'Вхід до робочого простору' })).toBeInTheDocument()
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })
  it('blocks employee access to admin page', async () => {
    renderApp('/users')
    expect(await screen.findByRole('heading', { name: 'Доступ обмежено' })).toBeInTheDocument()
  })
  it('leaves protected content immediately after logout', async () => {
    let loggedIn = true
    vi.stubGlobal('fetch', vi.fn(async (path: string) => {
      if (path.endsWith('/auth/logout')) { loggedIn = false; return new Response(null, { status: 204 }) }
      if (path.endsWith('/auth/me') && !loggedIn) return response({}, 401)
      return response(fixture(path))
    }))
    renderApp('/setups')
    fireEvent.click(await screen.findByRole('button', { name: 'Вийти' }))
    expect(await screen.findByRole('heading', { name: 'Вхід до робочого простору' })).toBeInTheDocument()
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })
  it('leaves protected content when an API request rejects the session', async () => {
    let expired = false
    vi.stubGlobal('fetch', vi.fn(async (path: string) => {
      if (path.endsWith('/auth/me') && !expired) return response(employee)
      expired = true
      return response({}, 401)
    }))
    renderApp()
    expect(await screen.findByRole('heading', { name: 'Вхід до робочого простору' })).toBeInTheDocument()
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })
  it('shows login errors without pretending success', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response({ detail: 'Невірний логін або пароль.' }, 401)))
    renderApp('/login')
    fireEvent.change(await screen.findByLabelText('Логін'), { target: { value: 'employee' } })
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'wrong-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Увійти' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Невірний логін або пароль.')
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
  })
})
