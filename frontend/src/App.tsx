import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import axios from 'axios'
import Login from './pages/Login'
import ForgotPassword from './pages/ForgotPassword'
import Dashboard from './pages/Dashboard'
import Playground from './pages/Playground'
import Accounts from './pages/Accounts'
import Models from './pages/Models'
import Logs from './pages/Logs'
import Analytics from './pages/Analytics'
import Admin from './pages/Admin'
import Health from './pages/Health'
import McpSettings from './pages/McpSettings'
import OpenClaw from './pages/OpenClaw'
import Packages from './pages/Packages'
import Features from './pages/Features'
import Docs from './pages/Docs'
import Layout from './components/Layout'
import { ThemeProvider } from './components/ThemeProvider'

// Only redirect to login when the server actively rejects with 401.
// A missing token just means the user hasn't logged in yet — handled by PrivateRoute.
function AxiosInterceptor() {
  const navigate = useNavigate()
  useEffect(() => {
    const id = axios.interceptors.response.use(
      (res) => res,
      (error) => {
        const url: string = error.config?.url ?? ''
        // Only log out for admin JWT routes, not API/native/mcp routes that use separate auth
        if (error.response?.status === 401 && !url.includes('/v1/') && !url.includes('/native/') && !url.includes('/mcp/')) {
          localStorage.removeItem('token')
          navigate('/login', { replace: true })
        }
        return Promise.reject(error)
      }
    )
    return () => axios.interceptors.response.eject(id)
  }, [navigate])
  return null
}

const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <Router>
        <AxiosInterceptor />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="accounts" element={<Accounts />} />
            <Route path="models" element={<Models />} />
            <Route path="playground" element={<Playground />} />
            <Route path="logs" element={<Logs />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="admin" element={<Admin />} />
            <Route path="health" element={<Health />} />
            <Route path="mcp" element={<McpSettings />} />
            <Route path="openclaw" element={<OpenClaw />} />
            <Route path="packages" element={<Packages />} />
            <Route path="features" element={<Features />} />
            <Route path="docs" element={<Docs />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
