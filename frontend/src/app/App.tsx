import { Navigate, Route, Routes, useParams } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Layout } from '../components/Layout'
import { Loading } from '../components/Feedback'
import { DashboardPage } from '../pages/DashboardPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { AuthGuard, AdminGuard, CapabilityGuard } from '../features/auth/AuthGuard'
import { LoginPage } from '../features/auth/LoginPage'
import { UsersPage } from '../features/users/UsersPage'
import { SettingsPage } from '../features/users/SettingsPage'
import { ProjectsPage } from '../features/projects/ProjectsPage'
import { ProjectFormPage } from '../features/projects/ProjectForm'
import { ProjectDetail } from '../features/projects/ProjectDetail'
import { TasksPage } from '../features/tasks/TasksPage'
import { TaskFormPage } from '../features/tasks/TaskForm'
import { TaskDetail } from '../features/tasks/TaskDetail'
import { ComponentsPage } from '../features/engineering/ComponentsPage'
import { ComponentFormPage } from '../features/engineering/ComponentForm'
import { ComponentDetail } from '../features/engineering/ComponentDetail'
import { SetupsPage } from '../features/engineering/SetupsPage'
import { SetupFormPage } from '../features/engineering/SetupForm'
import { SetupDetail } from '../features/engineering/SetupDetail'
import { ModulePage } from '../pages/ModulePage'
import { MyWorkPage } from '../pages/MyWorkPage'
import { RndPage } from '../pages/RndPage'
import { BranchDetail } from '../features/rnd/BranchDetail'
import { ProductsPage } from '../features/products/ProductsPage'
import { ProductDetail } from '../features/products/ProductDetail'
import { ProductionPage } from '../features/production/ProductionPage'
import { OrdersPage } from '../features/production/OrdersPage'
import { OrderDetail } from '../features/production/OrderDetail'
import { WorkerItemPage } from '../features/production/WorkerItemPage'

const TestsPage = lazy(() => import('../features/tests/TestsPage').then(module => ({ default: module.TestsPage })))
const TestFormPage = lazy(() => import('../features/tests/TestForm').then(module => ({ default: module.TestFormPage })))
const TestDetail = lazy(() => import('../features/tests/TestDetail').then(module => ({ default: module.TestDetail })))
const SearchPage = lazy(() => import('../features/search/SearchPage').then(module => ({ default: module.SearchPage })))

export function App() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route element={<AuthGuard />}>
      <Route element={<Layout />}>
        <Route element={<AdminGuard />}>
          <Route path="users" element={<UsersPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route index element={<DashboardPage />} />
        <Route path="rnd" element={<RndPage />} />
        <Route path="rnd/branches/:id" element={<BranchDetail />} />
        <Route element={<CapabilityGuard anyOf={['VIEW_ENGINEERING']} />}>
          <Route path="products" element={<ProductsPage />} />
          <Route path="products/:id" element={<ProductDetail />} />
        </Route>
        <Route element={<CapabilityGuard anyOf={['MANAGE_ORDERS', 'MANAGE_PROCUREMENT']} />}>
          <Route path="orders" element={<OrdersPage />} />
          <Route path="orders/:id" element={<OrderDetail />} />
          <Route path="inventory" element={<ModulePage title="Склад" description="Фізичні залишки, рухи та резервування компонентів." phase={7} />} />
        </Route>
        <Route element={<CapabilityGuard anyOf={['VIEW_PRODUCTION']} />}>
          <Route path="production" element={<ProductionPage />} />
          <Route path="my-work" element={<MyWorkPage />} />
          <Route path="my-work/items/:id" element={<WorkerItemPage />} />
        </Route>
        <Route path="production/orders/:id" element={<LegacyOrderRedirect />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<ProjectFormPage />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="projects/:id/edit" element={<ProjectFormPage />} />
        <Route path="tasks" element={<TasksPage />} />
        <Route path="tasks/new" element={<TaskFormPage />} />
        <Route path="tasks/:id" element={<TaskDetail />} />
        <Route path="tasks/:id/edit" element={<TaskFormPage />} />
        <Route path="setups" element={<SetupsPage />} />
        <Route path="setups/new" element={<SetupFormPage />} />
        <Route path="setups/:id" element={<SetupDetail />} />
        <Route path="setups/:id/edit" element={<SetupFormPage />} />
        <Route path="components" element={<ComponentsPage />} />
        <Route path="components/new" element={<ComponentFormPage />} />
        <Route path="components/:id" element={<ComponentDetail />} />
        <Route path="components/:id/edit" element={<ComponentFormPage />} />
        <Route path="tests" element={<Suspense fallback={<Loading />}><TestsPage /></Suspense>} />
        <Route path="tests/new" element={<Suspense fallback={<Loading />}><TestFormPage /></Suspense>} />
        <Route path="tests/:id" element={<Suspense fallback={<Loading />}><TestDetail /></Suspense>} />
        <Route path="tests/:id/edit" element={<Suspense fallback={<Loading />}><TestFormPage /></Suspense>} />
        <Route path="search" element={<Suspense fallback={<Loading />}><SearchPage /></Suspense>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      </Route>
    </Routes>
  )
}

function LegacyOrderRedirect() {
  const { id = '' } = useParams()
  return <Navigate replace to={`/orders/${id}`} />
}
