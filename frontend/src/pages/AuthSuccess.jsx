import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { Zap } from 'lucide-react'

export default function AuthSuccess() {
  const [params]   = useSearchParams()
  const { login }  = useAuth()
  const navigate   = useNavigate()

  useEffect(() => {
    const token      = params.get('token')
    const subscribed = params.get('subscribed')

    if (token) {
      login(token)
      // Small delay so the user sees the success animation
      setTimeout(() => {
        navigate(subscribed ? '/' : '/onboarding', { replace: true })
      }, 1500)
    } else {
      navigate('/login?error=no_token', { replace: true })
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-brand-600 flex items-center justify-center mx-auto mb-4 animate-pulse">
          <Zap size={28} className="text-white" />
        </div>
        <h2 className="text-xl font-bold text-slate-800">Connected!</h2>
        <p className="text-slate-500 text-sm mt-2">Setting up your dashboard…</p>
        <div className="flex justify-center mt-4 gap-1">
          {[0,1,2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-brand-400 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
