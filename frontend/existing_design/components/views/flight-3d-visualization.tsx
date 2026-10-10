'use client'

import { useEffect, useRef, useState } from 'react'
import Image from 'next/image'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Camera,
  Play,
  Pause,
  RotateCcw,
} from 'lucide-react'
import { useFlightStore } from '@/store/flight-store'
import type { AircraftTreeNode } from '@/lib/flight-tree'

interface Flight3DVisualizationProps {
  tree: AircraftTreeNode
}

interface StoryAct {
  id: number
  actNumber: string
  phase: string
  title: string
  flightData: {
    altitude: string
    speed: string
    attitude: string
  }
  realImage: string
  alt: string
  story: string
  modelPose: {
    rotX: number
    rotZ: number
    posY: number
    camPos: [number, number, number]
  }
  nodes: {
    a: { name: string; tag: string; status: string; isTrouble: boolean }
    b: { name: string; tag: string; status: string; isTrouble: boolean }
    c: { name: string; tag: string; status: string; isTrouble: boolean }
  }
}

const STORY_ACTS: StoryAct[] = [
  {
    id: 0,
    actNumber: '01',
    phase: 'PRE-FLIGHT & TAXI',
    title: 'The Calm Before the Storm',
    flightData: {
      altitude: '0 ft',
      speed: '0 kts',
      attitude: 'Level / On Ground',
    },
    realImage: '/images/flight_cutaway.jpg',
    alt: 'Aircraft Preflight Systems Overview',
    story:
      'At Madurai Airport (IXM), engines spool up. Both FMS computers boot normally with power stable at 36°C. The AFDX data bus and GPS navigation systems are in standby, ready for departure. All baseline parameters are nominal.',
    modelPose: {
      rotX: 0,
      rotZ: 0,
      posY: -2,
      camPos: [-18, 7, 24],
    },
    nodes: {
      a: { name: 'Node A (FMS)', tag: 'BOOT NORMAL (36°C)', status: 'Boot Normal · 36°C', isTrouble: false },
      b: { name: 'Node B (Bus)', tag: 'STANDBY (AFDX)', status: 'Standby · AFDX Bus Ready', isTrouble: false },
      c: { name: 'Node C (GPS)', tag: 'STANDBY (12 SATS)', status: 'Standby · 12 Sats Locked', isTrouble: false },
    },
  },
  {
    id: 1,
    actNumber: '02',
    phase: 'ROTATION & CLIMB',
    title: 'The Trap Springs — Fault 6074',
    flightData: {
      altitude: '4,850 ft',
      speed: '250 kts',
      attitude: 'Pitch +14° Climb',
    },
    realImage: '/images/real_flight_ascent.jpg',
    alt: 'Aircraft Takeoff and Climb into the Sky',
    story:
      'Passing V1 rotation, the aircraft pitches up into climb. The FMS transitions to airborne mode and strikes a software trap: Honeywell Fault 6074 locks the CPU thread at address 0x18000CE0. Node B detects cross-talk loss and drops to Single Mode.',
    modelPose: {
      rotX: -0.24,
      rotZ: 0.08,
      posY: 3,
      camPos: [-22, 9, 21],
    },
    nodes: {
      a: { name: 'Node A (FMS)', tag: 'TRAP 0x18000CE0', status: 'CPU Trap @ 0x18000CE0', isTrouble: true },
      b: { name: 'Node B (Bus)', tag: 'BUS TIMEOUT (SINGLE)', status: 'Timeout · Dropped to Single Mode', isTrouble: true },
      c: { name: 'Node C (GPS)', tag: 'HOLDING VECTOR', status: 'Holding Inertial Vector', isTrouble: false },
    },
  },
  {
    id: 2,
    actNumber: '03',
    phase: 'EN-ROUTE CRUISE',
    title: 'The Pilot Responds at FL350',
    flightData: {
      altitude: '35,000 ft',
      speed: '462 kts',
      attitude: 'Level Cruise · Mach 0.78',
    },
    realImage: '/images/real_flight_cruise.jpg',
    alt: 'Commercial Jet Level Cruise at High Altitude',
    story:
      'Level at FL350, the master caution illuminates: "FMS DEGRADED". The flight crew manually enters FL350 into the MCDU. Meanwhile, continuous message retries flood the avionics bus buffer, creating communication lag across the airframe.',
    modelPose: {
      rotX: -0.02,
      rotZ: 0,
      posY: 5,
      camPos: [-24, 10, 18],
    },
    nodes: {
      a: { name: 'Node A (FMS)', tag: 'DEGRADED (THREAD STALL)', status: 'Degraded · Thread Stalled', isTrouble: true },
      b: { name: 'Node B (Bus)', tag: 'BUS FLAPPING (QUEUE 99%)', status: 'Bus Flapping · Buffer 99% Full', isTrouble: true },
      c: { name: 'Node C (GPS)', tag: '42ms TIMING JITTER', status: '42ms Timing Jitter', isTrouble: true },
    },
  },
  {
    id: 3,
    actNumber: '04',
    phase: 'DESCENT & APPROACH',
    title: 'The Cascade — Total GPS Drop',
    flightData: {
      altitude: '2,870 ft (Frozen)',
      speed: '215 kts',
      attitude: 'Pitch -6° Descent',
    },
    realImage: '/images/real_flight_descent.jpg',
    alt: 'Commercial Jet Descending into Dusk Clouds',
    story:
      'During descent into Mumbai (BOM), the bus congestion starves the GPS receiver. Node C drops offline: coordinates reset to 0.000000 and altitude freezes at 2,870 ft. The captain initiates a manual FMS service restart to safely conduct the visual approach.',
    modelPose: {
      rotX: 0.14,
      rotZ: -0.08,
      posY: 1,
      camPos: [-18, 12, -22],
    },
    nodes: {
      a: { name: 'Node A (FMS)', tag: 'MANUAL RESTART', status: 'Manual Restart Triggered', isTrouble: true },
      b: { name: 'Node B (Bus)', tag: 'BUS LOCKED (OVERFLOW)', status: 'Queue Overflow · Bus Locked', isTrouble: true },
      c: { name: 'Node C (GPS)', tag: 'SIGNAL LOSS (0.000000)', status: 'Signal Loss · 0.000000 Lat/Lon', isTrouble: true },
    },
  },
  {
    id: 4,
    actNumber: '05',
    phase: 'POST-FLIGHT FORENSICS',
    title: 'Resolution: The Memory Trap',
    flightData: {
      altitude: 'Touchdown',
      speed: '0 kts',
      attitude: 'Safely on Ground',
    },
    realImage: '/images/flight_cutaway.jpg',
    alt: 'Internal Avionics Architecture Cutaway',
    story:
      'Forensic analysis confirms all avionics hardware is 100% healthy. The cascading GPS loss during descent was caused by bus congestion during cruise, which originated from a single software memory leak in Node A at takeoff.',
    modelPose: {
      rotX: 0,
      rotZ: 0,
      posY: 0,
      camPos: [20, 11, 20],
    },
    nodes: {
      a: { name: 'Node A (FMS)', tag: 'ROOT CAUSE: MEMORY LEAK', status: 'Root Cause: Software Memory Leak', isTrouble: true },
      b: { name: 'Node B (Bus)', tag: 'HEALTHY HARDWARE', status: 'Healthy Hardware · Flooded by Retries', isTrouble: false },
      c: { name: 'Node C (GPS)', tag: 'HEALTHY HARDWARE', status: 'Healthy Hardware · Starvation Casualty', isTrouble: false },
    },
  },
]

export function Flight3DVisualization({ tree }: Flight3DVisualizationProps) {
  const activeStoryAct = useFlightStore((s) => s.activeStoryAct)
  const setActiveStoryAct = useFlightStore((s) => s.setActiveStoryAct)

  const [displayMode, setDisplayMode] = useState<'simulated' | 'photo'>('simulated')
  const [isPlaying, setIsPlaying] = useState(false)

  // Canvas and DOM pointer references
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLDivElement>(null)

  // Direct DOM pointers for zero React re-render churn
  const dotARef = useRef<SVGCircleElement>(null)
  const dotBRef = useRef<SVGCircleElement>(null)
  const dotCRef = useRef<SVGCircleElement>(null)
  const lineARef = useRef<SVGLineElement>(null)
  const lineBRef = useRef<SVGLineElement>(null)
  const lineCRef = useRef<SVGLineElement>(null)
  const tagARef = useRef<HTMLDivElement>(null)
  const tagBRef = useRef<HTMLDivElement>(null)
  const tagCRef = useRef<HTMLDivElement>(null)

  // Three.js animation controller references
  const threeRef = useRef<{
    scene: THREE.Scene
    camera: THREE.PerspectiveCamera
    renderer: THREE.WebGLRenderer
    controls: OrbitControls
    planeGroup: THREE.Group
    anchorA: THREE.Object3D
    anchorB: THREE.Object3D
    anchorC: THREE.Object3D
    targetRotX: number
    targetRotZ: number
    targetPosY: number
    targetCamPos: THREE.Vector3
    animId: number | null
  } | null>(null)

  const currentAct = STORY_ACTS[activeStoryAct] || STORY_ACTS[0]

  // Auto-play timer for smooth story progression
  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setActiveStoryAct((activeStoryAct + 1) % STORY_ACTS.length)
    }, 7000)
    return () => clearInterval(timer)
  }, [isPlaying, activeStoryAct, setActiveStoryAct])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        setActiveStoryAct((activeStoryAct + 1) % STORY_ACTS.length)
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        setActiveStoryAct(
          (activeStoryAct - 1 + STORY_ACTS.length) % STORY_ACTS.length
        )
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeStoryAct, setActiveStoryAct])

  // Smoothly update 3D target attitude and camera when story act changes
  useEffect(() => {
    const act = STORY_ACTS[activeStoryAct]
    if (act && threeRef.current) {
      threeRef.current.targetRotX = act.modelPose.rotX
      threeRef.current.targetRotZ = act.modelPose.rotZ
      threeRef.current.targetPosY = act.modelPose.posY
      threeRef.current.targetCamPos.set(...act.modelPose.camPos)
    }
  }, [activeStoryAct])

  // =========================================================================
  // SIMULATED 3D FLIGHT INITIALIZATION (CLEAN THREE.JS ENGINE)
  // =========================================================================
  useEffect(() => {
    if (displayMode !== 'simulated') return

    const canvasContainer = canvasRef.current
    if (!canvasContainer) return

    const width = canvasContainer.clientWidth || window.innerWidth
    const height = canvasContainer.clientHeight || window.innerHeight

    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x070a12, 0.01)

    const camera = new THREE.PerspectiveCamera(46, width / height, 0.1, 1000)
    const initPose = currentAct.modelPose
    camera.position.set(...initPose.camPos)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.15
    renderer.setClearColor(0x070a12, 1)

    canvasContainer.innerHTML = ''
    canvasContainer.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.06
    controls.maxDistance = 100
    controls.minDistance = 6
    controls.autoRotate = false

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95)
    scene.add(ambientLight)

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.8)
    sunLight.position.set(30, 45, 25)
    scene.add(sunLight)

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.5)
    fillLight.position.set(-20, -15, -20)
    scene.add(fillLight)

    // Engineering Flight Grid Floor
    const grid = new THREE.GridHelper(240, 50, 0x334155, 0x0f172a)
    grid.position.y = -8
    scene.add(grid)

    // Subtle Starfield
    const starGeo = new THREE.BufferGeometry()
    const starCount = 500
    const starPos = new Float32Array(starCount * 3)
    for (let i = 0; i < starCount * 3; i++) {
      starPos[i] = (Math.random() - 0.5) * 400
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3))
    const starMat = new THREE.PointsMaterial({ color: 0x475569, size: 1.1 })
    scene.add(new THREE.Points(starGeo, starMat))

    // Aircraft Model Master Group
    const planeGroup = new THREE.Group()

    const fuselageMat = new THREE.MeshStandardMaterial({
      color: 0xf8fafc,
      roughness: 0.25,
      metalness: 0.15,
    })
    const navyMat = new THREE.MeshStandardMaterial({
      color: 0x0f2b5c,
      roughness: 0.3,
      metalness: 0.25,
    })
    const wingMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      roughness: 0.35,
      metalness: 0.2,
    })
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0x020617,
      roughness: 0.05,
      metalness: 0.95,
    })
    const engineDarkMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.4,
      metalness: 0.4,
    })
    const chromeLipMat = new THREE.MeshStandardMaterial({
      color: 0x94a3b8,
      roughness: 0.15,
      metalness: 0.85,
    })

    // Fuselage Body
    const fuselage = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 22, 32), fuselageMat)
    fuselage.rotateX(Math.PI / 2)
    planeGroup.add(fuselage)

    // Aerodynamic Nose Cone
    const nose = new THREE.Mesh(new THREE.ConeGeometry(1.4, 4.2, 32), fuselageMat)
    nose.rotateX(-Math.PI / 2)
    nose.position.set(0, 0, 13.1)
    planeGroup.add(nose)

    // Cockpit Windshield Glass
    const cockpit = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.42, 1.2), glassMat)
    cockpit.position.set(0, 0.95, 12.2)
    cockpit.rotation.x = 0.35
    planeGroup.add(cockpit)

    // Tail Cone
    const tailCone = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 1.4, 6.5, 32), navyMat)
    tailCone.rotateX(Math.PI / 2)
    tailCone.position.set(0, 0.3, -14.2)
    planeGroup.add(tailCone)

    // Main Wings (Swept Dihedral)
    const wingGeo = new THREE.BoxGeometry(11, 0.25, 3.8)
    const wingL = new THREE.Mesh(wingGeo, wingMat)
    wingL.position.set(-6.5, -0.1, 0.5)
    wingL.rotation.set(-0.04, -0.22, -0.05)
    planeGroup.add(wingL)

    const wingR = new THREE.Mesh(wingGeo, wingMat)
    wingR.position.set(6.5, -0.1, 0.5)
    wingR.rotation.set(-0.04, 0.22, 0.05)
    planeGroup.add(wingR)

    // Wingtips (Sharklets)
    const wingletL = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.6, 1.2), navyMat)
    wingletL.position.set(-11.8, 0.8, -0.8)
    wingletL.rotation.set(-0.04, -0.22, -0.2)
    planeGroup.add(wingletL)

    const wingletR = new THREE.Mesh(new THREE.BoxGeometry(0.2, 1.6, 1.2), navyMat)
    wingletR.position.set(11.8, 0.8, -0.8)
    wingletR.rotation.set(-0.04, 0.22, 0.2)
    planeGroup.add(wingletR)

    // Turbofan Jet Engines
    const engineCowlGeo = new THREE.CylinderGeometry(0.85, 0.9, 4.2, 28)
    const engineCowlL = new THREE.Mesh(engineCowlGeo, fuselageMat)
    engineCowlL.rotateX(Math.PI / 2)
    engineCowlL.position.set(-4.8, -1.2, 1.2)
    planeGroup.add(engineCowlL)

    const engineLipL = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.08, 12, 28), chromeLipMat)
    engineLipL.position.set(-4.8, -1.2, 3.3)
    planeGroup.add(engineLipL)

    const engineCowlR = new THREE.Mesh(engineCowlGeo, fuselageMat)
    engineCowlR.rotateX(Math.PI / 2)
    engineCowlR.position.set(4.8, -1.2, 1.2)
    planeGroup.add(engineCowlR)

    const engineLipR = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.08, 12, 28), chromeLipMat)
    engineLipR.position.set(4.8, -1.2, 3.3)
    planeGroup.add(engineLipR)

    // Vertical Tail Fin
    const verticalTail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 5.2, 3.6), navyMat)
    verticalTail.position.set(0, 3.4, -13.5)
    verticalTail.rotation.x = -0.32
    planeGroup.add(verticalTail)

    // Horizontal Stabilizers
    const hStabL = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.18, 1.8), wingMat)
    hStabL.position.set(-2.8, 1.1, -14.8)
    hStabL.rotation.set(-0.02, -0.2, -0.05)
    planeGroup.add(hStabL)

    const hStabR = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.18, 1.8), wingMat)
    hStabR.position.set(2.8, 1.1, -14.8)
    hStabR.rotation.set(-0.02, 0.2, 0.05)
    planeGroup.add(hStabR)

    // Initial pose
    planeGroup.rotation.x = initPose.rotX
    planeGroup.rotation.z = initPose.rotZ
    planeGroup.position.y = initPose.posY
    scene.add(planeGroup)

    // =========================================================================
    // 3D POINTER ANCHORS (NODE A, B, C PINNED TO SIMULATED AIRFRAME)
    // =========================================================================
    const anchorA = new THREE.Object3D()
    anchorA.position.set(0, 1.1, 10.5) // Nose / Cockpit Avionics Bay
    planeGroup.add(anchorA)

    const anchorB = new THREE.Object3D()
    anchorB.position.set(-5.5, -0.2, 1.0) // Wing Junction / Bus Line
    planeGroup.add(anchorB)

    const anchorC = new THREE.Object3D()
    anchorC.position.set(0, 4.6, -13.2) // Tail Fin / GPS Receiver
    planeGroup.add(anchorC)

    threeRef.current = {
      scene,
      camera,
      renderer,
      controls,
      planeGroup,
      anchorA,
      anchorB,
      anchorC,
      targetRotX: initPose.rotX,
      targetRotZ: initPose.rotZ,
      targetPosY: initPose.posY,
      targetCamPos: new THREE.Vector3(...initPose.camPos),
      animId: null,
    }

    // Direct Screen Projection Helper
    const getScreenPos = (obj3D: THREE.Object3D) => {
      const vector = new THREE.Vector3()
      obj3D.getWorldPosition(vector)
      vector.project(camera)
      const w = canvasContainer.clientWidth
      const h = canvasContainer.clientHeight
      return {
        x: (vector.x * 0.5 + 0.5) * w,
        y: -(vector.y * 0.5 - 0.5) * h,
        z: vector.z,
      }
    }

    // Animation & Smooth Attitude Transition Loop
    const clock = new THREE.Clock()
    let isRunning = true

    const animate = () => {
      if (!isRunning) return
      threeRef.current!.animId = requestAnimationFrame(animate)

      const delta = clock.getDelta()
      const t = threeRef.current!

      // Smooth, calm transition to target flight attitude (NO continuous wobbling)
      t.planeGroup.rotation.x += (t.targetRotX - t.planeGroup.rotation.x) * 3 * delta
      t.planeGroup.rotation.z += (t.targetRotZ - t.planeGroup.rotation.z) * 3 * delta
      t.planeGroup.position.y += (t.targetPosY - t.planeGroup.position.y) * 3 * delta

      // Smooth camera transition
      camera.position.lerp(t.targetCamPos, 2.2 * delta)
      controls.update()

      // =======================================================================
      // DIRECT DOM POINTER UPDATES (ZERO REACT RE-RENDER LAG)
      // =======================================================================
      const posA = getScreenPos(anchorA)
      const posB = getScreenPos(anchorB)
      const posC = getScreenPos(anchorC)

      const isVisible = posA.z < 1 && posB.z < 1 && posC.z < 1

      if (isVisible) {
        // Node A: Leader Line + Pin + Tag (Left / Up)
        if (dotARef.current) {
          dotARef.current.setAttribute('cx', String(posA.x))
          dotARef.current.setAttribute('cy', String(posA.y))
        }
        if (lineARef.current) {
          lineARef.current.setAttribute('x1', String(posA.x))
          lineARef.current.setAttribute('y1', String(posA.y))
          lineARef.current.setAttribute('x2', String(posA.x - 45))
          lineARef.current.setAttribute('y2', String(posA.y - 45))
        }
        if (tagARef.current) {
          tagARef.current.style.transform = `translate3d(${posA.x - 240}px, ${posA.y - 65}px, 0)`
          tagARef.current.style.opacity = '1'
        }

        // Node B: Leader Line + Pin + Tag (Left / Down)
        if (dotBRef.current) {
          dotBRef.current.setAttribute('cx', String(posB.x))
          dotBRef.current.setAttribute('cy', String(posB.y))
        }
        if (lineBRef.current) {
          lineBRef.current.setAttribute('x1', String(posB.x))
          lineBRef.current.setAttribute('y1', String(posB.y))
          lineBRef.current.setAttribute('x2', String(posB.x - 40))
          lineBRef.current.setAttribute('y2', String(posB.y + 40))
        }
        if (tagBRef.current) {
          tagBRef.current.style.transform = `translate3d(${posB.x - 240}px, ${posB.y + 30}px, 0)`
          tagBRef.current.style.opacity = '1'
        }

        // Node C: Leader Line + Pin + Tag (Right / Up)
        if (dotCRef.current) {
          dotCRef.current.setAttribute('cx', String(posC.x))
          dotCRef.current.setAttribute('cy', String(posC.y))
        }
        if (lineCRef.current) {
          lineCRef.current.setAttribute('x1', String(posC.x))
          lineCRef.current.setAttribute('y1', String(posC.y))
          lineCRef.current.setAttribute('x2', String(posC.x + 45))
          lineCRef.current.setAttribute('y2', String(posC.y - 45))
        }
        if (tagCRef.current) {
          tagCRef.current.style.transform = `translate3d(${posC.x + 48}px, ${posC.y - 65}px, 0)`
          tagCRef.current.style.opacity = '1'
        }
      }

      renderer.render(scene, camera)
    }

    animate()

    const handleResize = () => {
      if (!canvasContainer) return
      const newW = canvasContainer.clientWidth
      const newH = canvasContainer.clientHeight
      camera.aspect = newW / newH
      camera.updateProjectionMatrix()
      renderer.setSize(newW, newH)
    }

    const observer = new ResizeObserver(handleResize)
    observer.observe(canvasContainer)

    return () => {
      isRunning = false
      if (threeRef.current?.animId) {
        cancelAnimationFrame(threeRef.current.animId)
      }
      observer.disconnect()
      controls.dispose()
      renderer.dispose()
      if (canvasContainer.contains(renderer.domElement)) {
        canvasContainer.removeChild(renderer.domElement)
      }
    }
  }, [displayMode])

  const handlePrev = () => {
    setActiveStoryAct(
      (activeStoryAct - 1 + STORY_ACTS.length) % STORY_ACTS.length
    )
  }

  const handleNext = () => {
    setActiveStoryAct((activeStoryAct + 1) % STORY_ACTS.length)
  }

  return (
    <div
      ref={containerRef}
      className="relative flex h-full w-full flex-col overflow-hidden bg-[#070a12] text-white select-none font-sans"
    >
      {/* =====================================================================
          1. THE SIMULATED FLIGHT VISUALIZATION WITH LEADER LINE POINTERS
          ===================================================================== */}
      <div className="relative flex-1 w-full h-full overflow-hidden">
        {displayMode === 'simulated' ? (
          <>
            {/* Three.js Simulated 3D Aircraft Canvas */}
            <div ref={canvasRef} className="absolute inset-0 z-0 h-full w-full" />

            {/* Dynamic SVG Leader Line Pointers (Points to Node A, B, C on Simulated Flight) */}
            <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full">
              {/* Leader Line A (Nose / FMS) */}
              <line
                ref={lineARef}
                x1="0"
                y1="0"
                x2="0"
                y2="0"
                stroke={currentAct.nodes.a.isTrouble ? '#ef4444' : '#ffffff'}
                strokeWidth="1.5"
                strokeDasharray="4 2"
                opacity="0.85"
              />
              <circle
                ref={dotARef}
                cx="0"
                cy="0"
                r="3.5"
                fill={currentAct.nodes.a.isTrouble ? '#ef4444' : '#38bdf8'}
              />

              {/* Leader Line B (Wing / AFDX Bus) */}
              <line
                ref={lineBRef}
                x1="0"
                y1="0"
                x2="0"
                y2="0"
                stroke={currentAct.nodes.b.isTrouble ? '#f59e0b' : '#ffffff'}
                strokeWidth="1.5"
                strokeDasharray="4 2"
                opacity="0.85"
              />
              <circle
                ref={dotBRef}
                cx="0"
                cy="0"
                r="3.5"
                fill={currentAct.nodes.b.isTrouble ? '#f59e0b' : '#38bdf8'}
              />

              {/* Leader Line C (Tail Fin / GPS Antenna) */}
              <line
                ref={lineCRef}
                x1="0"
                y1="0"
                x2="0"
                y2="0"
                stroke={currentAct.nodes.c.isTrouble ? '#ef4444' : '#ffffff'}
                strokeWidth="1.5"
                strokeDasharray="4 2"
                opacity="0.85"
              />
              <circle
                ref={dotCRef}
                cx="0"
                cy="0"
                r="3.5"
                fill={currentAct.nodes.c.isTrouble ? '#ef4444' : '#38bdf8'}
              />
            </svg>

            {/* Clean, Compact Pointer Tags Pointing Directly to Simulated Flight */}
            {/* Tag A */}
            <div
              ref={tagARef}
              className={`pointer-events-none absolute z-20 w-[190px] rounded border px-2.5 py-1.5 backdrop-blur-md transition-opacity duration-200 ${
                currentAct.nodes.a.isTrouble
                  ? 'border-red-500/70 bg-red-950/85 text-white shadow-lg shadow-red-950/50'
                  : 'border-white/20 bg-black/85 text-slate-200 shadow-md'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono font-bold tracking-wider">
                <span>NODE A // FMS 1</span>
                <span
                  className={`size-1.5 rounded-full ${
                    currentAct.nodes.a.isTrouble ? 'bg-red-400' : 'bg-emerald-400'
                  }`}
                />
              </div>
              <div className="text-[11px] font-semibold truncate text-white mt-0.5">
                {currentAct.nodes.a.tag}
              </div>
            </div>

            {/* Tag B */}
            <div
              ref={tagBRef}
              className={`pointer-events-none absolute z-20 w-[190px] rounded border px-2.5 py-1.5 backdrop-blur-md transition-opacity duration-200 ${
                currentAct.nodes.b.isTrouble
                  ? 'border-amber-500/70 bg-amber-950/85 text-white shadow-lg shadow-amber-950/50'
                  : 'border-white/20 bg-black/85 text-slate-200 shadow-md'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono font-bold tracking-wider">
                <span>NODE B // AVIONICS BUS</span>
                <span
                  className={`size-1.5 rounded-full ${
                    currentAct.nodes.b.isTrouble ? 'bg-amber-400' : 'bg-emerald-400'
                  }`}
                />
              </div>
              <div className="text-[11px] font-semibold truncate text-white mt-0.5">
                {currentAct.nodes.b.tag}
              </div>
            </div>

            {/* Tag C */}
            <div
              ref={tagCRef}
              className={`pointer-events-none absolute z-20 w-[190px] rounded border px-2.5 py-1.5 backdrop-blur-md transition-opacity duration-200 ${
                currentAct.nodes.c.isTrouble
                  ? 'border-red-500/70 bg-red-950/85 text-white shadow-lg shadow-red-950/50'
                  : 'border-white/20 bg-black/85 text-slate-200 shadow-md'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono font-bold tracking-wider">
                <span>NODE C // GPS RECEIVER</span>
                <span
                  className={`size-1.5 rounded-full ${
                    currentAct.nodes.c.isTrouble ? 'bg-red-400' : 'bg-emerald-400'
                  }`}
                />
              </div>
              <div className="text-[11px] font-semibold truncate text-white mt-0.5">
                {currentAct.nodes.c.tag}
              </div>
            </div>
          </>
        ) : (
          /* Alternate Real Photo Flight View */
          <div className="relative w-full h-full">
            <Image
              key={currentAct.realImage}
              src={currentAct.realImage}
              alt={currentAct.alt}
              fill
              priority
              unoptimized
              className="object-cover object-center transition-opacity duration-500"
            />
          </div>
        )}

        {/* Soft Vignettes for High Visual Contrast */}
        <div className="pointer-events-none absolute inset-0 bg-radial from-transparent via-black/10 to-black/75" />
        <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-linear-to-b from-black/85 to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-48 bg-linear-to-t from-[#070a12] via-[#070a12]/80 to-transparent" />

        {/* Minimal Top Header: Identification & View Mode Switcher */}
        <div className="absolute top-4 inset-x-6 z-30 flex items-center justify-between text-xs pointer-events-auto">
          <div className="flex items-center gap-2.5">
            <span className="font-semibold tracking-wider text-slate-100 uppercase">
              {tree.id}
            </span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-300">{tree.route}</span>
            <span className="text-slate-600">·</span>
            <span className="text-slate-400 font-mono text-[11px]">
              Tail: {tree.tailNumber}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle: Simulated 3D Jet vs Real Photo */}
            <div className="flex items-center rounded-lg border border-white/10 bg-black/60 p-0.5 backdrop-blur-md">
              <button
                type="button"
                onClick={() => setDisplayMode('simulated')}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-medium transition-all ${
                  displayMode === 'simulated'
                    ? 'bg-sky-500/30 text-sky-300 border border-sky-400/40 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Eye className="size-3" />
                <span>Simulated 3D Flight</span>
              </button>
              <button
                type="button"
                onClick={() => setDisplayMode('photo')}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-medium transition-all ${
                  displayMode === 'photo'
                    ? 'bg-sky-500/30 text-sky-300 border border-sky-400/40 font-semibold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Camera className="size-3" />
                <span>Real 3D Image</span>
              </button>
            </div>

            {/* Auto-Play */}
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/60 px-2.5 py-1 text-[11px] font-medium text-slate-300 hover:text-white transition-colors backdrop-blur-md"
            >
              {isPlaying ? <Pause className="size-3 text-sky-400" /> : <Play className="size-3 text-slate-400" />}
              <span>{isPlaying ? 'Pause' : 'Auto-Play'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* =====================================================================
          2. THE STORY NARRATION CARD BELOW THE PLANE (PRESERVED & STREAMLINED)
          ===================================================================== */}
      <div className="relative z-30 w-full px-6 pb-5 pt-1">
        <div className="mx-auto max-w-4xl rounded-2xl border border-white/10 bg-[#0d121f]/95 p-4 sm:p-5 shadow-2xl backdrop-blur-xl">
          {/* Header Row: Phase + Telemetry Snapshot */}
          <div className="flex items-center justify-between border-b border-white/10 pb-2.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[11px] font-bold text-white">
                ACT {currentAct.actNumber} OF 05
              </span>
              <span className="font-semibold tracking-wide text-slate-300 uppercase">
                {currentAct.phase}
              </span>
            </div>

            <div className="flex items-center gap-3 font-mono text-[11px] text-slate-400">
              <span>
                ALT: <strong className="text-white">{currentAct.flightData.altitude}</strong>
              </span>
              <span>·</span>
              <span>
                SPD: <strong className="text-white">{currentAct.flightData.speed}</strong>
              </span>
              <span>·</span>
              <span className="hidden sm:inline">
                {currentAct.flightData.attitude}
              </span>
            </div>
          </div>

          {/* Title & Core Story Narrative */}
          <div className="py-2.5">
            <h2 className="text-sm sm:text-base font-bold text-white tracking-tight">
              {currentAct.title}
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-300">
              {currentAct.story}
            </p>
          </div>

          {/* Minimal 3-Node Subsystem Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-2.5 border-t border-white/10">
            {/* Node A */}
            <div
              className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                currentAct.nodes.a.isTrouble
                  ? 'border-red-500/40 bg-red-950/30'
                  : 'border-white/5 bg-white/5'
              }`}
            >
              <div className="flex items-center justify-between font-semibold">
                <span className="text-slate-300">{currentAct.nodes.a.name}</span>
                <span
                  className={`size-1.5 rounded-full ${
                    currentAct.nodes.a.isTrouble ? 'bg-red-400' : 'bg-emerald-400'
                  }`}
                />
              </div>
              <div className="mt-0.5 text-[11px] text-slate-400 font-mono truncate">
                {currentAct.nodes.a.status}
              </div>
            </div>

            {/* Node B */}
            <div
              className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                currentAct.nodes.b.isTrouble
                  ? 'border-amber-500/40 bg-amber-950/30'
                  : 'border-white/5 bg-white/5'
              }`}
            >
              <div className="flex items-center justify-between font-semibold">
                <span className="text-slate-300">{currentAct.nodes.b.name}</span>
                <span
                  className={`size-1.5 rounded-full ${
                    currentAct.nodes.b.isTrouble ? 'bg-amber-400' : 'bg-emerald-400'
                  }`}
                />
              </div>
              <div className="mt-0.5 text-[11px] text-slate-400 font-mono truncate">
                {currentAct.nodes.b.status}
              </div>
            </div>

            {/* Node C */}
            <div
              className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
                currentAct.nodes.c.isTrouble
                  ? 'border-red-500/40 bg-red-950/30'
                  : 'border-white/5 bg-white/5'
              }`}
            >
              <div className="flex items-center justify-between font-semibold">
                <span className="text-slate-300">{currentAct.nodes.c.name}</span>
                <span
                  className={`size-1.5 rounded-full ${
                    currentAct.nodes.c.isTrouble ? 'bg-red-400' : 'bg-emerald-400'
                  }`}
                />
              </div>
              <div className="mt-0.5 text-[11px] text-slate-400 font-mono truncate">
                {currentAct.nodes.c.status}
              </div>
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="mt-3 flex items-center justify-between pt-1">
            <button
              type="button"
              onClick={handlePrev}
              className="flex items-center gap-1 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
            >
              <ChevronLeft className="size-4" />
              <span>Previous</span>
            </button>

            {/* 5 Step Indicator Pills */}
            <div className="flex items-center gap-1.5">
              {STORY_ACTS.map((act, index) => {
                const isActive = activeStoryAct === index
                return (
                  <button
                    key={act.id}
                    type="button"
                    onClick={() => setActiveStoryAct(index)}
                    className={`h-2 rounded-full transition-all ${
                      isActive
                        ? 'w-7 bg-white'
                        : 'w-2 bg-white/20 hover:bg-white/50'
                    }`}
                    title={`Jump to Act ${act.actNumber}: ${act.phase}`}
                  />
                )
              })}
            </div>

            <button
              type="button"
              onClick={handleNext}
              className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/10 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-white/20 transition-colors"
            >
              <span>{activeStoryAct === STORY_ACTS.length - 1 ? 'Restart' : 'Next'}</span>
              <ChevronRight className="size-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
