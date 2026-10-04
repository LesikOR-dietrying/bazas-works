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
    expect(screen.getByRole('link', { name: 'Розробка' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Продукція' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Користувачі' })).not.toBeInTheDocument()
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
    expect(screen.getByRole('navigation', { name: 'Основні розділи' })).toBeInTheDocument()
  })
  it('reports API readiness', async () => {
    renderApp()
    expect(await screen.findByText('Система доступна')).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /Активні задачі/ })).toHaveTextContent('3')
    expect(screen.getByRole('link', { name: /Заблоковані/ })).toHaveTextContent('2')
  })
  it('submits customer and order creation from Orders', async () => {
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
    renderApp('/orders')
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
  it('shows product configurations and creates a new one', async () => {
    const engineer = { ...employee, role: 'ENGINEER', roles: ['ENGINEER'], capabilities: ['VIEW_ENGINEERING', 'MANAGE_ENGINEERING'] }
    const productId = 'd41c1e54-2cf7-4bc4-85ef-d9756558f8ab'
    const variantId = '7ed6fb59-350e-4d2c-8b52-c61cc0c2c457'
    const posts: string[] = []
    vi.stubGlobal('fetch', vi.fn(async (path: string, options?: RequestInit) => {
      if (path.endsWith('/auth/me')) return response(engineer)
      if (path.endsWith(`/products/${productId}/variants`) && options?.method === 'POST') { posts.push(path); return response({ id: 'new-variant', product_id: productId, code: 'FIELD', name: 'Польова', description: '', is_active: true, current_revision_id: null, created_at: '', updated_at: '' }, 201) }
      if (path.endsWith(`/products/${productId}/variants`)) return response([{ id: variantId, product_id: productId, code: 'STANDARD', name: 'Стандартна', description: '', is_active: true, current_revision_id: null, created_at: '', updated_at: '' }])
      if (path.endsWith(`/products/${productId}/revisions`)) return response([{ id: 'revision-id', product_id: productId, product_name: 'Розвідник', variant_id: variantId, variant_name: 'Стандартна', revision_code: 'R1', status: 'DRAFT', technical_characteristics: {}, standard_cost: null, currency: 'UAH', revision_instructions: '', source_setup_id: null, source_branch_id: null, source_project_id: null, released_at: null, created_at: '', updated_at: '' }])
      if (path.endsWith(`/products/${productId}`)) return response({ id: productId, code: 'UAV-1', name: 'Розвідник', category_id: 'category', category_name: 'БПЛА', description: '', lifecycle: 'DEVELOPMENT', tracking_mode: 'SERIAL', current_revision_id: null, general_image_attachment_id: null, variant_count: 1, created_at: '', updated_at: '' })
      return response({ status: 'ok' })
    }))
    renderApp(`/products/${productId}`)
    expect(await screen.findByRole('combobox', { name: 'Комплектація' })).toHaveValue(variantId)
    expect(screen.getByText('Не розраховано')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Версії' }))
    fireEvent.change(screen.getByPlaceholderText('Код комплектації'), { target: { value: 'FIELD' } })
    fireEvent.change(screen.getByPlaceholderText('Назва комплектації'), { target: { value: 'Польова' } })
    fireEvent.click(screen.getByRole('button', { name: 'Створити комплектацію' }))
    await waitFor(() => expect(posts).toContain(`/api/products/${productId}/variants`))
  })
  it('shows execution data on Production without planning forms', async () => {
    const manager = { ...employee, role: 'MANAGER', roles: ['PRODUCTION_MANAGER'], capabilities: ['VIEW_PRODUCTION', 'MANAGE_ORDERS'] }
    const queue = { items: [{ order_id: 'd41c1e54-2cf7-4bc4-85ef-d9756558f8ab', order_number: 'ORD-RUN', customer_name: 'Замовник', deadline: '2026-10-20', status: 'PRODUCTION', completed_quantity: 12, planned_quantity: 20, percent: 60, active_operations: 2, blocked_operations: 1, assignees: ['Оператор'], current_item_id: '7ed6fb59-350e-4d2c-8b52-c61cc0c2c457', current_item_identifier: 'UNIT-001', stages: [] }], total: 1, page: 1, page_size: 20 }
    vi.stubGlobal('fetch', vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(manager) : path.includes('/production/queue?') ? response(queue) : response({ status: 'ok' })))
    renderApp('/production')
    expect(await screen.findByRole('heading', { name: 'Виробництво' })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'ORD-RUN' })).toHaveAttribute('href', `/production/orders/${queue.items[0].order_id}/execution`)
    expect(screen.getByRole('link', { name: 'UNIT-001' })).toHaveAttribute('href', `/my-work/items/${queue.items[0].current_item_id}`)
    expect(screen.getByText('12 / 20 · 60%')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Нове замовлення' })).not.toBeInTheDocument()
  })
  it('keeps active operations and labels inside the production flow', async () => {
    const manager = { ...employee, role: 'MANAGER', roles: ['PRODUCTION_MANAGER'], capabilities: ['VIEW_PRODUCTION', 'MANAGE_ORDERS'] }
    const orderId = 'd41c1e54-2cf7-4bc4-85ef-d9756558f8ab'
    const item = { id: '7ed6fb59-350e-4d2c-8b52-c61cc0c2c457', identifier: 'UNIT-001', tracking_mode: 'SERIAL', quantity: 1, variant_id: 'variant-id', variant_name: 'Стандартна', product_name: 'БПЛА', revision_code: 'R1', order_number: 'ORD-RUN', qr_value: 'UNIT-001' }
    const execution = { id: 'execution-id', production_item_id: item.id, stage_id: 'stage-id', stage_code: 'ASSEMBLY', stage_name: 'Складання', planned_quantity: 1, completed_quantity: 0, status: 'READY', assigned_user_id: null, started_at: null, completed_at: null, result_note: '' }
    vi.stubGlobal('fetch', vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(manager) : path.endsWith(`/production/orders/${orderId}/items`) ? response([item]) : path.endsWith(`/production/orders/${orderId}/progress`) ? response({ order_id: orderId, completed: 0, total: 1, percent: 0, stages: [{ stage_code: 'ASSEMBLY', stage_name: 'Складання', completed: 0, total: 1 }] }) : path.endsWith(`/production/orders/${orderId}/work`) ? response([{ item, execution }]) : path.endsWith('/users/options') ? response([]) : response({ status: 'ok' })))
    renderApp(`/production/orders/${orderId}/execution`)
    expect(await screen.findByRole('heading', { name: 'ORD-RUN' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Активні операції' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'UNIT-001' })).toHaveAttribute('href', `/my-work/items/${item.id}`)
    expect(screen.getByRole('button', { name: 'Друкувати мітки' })).toBeInTheDocument()
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
  it('shows all five main sections to an administrator', async () => {
    const administrator = { ...employee, role: 'ADMIN', roles: ['ADMINISTRATOR'], capabilities: ['ADMIN_USERS', 'VIEW_ENGINEERING', 'VIEW_PRODUCTION', 'MANAGE_ORDERS', 'MANAGE_PROCUREMENT'] }
    vi.stubGlobal('fetch', vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(administrator) : response(fixture(path))))
    renderApp()
    const navigation = await screen.findByRole('navigation', { name: 'Основні розділи' })
    for (const label of ['Розробка', 'Продукція', 'Замовлення', 'Виробництво', 'Склад']) {
      expect(navigation).toHaveTextContent(label)
    }
  })
  it('redirects the old order URL to the orders section', async () => {
    const manager = { ...employee, role: 'MANAGER', roles: ['PRODUCTION_MANAGER'], capabilities: ['VIEW_PRODUCTION', 'MANAGE_ORDERS'] }
    const order = { id: 'd41c1e54-2cf7-4bc4-85ef-d9756558f8ab', order_number: 'ORD-LEGACY', customer_id: '91c7b840-d713-4aac-a220-7bfc7909cfd6', customer_name: 'Замовник', recipient: '', destination: '', order_date: '2026-10-04', deadline: null, notes: '', status: 'DRAFT', draft_version: 1, total_quantity: 0, product_summary: '', created_by_id: employee.id, created_at: '2026-10-04T00:00:00Z', updated_at: '2026-10-04T00:00:00Z' }
    vi.stubGlobal('fetch', vi.fn(async (path: string) => path.endsWith('/auth/me') ? response(manager) : path.endsWith(`/orders/${order.id}/items`) ? response([]) : path.endsWith(`/orders/${order.id}`) ? response(order) : path.endsWith('/orders/revision-options') ? response([]) : path.endsWith(`/orders/${order.id}/requirements`) || path.endsWith(`/orders/${order.id}/materials`) ? response([]) : response({ status: 'ok' })))
    renderApp(`/production/orders/${order.id}`)
    expect(await screen.findByRole('heading', { name: 'ORD-LEGACY' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '← До замовлень' })).toHaveAttribute('href', '/orders')
    for (const tab of ['Огляд', 'Вироби', 'Комплектуючі', 'Закупівлі', 'Виробництво', 'Відвантаження']) expect(screen.getByRole('button', { name: tab })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Відвантаження' }))
    expect(screen.getByText('Облік відвантаження ще не реалізований.')).toBeInTheDocument()
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
