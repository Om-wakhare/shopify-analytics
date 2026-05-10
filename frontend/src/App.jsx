import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute  from './components/ui/ProtectedRoute.jsx'
import LoginPage       from './pages/LoginPage.jsx'
import AuthSuccess     from './pages/AuthSuccess.jsx'
import OnboardingPage  from './pages/OnboardingPage.jsx'
import SubscriptionPage from './pages/SubscriptionPage.jsx'
import Overview        from './pages/Overview.jsx'
import Revenue         from './pages/Revenue.jsx'
import CLTVPage        from './pages/CLTVPage.jsx'
import CohortPage      from './pages/CohortPage.jsx'
import ChurnPage       from './pages/ChurnPage.jsx'
import ProductsPage    from './pages/ProductsPage.jsx'
import RepeatPage      from './pages/RepeatPage.jsx'

export default function App() {
  return (
    <Routes>
      {/* ── Public ───────────────────────────────────── */}
      <Route path="/login"        element={<LoginPage />} />
      <Route path="/auth/success" element={<AuthSuccess />} />

      {/* ── Post-auth setup ───────────────────────────── */}
      <Route path="/onboarding" element={
        <ProtectedRoute><OnboardingPage /></ProtectedRoute>
      } />
      <Route path="/subscribe" element={
        <ProtectedRoute><SubscriptionPage /></ProtectedRoute>
      } />

      {/* ── Protected dashboard ───────────────────────── */}
      <Route path="/" element={
        <ProtectedRoute><Overview /></ProtectedRoute>
      } />
      <Route path="/revenue" element={
        <ProtectedRoute><Revenue /></ProtectedRoute>
      } />
      <Route path="/cltv" element={
        <ProtectedRoute><CLTVPage /></ProtectedRoute>
      } />
      <Route path="/cohorts" element={
        <ProtectedRoute><CohortPage /></ProtectedRoute>
      } />
      <Route path="/churn" element={
        <ProtectedRoute><ChurnPage /></ProtectedRoute>
      } />
      <Route path="/products" element={
        <ProtectedRoute><ProductsPage /></ProtectedRoute>
      } />
      <Route path="/repeat" element={
        <ProtectedRoute><RepeatPage /></ProtectedRoute>
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
