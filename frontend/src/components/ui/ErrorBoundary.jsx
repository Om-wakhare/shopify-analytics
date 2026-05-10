import { Component } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

export class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center mb-3">
            <AlertTriangle size={22} className="text-red-500" />
          </div>
          <p className="text-sm font-semibold text-slate-700">Something went wrong</p>
          <p className="text-xs text-slate-400 mt-1 max-w-xs">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ error: null })}
            className="mt-4 btn-ghost text-xs gap-1.5"
          >
            <RefreshCw size={12} /> Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export function withErrorBoundary(Component) {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}
