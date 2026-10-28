import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from './components/AppLayout'
import { AdminRoute, ProtectedRoute, RequireGuest } from './components/RouteGuards'
import { Loading } from './components/Spinner'
import CertificatesPage from './pages/CertificatesPage'
import CourseCheckoutPage from './pages/CourseCheckoutPage'
import CourseDetailPage from './pages/CourseDetailPage'
import CoursesPage from './pages/CoursesPage'
import DashboardPage from './pages/DashboardPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import QuizPage from './pages/QuizPage'
import RewardsPolicyPage from './pages/RewardsPolicyPage'
import SignUpPage from './pages/SignUpPage'
import AdminCoursesPage from './pages/admin/AdminCoursesPage'
import AdminLayout from './pages/admin/AdminLayout'
import AdminOverviewPage from './pages/admin/AdminOverviewPage'
import AdminSettingsPage from './pages/admin/AdminSettingsPage'
import AdminTasksPage from './pages/admin/AdminTasksPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import BillingSettings from './pages/settings/BillingSettings'
import PreferencesSettings from './pages/settings/PreferencesSettings'
import ProfileSettings from './pages/settings/ProfileSettings'
import SecuritySettings from './pages/settings/SecuritySettings'
import SettingsLayout from './pages/settings/SettingsLayout'
import SubscriptionPage from './pages/SubscriptionPage'
import TaskPage from './pages/TaskPage'
import TopicDetailPage from './pages/TopicDetailPage'
import TransactionsPage from './pages/TransactionsPage'
import WalletPage from './pages/WalletPage'
import { useAuth } from './hooks/useAuth'

/** Signed-in-only pages are wrapped in one place, never guarded in the page. */
function guarded(element) {
  return <ProtectedRoute>{element}</ProtectedRoute>
}

/**
 * `/` is the public landing page. Someone already signed in has no use for it,
 * so admins land in the console and learners in their dashboard.
 */
function HomeRoute() {
  const { user, status } = useAuth()

  if (status === 'loading') return <Loading label="Checking your session…" />

  return user ? <Navigate to={user.is_admin ? '/admin' : '/dashboard'} replace /> : <LandingPage />
}

export default function App() {
  return (
    <Routes>
      {/* The admin console has its own shell, outside the learner navigation. */}
      <Route
        path="admin"
        element={
          <AdminRoute>
            <AdminLayout />
          </AdminRoute>
        }
      >
        <Route index element={<AdminOverviewPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="courses" element={<AdminCoursesPage />} />
        <Route path="tasks" element={<AdminTasksPage />} />
        <Route path="settings" element={<AdminSettingsPage />} />
      </Route>

      <Route element={<AppLayout />}>
        <Route index element={<HomeRoute />} />
        <Route path="dashboard" element={guarded(<DashboardPage />)} />

        {/* Catalogue: readable by anyone, so people can see what they would buy. */}
        <Route path="courses" element={<CoursesPage />} />
        <Route path="courses/:courseId" element={<CourseDetailPage />} />
        <Route path="topics/:topicId" element={<TopicDetailPage />} />
        <Route path="rewards-policy" element={<RewardsPolicyPage />} />

        {/* Tasks, money and account pages need a signed-in user. */}
        <Route path="checkout/:courseId" element={guarded(<CourseCheckoutPage />)} />
        <Route path="tasks/:taskId" element={guarded(<TaskPage />)} />
        <Route path="tasks/:taskId/quiz" element={guarded(<QuizPage />)} />
        <Route path="subscription" element={guarded(<SubscriptionPage />)} />
        <Route path="wallet" element={guarded(<WalletPage />)} />
        <Route path="transactions" element={guarded(<TransactionsPage />)} />
        <Route path="certificates" element={guarded(<CertificatesPage />)} />

        {/* Account settings, one section per URL so links can be shared. */}
        <Route path="settings" element={guarded(<SettingsLayout />)}>
          <Route index element={<Navigate to="profile" replace />} />
          <Route path="profile" element={<ProfileSettings />} />
          <Route path="security" element={<SecuritySettings />} />
          <Route path="preferences" element={<PreferencesSettings />} />
          <Route path="billing" element={<BillingSettings />} />
        </Route>
        <Route path="profile" element={<Navigate to="/settings/profile" replace />} />

        <Route
          path="login"
          element={
            <RequireGuest>
              <LoginPage />
            </RequireGuest>
          }
        />
        <Route
          path="signup"
          element={
            <RequireGuest>
              <SignUpPage />
            </RequireGuest>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
