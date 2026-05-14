import { useState } from 'react'
import Layout from '../components/layout/Layout.jsx'
import { useStore } from '../context/StoreContext.jsx'
import { useToast } from '../components/ui/Toast.jsx'
import { fmt } from '../utils/formatters.js'
import {
  RefreshCw, Bell, Key, CreditCard, Globe,
  ToggleLeft, ToggleRight, Copy, Check, ExternalLink,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import clsx from 'clsx'

function Section({ title, description, children }) {
  return (
    <div className="card mb-4">
      <div className="mb-5">
        <p className="section-title">{title}</p>
        {description && <p className="section-sub">{description}</p>}
      </div>
      {children}
    </div>
  )
}

function Toggle({ label, description, value, onChange }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
      </div>
      <button
        onClick={() => onChange(!value)}
        className={clsx('transition-colors', value ? 'text-brand-600' : 'text-slate-300')}
      >
        {value ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
      </button>
    </div>
  )
}

export default function SettingsPage() {
  const { store }  = useStore()
  const toast      = useToast()
  const navigate   = useNavigate()

  const [settings, setSettings] = useState({
    autoSync:           true,
    webhooksEnabled:    true,
    syncChurnAlerts:    false,
    syncCompleteAlert:  true,
    darkMode:           false,
    compactTables:      false,
  })
  const [copied, setCopied] = useState(false)

  const toggle = (key) => setSettings(s => ({ ...s, [key]: !s[key] }))

  const handleSave = () => {
    toast('Settings saved', 'success')
  }

  const handleCopyKey = () => {
    navigator.clipboard.writeText('sap_••••••••••••••••')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleManualSync = async () => {
    const backendUrl = import.meta.env.VITE_API_URL || ''
    try {
      const res = await fetch(`${backendUrl}/sync/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shop_domain: store.domain, entity: 'all' }),
      })
      if (res.ok) toast('Sync triggered successfully', 'success')
      else        toast('Sync failed — check Celery worker', 'error')
    } catch {
      toast('Could not connect to backend', 'error')
    }
  }

  return (
    <Layout>
      <div className="max-w-2xl">

        {/* Sync Settings */}
        <Section
          title="Data Sync"
          description="Control how and when your Shopify data is synced"
        >
          <Toggle
            label="Auto Incremental Sync"
            description="Sync new orders and customers every hour automatically"
            value={settings.autoSync}
            onChange={() => toggle('autoSync')}
          />
          <Toggle
            label="Webhook Real-time Updates"
            description="Receive instant updates when orders are created or updated"
            value={settings.webhooksEnabled}
            onChange={() => toggle('webhooksEnabled')}
          />
          <div className="pt-4">
            <button onClick={handleManualSync} className="btn-primary text-sm gap-2">
              <RefreshCw size={14} /> Trigger Full Sync Now
            </button>
            <p className="text-xs text-slate-400 mt-2">
              Re-syncs all historical data from your Shopify store. May take a few minutes.
            </p>
          </div>
        </Section>

        {/* Display Preferences */}
        <Section
          title="Display Preferences"
          description="Customise how data is presented in your dashboard"
        >
          <Toggle
            label="Compact Table View"
            description="Show more rows by reducing row height in tables"
            value={settings.compactTables}
            onChange={() => toggle('compactTables')}
          />
          <div className="flex items-center justify-between py-3 border-b border-slate-50">
            <div>
              <p className="text-sm font-medium text-slate-700">Currency</p>
              <p className="text-xs text-slate-400 mt-0.5">All monetary values are shown in this currency</p>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 rounded-xl text-sm font-medium text-slate-700">
              <Globe size={13} />
              USD
            </div>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-slate-700">Date Format</p>
              <p className="text-xs text-slate-400 mt-0.5">How dates are displayed throughout the dashboard</p>
            </div>
            <span className="text-sm text-slate-600 font-medium">MMM D, YYYY</span>
          </div>
        </Section>

        {/* Notifications */}
        <Section
          title="Notifications"
          description="Choose which events trigger notifications"
        >
          <Toggle
            label="Sync Complete"
            description="Notify when a data sync completes successfully"
            value={settings.syncCompleteAlert}
            onChange={() => toggle('syncCompleteAlert')}
          />
          <Toggle
            label="Churn Alerts"
            description="Notify when high-risk churn customers are detected"
            value={settings.syncChurnAlerts}
            onChange={() => toggle('syncChurnAlerts')}
          />
        </Section>

        {/* API Keys */}
        <Section
          title="API Access"
          description="Use the API to access your analytics data programmatically"
        >
          <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
            <Key size={14} className="text-slate-400 shrink-0" />
            <code className="flex-1 text-xs text-slate-600 font-mono">sap_••••••••••••••••••••••••••••</code>
            <button
              onClick={handleCopyKey}
              className="text-slate-400 hover:text-brand-600 transition-colors"
            >
              {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">API keys are available on Growth and Pro plans.</p>
        </Section>

        {/* Billing */}
        <Section
          title="Billing"
          description="Manage your subscription and billing details"
        >
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm font-medium text-slate-700">Current Plan</p>
              <p className="text-xs text-slate-400 mt-0.5">14-day free trial — upgrade anytime</p>
            </div>
            <button
              onClick={() => navigate('/subscribe')}
              className="btn-primary text-xs gap-1.5"
            >
              <CreditCard size={12} /> Manage Plan
            </button>
          </div>
        </Section>

        {/* Save */}
        <div className="flex justify-end">
          <button onClick={handleSave} className="btn-primary px-6">
            Save Settings
          </button>
        </div>
      </div>
    </Layout>
  )
}
