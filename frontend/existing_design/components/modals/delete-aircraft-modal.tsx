'use client'

import { useState } from 'react'
import { CheckCircle2, Loader2, Trash2, X } from 'lucide-react'
import { useFlightStore } from '@/store/flight-store'

export function DeleteAircraftModal() {
  const isOpen = useFlightStore((s) => s.isDeleteModalOpen)
  const setOpen = useFlightStore((s) => s.setDeleteModalOpen)
  const targetDeleteFlightId = useFlightStore((s) => s.targetDeleteFlightId)
  const confirmDeleteAircraft = useFlightStore((s) => s.confirmDeleteAircraft)

  const [deleteAircraftData, setDeleteAircraftData] = useState(true)
  const [deleteNodes, setDeleteNodes] = useState(true)
  const [deleteLogs, setDeleteLogs] = useState(true)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteSuccess, setDeleteSuccess] = useState(false)

  if (!isOpen) return null

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      // 1. Call Next.js API route
      await fetch(`/api/delete-flight?flight_id=${encodeURIComponent(targetDeleteFlightId)}`, {
        method: 'POST',
      }).catch(() => null)

      // 2. Call FastAPI backend if active
      await fetch(
        `http://localhost:8000/api/delete-flight?flight_id=${encodeURIComponent(targetDeleteFlightId)}`,
        { method: 'POST' }
      ).catch(() => null)

      setDeleteSuccess(true)
      setTimeout(() => {
        confirmDeleteAircraft(targetDeleteFlightId)
        setIsDeleting(false)
        setDeleteSuccess(false)
        setOpen(false)
      }, 600)
    } catch {
      confirmDeleteAircraft(targetDeleteFlightId)
      setIsDeleting(false)
      setOpen(false)
    }
  }

  const options = [
    {
      id: 'aircraft',
      label: 'Complete Aircraft Data',
      checked: deleteAircraftData,
      toggle: () => setDeleteAircraftData((v) => !v),
    },
    {
      id: 'nodes',
      label: 'Avionics Nodes',
      checked: deleteNodes,
      toggle: () => setDeleteNodes((v) => !v),
    },
    {
      id: 'logs',
      label: 'Data Logs',
      checked: deleteLogs,
      toggle: () => setDeleteLogs((v) => !v),
    },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 select-none">
      <div className="relative w-full max-w-sm rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl transition-all">
        {/* Close Button */}
        <button
          type="button"
          onClick={() => setOpen(false)}
          disabled={isDeleting}
          className="absolute right-5 top-5 rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          aria-label="Close"
        >
          <X className="size-4" />
        </button>

        {/* Android Material-Style Icon & Title */}
        <div className="flex flex-col items-center text-center">
          <div className="flex size-14 items-center justify-center rounded-2xl bg-rose-50 text-rose-600 mb-3">
            <Trash2 className="size-6 stroke-[2.2]" />
          </div>
          <h2 className="text-base font-bold text-slate-900">
            Delete Aircraft
          </h2>
          <span className="mt-0.5 rounded-full bg-slate-100 px-2.5 py-0.5 font-mono text-xs font-semibold text-slate-600">
            {targetDeleteFlightId}
          </span>
        </div>

        {/* Clean Curved Selection Rows */}
        <div className="mt-5 space-y-2">
          {options.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={opt.toggle}
              className={`flex w-full items-center justify-between rounded-2xl px-4 py-3 text-xs font-semibold transition-all ${
                opt.checked
                  ? 'bg-rose-50/60 text-slate-900 border border-rose-200/80'
                  : 'bg-slate-50 text-slate-500 border border-slate-100 hover:bg-slate-100/60'
              }`}
            >
              <span>{opt.label}</span>
              {/* Android-style Switch Toggle */}
              <div
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out ${
                  opt.checked ? 'bg-rose-600' : 'bg-slate-300'
                }`}
              >
                <span
                  className={`inline-block size-3.5 transform rounded-full bg-white shadow-xs transition duration-200 ease-in-out mt-[3px] ml-[3px] ${
                    opt.checked ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </div>
            </button>
          ))}
        </div>

        {/* Action Buttons: Android-Style Rounded-Full Pills */}
        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={() => setOpen(false)}
            disabled={isDeleting}
            className="flex-1 rounded-full bg-slate-100 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting || (!deleteAircraftData && !deleteNodes && !deleteLogs)}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-full bg-rose-600 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-rose-700 transition-colors disabled:opacity-40"
          >
            {isDeleting ? (
              <>
                <Loader2 className="size-3.5 animate-spin" />
                <span>Deleting...</span>
              </>
            ) : deleteSuccess ? (
              <>
                <CheckCircle2 className="size-3.5" />
                <span>Deleted</span>
              </>
            ) : (
              <span>Delete</span>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
