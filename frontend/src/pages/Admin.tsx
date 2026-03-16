import React, { useState, useEffect } from 'react'
import { Users, UserPlus, Shield, UserX, Check, X, Mail, ShieldCheck, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import axios from 'axios'

interface User {
  id: number
  email: string
  role: string
  status: string
  created_at: string
}

const Admin = () => {
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [newUser, setNewUser] = useState({ email: '', password: '', role: 'viewer', status: 'active' })

  const API_BASE = `http://${window.location.hostname}:6400`
  const token = localStorage.getItem('token')

  const fetchUsers = async () => {
    setIsLoading(true)
    try {
      const res = await axios.get(`${API_BASE}/admin/users/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setUsers(res.data)
    } catch (err) {
      toast.error('Failed to fetch users')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await axios.post(`${API_BASE}/admin/users/`, newUser, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('User created successfully')
      setIsAdding(false)
      setNewUser({ email: '', password: '', role: 'viewer', status: 'active' })
      fetchUsers()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create user')
    }
  }

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return
    try {
      await axios.delete(`${API_BASE}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      toast.success('User deleted')
      fetchUsers()
    } catch (err) {
      toast.error('Failed to delete user')
    }
  }

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
      case 'operator': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      case 'developer': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <Shield className="mr-3 text-blue-600" />
            Admin Control
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1.5">
            Manage users, roles, and system security
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button 
            onClick={fetchUsers}
            className="p-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-750 transition shadow-sm"
          >
            <RefreshCw size={20} className="text-gray-500" />
          </button>
          
          <button 
            onClick={() => setIsAdding(!isAdding)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl flex items-center space-x-2 transition font-medium text-sm shadow-sm"
          >
            {isAdding ? <X size={18} /> : <UserPlus size={18} />}
            <span>{isAdding ? 'Cancel' : 'Add User'}</span>
          </button>
        </div>
      </div>

      {isAdding && (
        <div className="bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm animate-in fade-in slide-in-from-top-4">
          <h2 className="text-xl font-bold mb-6 flex items-center">
            <UserPlus className="mr-2 text-blue-500" size={20} />
            Create New User
          </h2>
          <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 ml-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input 
                  type="email" 
                  required
                  placeholder="user@example.com"
                  className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-gray-900 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition"
                  value={newUser.email}
                  onChange={e => setNewUser({...newUser, email: e.target.value})}
                />
              </div>
            </div>
            
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 ml-1">Initial Password</label>
              <input 
                type="password" 
                required
                placeholder="••••••••"
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition"
                value={newUser.password}
                onChange={e => setNewUser({...newUser, password: e.target.value})}
              />
            </div>
            
            <div className="space-y-1.5">
              <label className="text-sm font-semibold text-gray-700 dark:text-gray-300 ml-1">Role</label>
              <select 
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition"
                value={newUser.role}
                onChange={e => setNewUser({...newUser, role: e.target.value})}
              >
                <option value="admin">Admin (Full Access)</option>
                <option value="operator">Operator (Manage Accounts)</option>
                <option value="developer">Developer (Playground/API)</option>
                <option value="viewer">Viewer (Read Only)</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button 
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition shadow-lg shadow-blue-500/20"
              >
                Create User Account
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-100 dark:border-gray-700">
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Joined</th>
                <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-700/50">
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={5} className="px-6 py-4 h-16 bg-gray-50/20"></td>
                  </tr>
                ))
              ) : (
                users.map(user => (
                  <tr key={user.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-750 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold mr-3 shadow-sm">
                          {user.email[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900 dark:text-white">{user.email}</div>
                          <div className="text-xs text-gray-500">ID: {user.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-bold flex items-center w-fit ${getRoleBadge(user.role)}`}>
                        <ShieldCheck size={12} className="mr-1" />
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className={`h-2 w-2 rounded-full mr-2 ${user.status === 'active' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className="text-sm font-medium">{user.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleDeleteUser(user.id)}
                        className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition"
                        title="Delete User"
                      >
                        <UserX size={20} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Admin
