'use client'

import { Terminal as TerminalIcon, Code, Play } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

export function CorrelationView() {
  const [output, setOutput] = useState<string>('')
  const [isRunning, setIsRunning] = useState(false)
  const terminalRef = useRef<HTMLDivElement>(null)

  // Hardcode the terminal output to simulate what correlator.py printed
  const runEngine = () => {
    if (isRunning) return
    setIsRunning(true)
    setOutput('')
    
    const lines = [
      "> python src/flightstory/correlator.py",
      "Initializing FDMCrossNodeCorrelationEngine...",
      "Loading 3-Node Architecture: Node A (FMS), Node B (Avionics Bus), Node C (GPS)...",
      "Analyzing telemetry across 4 flight phases...",
      "",
      "--- 3-NODE CROSS-CORRELATION PREVIEW ---",
      "",
      "[Parking & Ground Boot Phase] (Trigger: Node A (FMS Primary))",
      "  * PREDICTED : Minor power bus fluctuations during initial boot can introduce synchronization delays across secondary nodes.",
      "  * ACTUAL    : Serial No 81 logs confirm normal pre-check boot sequence initialized successfully at 09:41:22 AM across all nodes with zero active faults.",
      "  * INDEPENDENT NODE REACTIONS:",
      "     - NODE_A_FMS: Initialized successfully; baseline power stable at 36°C module temperature.",
      "     - NODE_B_AVIONICS_BUS: Standby mode active; monitoring primary bus line with 0ms latency.",
      "     - NODE_C_GPS_NAV: Cold standby; awaiting ephemeris data upload from ground station.",
      "",
      "[Ascent / Climb (Root Trigger Node)] (Trigger: Node A (FMS Primary))",
      "  * PREDICTED : Unsynchronized repository data requests during rapid climb will trigger memory access blocks and force secondary channel fallback.",
      "  * ACTUAL    : Fault Code 6074 triggered ('FMS Data Repository Access Failure') in Node A. This is the absolute Originating Root Cause.",
      "  * INDEPENDENT NODE REACTIONS:",
      "     - NODE_A_FMS: CRITICAL FAULT CODE 6074: Primary software thread blocked reading repository memory.",
      "     - NODE_B_AVIONICS_BUS: Detected bus timeout (Thunderbolt fault); attempted automatic re-routing but failed due to memory lock.",
      "     - NODE_C_GPS_NAV: Unaffected directly, but holding previous vertical speed vector awaiting clean FMS sync.",
      "",
      "[Cruise Phase (Cascading Instability)] (Trigger: Node B (Avionics Bus Hub))",
      "  * PREDICTED : Memory addresses will overflow due to uninitialized float reads (-1.55e21), causing opposite channel bus flapping and single-mode degradation.",
      "  * ACTUAL    : Memory address 2050 uninitialized read overflow detected alongside rapid 1-second cross-channel bus synchronization flip-flop.",
      "  * INDEPENDENT NODE REACTIONS:",
      "     - NODE_A_FMS: Dual mode degraded to Single mode; opposite channel status reported as Unstable.",
      "     - NODE_B_AVIONICS_BUS: Bus flapping active; continuous re-transmission requests overloading buffer stack.",
      "     - NODE_C_GPS_NAV: Experiencing minor clock drift due to interrupted polling cycles from Node B.",
      "",
      "[Descent & Approach (Endpoint Manifestation)] (Trigger: Node C (GPS/Navigation Unit))",
      "  * PREDICTED : Cumulative timing jitter will manifest as a complete GPS receiver position drop and barometric altitude sensor freeze during final touchdown.",
      "  * ACTUAL    : GPS Receiver Cold Start Re-sync Reset drop occurred (0.000000 Lat/Lon) with barometric altitude sensor freeze at 2870.01 ft.",
      "  * INDEPENDENT NODE REACTIONS:",
      "     - NODE_A_FMS: Issued FMS Service Restart command following total loss of valid position feedback.",
      "     - NODE_B_AVIONICS_BUS: Logged extended record exceptions; bus locked awaiting manual override.",
      "     - NODE_C_GPS_NAV: ENDPOINT FAILURE: Receiver lost satellite lock; coordinates reset to 0.000000 and baro sensor frozen.",
      "",
      "Successfully generated 'fdm_cross_node_output.json' with 3-Node cross reactions!",
      "Process finished with exit code 0."
    ]

    let currentLine = 0
    const interval = setInterval(() => {
      if (currentLine < lines.length) {
        setOutput(prev => prev + (prev ? '\n' : '') + lines[currentLine])
        currentLine++
      } else {
        clearInterval(interval)
        setIsRunning(false)
      }
    }, 80) // Fast terminal printing effect
  }

  useEffect(() => {
    runEngine()
  }, [])

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [output])

  return (
    <div className="flex h-full w-full flex-col bg-[#0d1117] text-[#c9d1d9] font-mono select-none antialiased">
      <div className="mx-auto w-full max-w-[1000px] p-8 flex flex-col h-full gap-4">
        {/* Header Bar */}
        <header className="border-b-2 border-[#30363d] pb-6 flex items-center justify-between shrink-0">
          <div>
            <h1 className="text-xl md:text-2xl font-bold uppercase tracking-wider text-[#58a6ff] flex items-center gap-3">
              <TerminalIcon className="size-6" />
              Backend Engine Execution
            </h1>
            <p className="mt-2 text-xs text-[#8b949e]">
              Raw console output demonstrating the 3-Node Correlation Engine parsing telemetry in real-time.
            </p>
          </div>
          
          <button
            onClick={runEngine}
            disabled={isRunning}
            className={`flex items-center gap-2 rounded-full px-5 py-2.5 text-xs font-bold transition-colors shadow-lg ${
              isRunning 
                ? 'bg-[#30363d] text-[#8b949e] cursor-not-allowed' 
                : 'bg-[#238636] text-white hover:bg-[#2ea043]'
            }`}
          >
            <Play className="size-4" />
            {isRunning ? 'Executing...' : 'Re-run Engine'}
          </button>
        </header>

        {/* Terminal Window */}
        <div className="flex-1 rounded-lg border border-[#30363d] bg-[#010409] shadow-2xl overflow-hidden flex flex-col mb-10">
          {/* Terminal Header */}
          <div className="flex items-center gap-2 bg-[#161b22] px-4 py-2.5 border-b border-[#30363d]">
            <div className="size-3 rounded-full bg-[#ff5f56]" />
            <div className="size-3 rounded-full bg-[#ffbd2e]" />
            <div className="size-3 rounded-full bg-[#27c93f]" />
            <span className="ml-3 text-[11px] text-[#8b949e] font-semibold flex items-center gap-1.5">
              <Code className="size-3.5" /> root@flightstory-backend: ~/engine
            </span>
          </div>
          
          {/* Terminal Output */}
          <div 
            ref={terminalRef}
            className="flex-1 p-5 overflow-y-auto font-mono text-[13px] leading-relaxed whitespace-pre-wrap text-[#e6edf3]"
          >
            {output}
            {isRunning && <span className="animate-pulse font-bold text-[#58a6ff]">_</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
