import os
import webbrowser

def generate_case_file():
    # Forensic Case File: The Memory Trap
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Forensics: Incident Storyboard</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { border-bottom: 2px solid #30363d; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { color: #58a6ff; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 2px; }
        .metadata { display: flex; gap: 20px; font-size: 14px; color: #8b949e; }
        .metadata span { background: #161b22; padding: 4px 8px; border-radius: 4px; border: 1px solid #30363d; }
        .story-section { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #58a6ff; }
        .story-section h2 { margin-top: 0; color: #ffffff; font-size: 18px; border-bottom: 1px dashed #30363d; padding-bottom: 10px; }
        .fault-box { background: #2a1114; border: 1px solid #ff7b72; border-radius: 6px; padding: 15px; margin: 15px 0; color: #ff7b72; }
        .fault-box h3 { margin: 0 0 10px 0; font-size: 14px; }
        .pilot-action { background: #0c2d4a; border: 1px solid #58a6ff; border-radius: 6px; padding: 15px; margin: 15px 0; color: #79c0ff; }
        .forensics-view { background: #121d14; border: 1px solid #3fb950; border-radius: 6px; padding: 15px; margin: 15px 0; color: #56d364; }
        .node-chip { display: inline-block; background: #21262d; border: 1px solid #30363d; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; color: #d2a8ff; margin-right: 5px; }
        .highlight { color: #f2cc60; font-weight: bold; }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>Forensic Case File: The Memory Trap</h1>
        <div class="metadata">
            <span>ROUTE: Madurai (IXM) ➔ Mumbai (BOM)</span>
            <span>AIRCRAFT: Boeing Commercial</span>
            <span>SYSTEM: Honeywell FMS</span>
        </div>
    </div>

    <div class="story-section">
        <h2>1. The Calm Before (Madurai Departure)</h2>
        <p>It’s early morning at Madurai Airport (IXM). The aircraft is sitting at the gate, engines spooling up. Inside the avionics bay, the Honeywell systems are waking up.</p>
        <p>According to our Python timeline script, the <span class="node-chip">Node A (FMS)</span> logged a perfect <strong>Schema A (Gate)</strong> boot sequence. Baseline power is stable at 36°C. The <span class="node-chip">Node B (Bus)</span> and <span class="node-chip">Node C (GPS)</span> are in cold standby, silently waiting for the flight to begin. Everything looks perfectly nominal.</p>
    </div>

    <div class="story-section" style="border-left-color: #ff7b72;">
        <h2>2. The Trap Springs (Ascent)</h2>
        <p>The pilot pushes the throttles forward. The plane hurdles down Runway 09. As the aircraft hits V1 rotation and the nose lifts into the sky, the FMS shifts to its "AIRBORNE" schema to pull departure repository data.</p>
        <p>Suddenly, it hits a wall.</p>
        
        <div class="fault-box">
            <h3>⚠️ SYSTEM ALARM: CRITICAL FAULT TRIGGERED</h3>
            <strong>Honeywell Fault Code:</strong> 6074 (FMS Data Repository Access Failure)<br>
            <strong>Forensic Trace:</strong> CPU Instruction Trap @ Address <span class="highlight">0x18000CE0</span><br>
            <strong>Impact:</strong> The primary software thread completely blocks. Memory is locked.
        </div>
        
        <p>Because Node A freezes, <span class="node-chip">Node B</span> panics. It detects a bus timeout and tries to automatically re-route the data, but the buffer stack begins to overflow. The system violently drops from Dual Redundancy into <strong>Single Mode</strong>.</p>
    </div>

    <div class="story-section" style="border-left-color: #58a6ff;">
        <h2>3. The Pilot's Response (Cruise Phase)</h2>
        <p>Up in the cockpit, the master caution light flashes. The EICAS screen warns the pilot: <em>"FMS DEGRADED - SINGLE MODE"</em>. The automated vertical guidance is compromised.</p>
        
        <div class="pilot-action">
            <h3>👨‍✈️ COCKPIT LOG: OPERATOR INTERVENTION</h3>
            The timeline script detects multiple <strong>"FMS Button Push"</strong> events in the MCDU buffer. The pilot immediately takes manual control of the navigation. They manually punch in the cruise altitude (<strong>FL350</strong>) and physically clear the conflicting altitude constraints to keep the aircraft flying smoothly despite the background software chaos.
        </div>
    </div>

    <div class="story-section" style="border-left-color: #f85149;">
        <h2>4. The Cascade (Descent into Mumbai)</h2>
        <p>As the Boeing aligns with the Mumbai (BOM) glideslope, the cascading data failure finally reaches the tail of the plane. Because Node B has been "flapping" (overloading the network with re-transmission requests), it starves the GPS unit of data.</p>
        <p><span class="node-chip">Node C (GPS)</span> drops out entirely. It experiences a Cold Start Re-sync Reset. The coordinates instantly read <strong>0.000000 Lat/Lon</strong>, and the barometric altitude freezes at 2,870 feet.</p>
        <p>Seeing the navigation map freeze, the pilot executes a hard <strong>FMS Service Restart</strong> command, taking the plane entirely on visual and manual backup instruments to touch down safely on the Mumbai tarmac.</p>
    </div>

    <div class="story-section" style="border-left-color: #3fb950;">
        <h2>5. The Investigation (How We Solved It)</h2>
        <p>When the plane landed, the maintenance crew saw a massive mess of errors: GPS failures, Bus timeouts, and FMS faults. Without our tool, they might have replaced the expensive GPS antenna (Node C) thinking it was broken.</p>
        
        <div class="forensics-view">
            <h3>🔬 FORENSIC DASHBOARD ANALYSIS</h3>
            By running the <code>flight_forensics_dashboard.py</code> script, we independently parsed the HTML logs for each node. The script separated the timeline by <strong>Node</strong> and <strong>Flight Phase</strong>.<br><br>
            Because the script uses exact timestamps (Δt) and tags (GROUND_FAULT vs PHASE_CHANGE), we could trace the exact timeline backwards:<br>
            1. The GPS (Node C) failed at descent.<br>
            2. The Bus (Node B) overflowed during cruise.<br>
            3. But the <strong>Root Cause</strong> happened at the exact second of takeoff in Node A (Trap <code>0x18000CE0</code>).<br><br>
            <strong>Conclusion:</strong> The hardware is perfectly fine. The issue is a software memory leak in the Honeywell FMS repository triggered by the takeoff phase transition.
        </div>
    </div>

</div>

</body>
</html>"""

    output_filename = "data/flight_case_story.html"
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write(html_content)
    
    print(f"Success! Generated {output_filename}")
    full_path = os.path.abspath(output_filename)
    print(f"File URI: file://{full_path}")

if __name__ == "__main__":
    generate_case_file()
