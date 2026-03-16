import React, { useState } from 'react'
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Box, PlaySquare, LogOut, Sun, Moon, Laptop, Menu, X, History, TrendingUp, Shield, Activity, Server, LayoutGrid, BookOpen } from 'lucide-react'
import { useTheme } from './ThemeProvider'

const Layout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { theme, setTheme } = useTheme()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/login')
  }

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/accounts', label: 'Accounts', icon: <Users size={20} /> },
    { path: '/models', label: 'Models', icon: <Box size={20} /> },
    { path: '/playground', label: 'Playground', icon: <PlaySquare size={20} /> },
    { path: '/logs', label: 'Logs', icon: <History size={20} /> },
    { path: '/analytics', label: 'Analytics', icon: <TrendingUp size={20} /> },
    { path: '/admin', label: 'Admin', icon: <Shield size={20} /> },
    { path: '/health', label: 'Health', icon: <Activity size={20} /> },
    { path: '/mcp', label: 'MCP', icon: <Server size={20} /> },
    { path: '/packages', label: 'Packages', icon: <Box size={20} /> },
    { path: '/features', label: 'Features', icon: <LayoutGrid size={20} /> },
    { path: '/docs', label: 'Docs', icon: <BookOpen size={20} /> },
  ]

  const closeMobileMenu = () => setIsMobileMenuOpen(false)

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden transition-colors duration-200">
      
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-white dark:bg-gray-800 border-b dark:border-gray-700 flex items-center justify-between px-4 z-50">
        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
          Gemini Gateway
        </h1>
        <button 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar Overlay (Mobile) */}
      {isMobileMenuOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={closeMobileMenu}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50
        w-64 bg-white dark:bg-gray-800 border-r dark:border-gray-700 flex flex-col
        transition-transform duration-300 ease-in-out
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-6 border-b dark:border-gray-700 h-16 md:h-auto flex items-center">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 hidden md:block">
            Gemini Gateway
          </h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map(item => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={closeMobileMenu}
                className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive 
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium shadow-sm' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-200'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t dark:border-gray-700 flex flex-col space-y-2">
          {/* Theme Toggle */}
          <div className="flex bg-gray-100 dark:bg-gray-900 p-1 rounded-lg justify-between">
            <button
              onClick={() => setTheme('light')}
              className={`p-2 rounded-md flex-1 flex justify-center transition-colors ${theme === 'light' ? 'bg-white dark:bg-gray-800 shadow-sm text-yellow-500' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}
              title="Light Mode"
            >
              <Sun size={18} />
            </button>
            <button
              onClick={() => setTheme('system')}
              className={`p-2 rounded-md flex-1 flex justify-center transition-colors ${theme === 'system' ? 'bg-white dark:bg-gray-800 shadow-sm text-blue-500' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}
              title="System Theme"
            >
              <Laptop size={18} />
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`p-2 rounded-md flex-1 flex justify-center transition-colors ${theme === 'dark' ? 'bg-white dark:bg-gray-800 shadow-sm text-indigo-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}
              title="Dark Mode"
            >
              <Moon size={18} />
            </button>
          </div>

          <button 
            onClick={handleLogout}
            className="flex items-center space-x-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 px-4 py-3 rounded-lg w-full transition-colors mt-2"
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto md:pt-0 pt-16 w-full relative">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent to-blue-50/30 dark:to-blue-900/10 pointer-events-none" />
        <div className="relative z-10 w-full h-full">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default Layout