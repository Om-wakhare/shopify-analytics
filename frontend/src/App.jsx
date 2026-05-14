import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute   from './components/ui/ProtectedRoute.jsx'
import LoginPage        from './pages/LoginPage.jsx'
import AuthSuccess      from './pages/AuthSuccess.jsx'
import OnboardingPage   from './pages/OnboardingPage.jsx'
import SubscriptionPage from './pages/SubscriptionPage.jsx'
import ProfilePage      from './pages/ProfilePage.jsx'
import SettingsPage     from './pages/SettingsPage.jsx'
import Overview         from './pages/Overview.jsx'
import Revenue          from './pages/Revenue.jsx'
import CLTVPage         from './pages/CLTVPage.jsx'
import CohortPage       from './pages/CohortPage.jsx'
import ChurnPage        from './pages/ChurnPage.jsx'
import ProductsPage     from './pages/ProductsPage.jsx'
import RepeatPage       from './pages/RepeatPage.jsx'

const P = ({ children }) => <ProtectedRoute>{children}</ProtectedRoute>

export default function App() {
  return (
    <Routes>
      {/* ── Public ───────────────────────────── */}
      <Route path="/login"        element={<LoginPage />} />
      <Route path="/auth/success" element={<AuthSuccess />} />

      {/* ── Post-auth setup ───────────────────── */}
      <Route path="/onboarding"  element={<P><OnboardingPage /></P>} />
      <Route path="/subscribe"   element={<P><SubscriptionPage /></P>} />

      {/* ── Account ───────────────────────────── */}
      <Route path="/profile"     element={<P><ProfilePage /></P>} />
      <Route path="/settings"    element={<P><SettingsPage /></P>} />

      {/* ── Dashboard ─────────────────────────── */}
      <Route path="/"            element={<P><Overview /></P>} />
      <Route path="/revenue"     element={<P><Revenue /></P>} />
      <Route path="/cltv"        element={<P><CLTVPage /></P>} />
      <Route path="/cohorts"     element={<P><CohortPage /></P>} />
      <Route path="/churn"       element={<P><ChurnPage /></P>} />
      <Route path="/products"    element={<P><ProductsPage /></P>} />
      <Route path="/repeat"      element={<P><RepeatPage /></P>} />

      <Route path="*"            element={<Navigate to="/" replace />} />
    </Routes>
  )
}
