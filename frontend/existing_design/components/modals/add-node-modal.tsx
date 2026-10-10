'use client'

import { useState } from 'react'
import { Plus, Server, X } from 'lucide-react'
import { useFlightStore } from '@/store/flight-store'

export function AddNodeModal() {
  const isOpen = useFlightStore((s) => s.isAddNodeModalOpen)
  const setOpen = useFlightStore((s) => s.setAddNodeModalOpen)

  const [nodeId, setNodeId] = useState('')
  const [nodeName, setNodeName] = useState('')
  const [description, setDescription] = useState('')
  const [filePattern, setFilePattern] = useState('')
  const [success, setSuccess] = useState(false)

  if (!isOpen) return null

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nodeId || !nodeName) return

    setSuccess(true)
    setTimeout(() => {
      setSuccess(false)
      setOpen(false)
      setNodeId('')
      setNodeName('')
      setDescription('')
      setFilePattern('')
    }, 1000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs select-none">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-2xl bg-slate-100 text-slate-800">
              <Server className="size-4" />
            </div>
            <h2 className="text-sm font-bold text-slate-900">Add Avionics Node</h2>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSave} className="mt-4 flex flex-col gap-3.5 text-xs">
          <div>
            <label className="block font-medium text-slate-700 mb-1">
              Node Identifier (ID)
            </label>
            <input
              type="text"
              required
              value={nodeId}
              onChange={(e) => setNodeId(e.target.value)}
              placeholder="e.g. NODE_D or ENGINE_FADEC_1"
              className="h-9 w-full rounded-xl border border-slate-200 bg-white px-3 font-mono text-xs text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">
              Display Name
            </label>
            <input
              type="text"
              required
              value={nodeName}
              onChange={(e) => setNodeName(e.target.value)}
              placeholder="e.g. Node D (Standby FMS)"
              className="h-9 w-full rounded-xl border border-slate-200 bg-white px-3 text-xs text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">
              File Pattern Matcher
            </label>
            <input
              type="text"
              value={filePattern}
              onChange={(e) => setFilePattern(e.target.value)}
              placeholder="e.g. *NODE_D* or *FADEC*"
              className="h-9 w-full rounded-xl border border-slate-200 bg-white px-3 font-mono text-xs text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
            />
          </div>

          <div>
            <label className="block font-medium text-slate-700 mb-1">
              Description (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Engine Control Unit logging bus"
              className="h-9 w-full rounded-xl border border-slate-200 bg-white px-3 text-xs text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
            />
          </div>

          {success && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-2.5 text-center text-xs font-medium text-slate-900">
              Node configuration saved
            </div>
          )}

          <div className="mt-2 flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-full bg-slate-100 px-4 py-2 font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-full bg-slate-900 px-5 py-2 font-semibold text-white hover:bg-slate-800 transition-colors shadow-xs"
            >
              Add Node
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
