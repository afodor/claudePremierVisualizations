# premierRenewal Figure Creation Instructions

These figures visualize a microbiome sentinel network — autonomous robots that detect and remediate pathogens (bacteria, mold) in hospitals and homes. This guide covers all figure types so another Claude Code instance can create or modify them.

## Project Location
- `C:\premierRenewal\figures\` — all figures live here
- `C:\premierRenewal\figures\keep\` — preserved original versions (copy here before major edits)
- `C:\premierRenewal\figures\old\` — deprecated versions

## Two Figure Types

### Type 1: Interactive 3D Scenes (Three.js)
Self-contained HTML files using Three.js 0.163.0 via CDN. User opens them in a browser, drags to orbit, hovers for tooltips/labels.

**Files:**
- `figure1C_3d_interactive.html` — Overview: street scene with hospital + home buildings, 10 robots, server rooms
- `narrative_A_3d_ptrap.html` — Close-up: hospital ICU room, P-trap pipe with biofilm, roomba bots
- `narrative_B_3d_basement.html` — Close-up: residential basement, mold colony on wall, patrol + spray bots

### Type 2: SVG Floor Plan Diagrams
Self-contained HTML files wrapping an `<svg>`. Designed for print/static use. Rendered to PNG via Node.js `sharp`.

**Files:**
- `keep/figure3_hospital_ward.html` → `figure3_hospital_ward.png` — Hospital ward floor plan + dashboard
- `figure3B_residential_basement.html` → `figure3B_residential_basement.png` — Basement floor plan + dashboard

---

## Type 1: Three.js 3D Scenes — How to Build

### Boilerplate Template
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Figure Title</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0e1a; overflow: hidden; font-family: 'Segoe UI', Tahoma, sans-serif; }
  /* Info banner, labels, tooltip styles go here */
</style>
</head>
<body>
<!-- Info banner, legend, tooltip divs -->
<script type="importmap">
{ "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.163.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.163.0/examples/jsm/"
} }
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
// If using CSS labels:
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
// ... scene, camera, renderer, controls, lighting, geometry, animation ...
</script>
</body>
</html>
```

### Scene Setup Pattern
```js
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1c28);

const camera = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.1, 200);
camera.position.set(8, 7, 12);  // adjust per scene

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.target.set(0, 2, -1);
```

### Environment Map (IBL-style gradient sky)
```js
const pmrem = new THREE.PMREMGenerator(renderer);
const eScene = new THREE.Scene();
const eMat = new THREE.ShaderMaterial({ side: THREE.BackSide,
  uniforms: { top:{value:new THREE.Color(0x3a4a6a)}, bot:{value:new THREE.Color(0x0a0a12)} },
  vertexShader: `varying float vY; void main(){vY=normalize(position).y;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
  fragmentShader: `uniform vec3 top,bot;varying float vY;void main(){gl_FragColor=vec4(mix(bot,top,vY*.5+.5),1.0);}`
});
eScene.add(new THREE.Mesh(new THREE.SphereGeometry(50,32,16), eMat));
scene.environment = pmrem.fromScene(eScene).texture;
```

### Box Helper (used everywhere)
```js
function box(w,h,d,mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), mat);
  m.castShadow = true; m.receiveShadow = true; return m;
}
// or for figure1C:
function makeBox(w,h,d,mat,x,y,z) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), mat);
  mesh.position.set(x,y,z); mesh.castShadow = true; mesh.receiveShadow = true;
  return mesh;
}
```

### Procedural Canvas Textures
Create textures in code (no external images needed):
```js
function mkTex(size, fn) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  fn(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
}
// Example: tile floor
const tileTex = mkTex(512, (ctx,s) => {
  ctx.fillStyle='#c0b8a8'; ctx.fillRect(0,0,s,s);
  ctx.fillStyle='#e8e4dc';
  for(let y=0;y<s;y+=64) for(let x=0;x<s;x+=64) ctx.fillRect(x+2,y+2,60,60);
}); tileTex.repeat.set(3,3);
```

### Robot Factory Patterns

**figure1C: Small wheeled robots (overview scene)**
```js
function createRobot(eyeMat, label, tooltipText, scale) {
  const s = scale || 1;
  const group = new THREE.Group();
  group.userData = { label, tooltip: tooltipText, isRobot: true };
  // Body (box), head (box), eyes (spheres), antenna (cylinder+sphere), wheels (cylinders), eye glow (PointLight)
  return group;
}
```

**narrative_A: Roomba-style bots (flat disc)**
```js
function createRoombaBot(eyeColor, emissiveColor, label) {
  const g = new THREE.Group();
  // CylinderGeometry disc body (r=0.5, h=0.16)
  // Dome on top (half-sphere)
  // Eyes (2 small spheres)
  // Front sensor bar, LED torus ring, eye glow PointLight
  return g;
}
```

**narrative_B: Large bots with articulated arms**
```js
function createBigBot(eyeColor, emissiveColor, showArms) {
  const g = new THREE.Group();
  // Larger disc body (r=0.75), dome, face plate, eyes, eyebrows, sensor bar, LED ring, antenna
  if (showArms) {
    // Sensing Arm (right): shoulder sphere → upper arm cylinder → elbow sphere → forearm → sensor cone tip
    // Intervention Arm (left): same structure → nozzle box tip
    // Arm labels via addArmLabel() stored in g.userData.armLabelInners
  }
  return g;
}
```

### CSS2D Label System (narrative files)
Labels appear as HTML overlays positioned in 3D space. Hidden by default, shown on hover.

```js
// Requires CSS2DRenderer setup:
const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(innerWidth, innerHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0';
labelRenderer.domElement.style.pointerEvents = 'none';
document.body.appendChild(labelRenderer.domElement);

// CSS: .step-text { opacity: 0; transition: opacity 0.25s ease; }

// Label factory:
function addLabel(text, color, lx,ly,lz, tx,ty,tz) {
  // Creates CSS2DObject at (lx,ly,lz) with optional dashed leader line to (tx,ty,tz)
  // Returns { inner: HTMLElement, line: Line|null, dot: Mesh|null }
}

// Bot-attached labels (follow the bot):
function addBotLabel(text, color, bot) {
  const label = new CSS2DObject(div);
  label.position.set(0, 1.0, 0);  // above the bot
  bot.add(label);                   // parented to bot group
  return { inner, line: null, dot: null };
}
```

### Hover System (raycaster-based)
```js
const hoverMap = new Map();  // Object3D → { inners: [], lines: [], dots: [] }

function registerHover(obj, labelData) { /* ... */ }
function findHoverTarget(obj) {
  // Walk up parent chain until finding a registered object
}
function showLabelsFor(target) { /* set opacity 1, visible true */ }
function hideLabelsFor(target) { /* set opacity 0, visible false */ }

renderer.domElement.addEventListener('mousemove', (event) => {
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(scene.children, true);
  // Find first hit with registered hover target, show/hide labels
});
```

**IMPORTANT: Do NOT use invisible hitbox meshes.** They intercept raycaster rays and break hover on actual objects. Register the actual scene objects/groups directly. This was a proven bug.

### Tooltip System (figure1C style — no CSS2D)
figure1C uses a simpler HTML tooltip that follows the mouse:
```js
renderer.domElement.addEventListener('mousemove', (e) => {
  raycaster.setFromCamera(mouse, camera);
  for (const r of robots) {
    const intersects = raycaster.intersectObjects(r.mesh.children, true);
    if (intersects.length > 0) {
      tooltip.style.left = (e.clientX + 15) + 'px';
      tooltip.style.top = (e.clientY - 10) + 'px';
      tooltip.querySelector('.tt-title').textContent = r.mesh.userData.label;
      tooltip.querySelector('.tt-body').textContent = r.mesh.userData.tooltip;
    }
  }
});
```

### Floating Scene Labels (figure1C style — HTML overlays projected from 3D)
For persistent labels that track world positions as the camera moves (no CSS2DRenderer needed):
```css
.scene-label {
  position: absolute; z-index: 15; pointer-events: none;
  font-size: 15px; font-weight: 600; color: #ddeeff; text-align: center; white-space: nowrap;
  text-shadow: 0 0 8px rgba(0,0,0,0.9), 0 0 20px rgba(0,100,200,0.4);
}
.scene-label .label-accent { display: block; width: 40px; height: 3px; margin: 4px auto 0; border-radius: 2px; }
```
```html
<div id="labelHospital" class="scene-label">Use Case 1: Hospital<span class="label-accent" style="background:#cc3333"></span></div>
<div id="labelHome" class="scene-label">Use Case 2: Home<span class="label-accent" style="background:#e8c840"></span></div>
<div id="labelHub" class="scene-label">Central AI Hub<span class="label-accent" style="background:#00ddff"></span></div>
```
```js
const sceneLabels = [
  { el: document.getElementById('labelHospital'), worldPos: new THREE.Vector3(-16, 14.5, 0) },
  { el: document.getElementById('labelHome'),     worldPos: new THREE.Vector3(16, 10, 0) },
  { el: document.getElementById('labelHub'),      worldPos: new THREE.Vector3(0, 24, 0) },
];

function updateSceneLabels() {
  const halfW = window.innerWidth / 2;
  const halfH = window.innerHeight / 2;
  for (const lbl of sceneLabels) {
    const v = lbl.worldPos.clone().project(camera);
    if (v.z > 1) { lbl.el.style.display = 'none'; continue; }
    lbl.el.style.display = 'block';
    lbl.el.style.left = (v.x * halfW + halfW - lbl.el.offsetWidth / 2) + 'px';
    lbl.el.style.top  = (-v.y * halfH + halfH - lbl.el.offsetHeight / 2) + 'px';
  }
}
// Call updateSceneLabels() in the animate loop before renderer.render()
```
World positions: Hospital label at (-16, 14.5, 0) above the hospital roof, Home label at (16, 10, 0) above the home roof, Central AI Hub label at (0, 24, 0) just above the hub rings.

### Robot Animation (elliptical patrol paths)
```js
const roombaPaths = [
  { bot: roomba1, cx: -1, cz: 1.5, rx: 3.5, rz: 2.5, speed: 0.04, t: 0 },
  // cx,cz = center; rx,rz = radii; speed ~0.03-0.05 for slow, 0.08-0.15 for fast
];

// In animate():
roombaPaths.forEach(rp => {
  rp.t += dt * rp.speed;
  const a = (rp.t % 1) * Math.PI * 2;
  rp.bot.position.x = rp.cx + Math.sin(a) * rp.rx;
  rp.bot.position.z = rp.cz + Math.cos(a) * rp.rz;
  rp.bot.rotation.y = Math.atan2(Math.cos(a) * rp.rx, -Math.sin(a) * rp.rz);
});
```

### Data/Communication Particles
figure1C uses quadratic bezier arcs between bots and hubs:
```js
// Bot positions → local hub → central hub
// Each particle has { pathIdx, t, speed }
// In animate(): quadratic bezier interpolation with jitter
const oneMinusT = 1 - t;
positions[i*3] = oneMinusT*oneMinusT*from.x + 2*oneMinusT*t*mid.x + t*t*to.x;
```

### figure1C Specific: Multi-Building Overview Scene
- **Layout**: Hospital at (-16,0,0), Home at (16,0,0), road between them
- **Hospital**: 3 floors (FLOOR_H=4), 20x15 footprint, transparent walls, furnished rooms (patient, ICU, OR, nurse station, server room), MRSA hotspot, local AI hub
- **Home**: basement + first floor + pitched roof, kitchen/living/bathroom, mold colony in basement, server closet, local AI hub
- **Central AI Hub**: floating at (0,22,0) with rotating torus rings
- **Robots**: 6 hospital bots + 4 home bots, each with named patrol path in `getRobotPosition()` switch
- **10 robot types**: Sensor Bot, Sterilize Bot, Air Monitor, P-trap MicroBot, Supply Bot, Data Room Sentry, Basement MicroGuard, First Floor Patrol, Kitchen Air Sampler, HVAC/Roof Monitor
- **Data particles**: 180 particles across 12 communication paths (bots→local hubs→central hub)
- **Visual extras**: sky gradient canvas texture, fog, street lights, trees, bushes, sidewalks, lane markings

### narrative_A Specific: Hospital ICU P-Trap Scene
- Single hospital room with patient in bed, IV pole, monitor
- Sink/vanity with detailed P-trap pipe system (TorusGeometry for U-bend)
- CRE bacteria (red CapsuleGeometry rods) in biofilm
- Treated zone with multi-colored probiotic organisms
- 3 pipe robots (tiny, CapsuleGeometry bodies) at different positions in the plumbing
- 3 roomba bots patrolling the floor (Surface Sampler, Air Quality Bot, UV Sterilizer)
- AI Hub on wall, dashboard panel, communication beam (CatmullRomCurve3)
- Zoomed inset panel showing competitive exclusion (before/after)
- 6 fixed hover labels + 3 bot-attached labels

### narrative_B Specific: Basement Fungi Scene
- Cinder block walls (procedural texture), concrete floor, wood ceiling/joists
- Water heater, washer, dryer, shelving with items, staircase, ceiling pipes, small window
- Large mold colony: clusters of SphereGeometry (flattened z=0.35), conidiophore stalks, floating spores, moisture stain
- 2 large bots with articulated sensing + intervention arms (createBigBot)
- VOC particles floating near mold, spray particles from intervention bot
- Probiotic coating (transparent green circle on wall)
- AI Hub + phone notification display
- Hover labels inside the room

---

## Type 2: SVG Floor Plan Diagrams — How to Build

### Common SVG Boilerplate
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Figure Title</title>
<style>
  body { margin: 0; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
  svg { max-width: 2400px; width: 100%; height: auto; }
</style>
</head>
<body>
<svg viewBox="0 0 2400 1430" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif">
  <defs>
    <!-- 1. Header gradient -->
    <linearGradient id="headerBar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#COLOR1"/>
      <stop offset="100%" stop-color="#COLOR2"/>
    </linearGradient>
    <!-- 2. Drop shadow for panels -->
    <filter id="shadow">
      <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.1"/>
    </filter>
    <!-- 3. Floor patterns -->
    <!-- 4. Arrow markers for data/alert lines -->
    <marker id="arrowData" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L10,4 L0,8" fill="#3a7aba"/>
    </marker>
    <marker id="arrowAlert" markerWidth="10" markerHeight="8" refX="10" refY="4" orient="auto">
      <path d="M0,0 L10,4 L0,8" fill="#cc3333"/>
    </marker>
  </defs>
  <!-- ... content ... -->
</svg>
</body>
</html>
```

### Layout Grid
- **Total canvas**: 2400 x 1430
- **Header bar**: x=0, y=0, full width, height=85
- **Floor plan area**: x=50, y=105, width=1460, height=940-1000
- **Dashboard panel**: x=1560, y=105, width=800, height=940-1000
- **Caption**: x=50, y=~1150-1200, height=~100-115
- **Legend**: y=~1295-1320, two boxes side by side (710px each), starting at x=50 and x=780

### Font Sizes (CRITICAL)
Use LARGE fonts — the user found 6-10pt unreadable:
- **Main title** (header bar): 46pt bold
- **Section/room headers**: 26-28pt bold
- **Dashboard title**: 34pt bold
- **Dashboard subheaders**: 28pt bold
- **Body text / status lines**: 22-24pt
- **Small annotations**: 20pt (minimum)
- **Caption title**: 26pt bold, caption body: 22pt

### Status Indicator Colors
- Green `#2dc653` = healthy/nominal
- Orange `#f4a020` = caution/elevated
- Red `#dd4444` = alert/pathogen detected

---

### Figure 3: Hospital Ward (figure3_hospital_ward.html)

**Source**: `keep/figure3_hospital_ward.html` → rendered to `figure3_hospital_ward.png`
**Theme**: Blue — header gradient `#1a4a6a → #2a7aaa`, page background `#f8fafc`

#### Defs — Floor Patterns
```xml
<!-- Checkerboard tile (used in rooms) -->
<pattern id="tileFloor" width="24" height="24" patternUnits="userSpaceOnUse">
  <rect width="24" height="24" fill="#eef2f6"/>
  <rect width="12" height="12" fill="#e4e8ee"/>
  <rect x="12" y="12" width="12" height="12" fill="#e4e8ee"/>
</pattern>
<!-- Corridor tile (slightly different shade) -->
<pattern id="corridorFloor" width="30" height="30" patternUnits="userSpaceOnUse">
  <rect width="30" height="30" fill="#e8ecf0"/>
  <rect width="15" height="15" fill="#e0e4e8"/>
  <rect x="15" y="15" width="15" height="15" fill="#e0e4e8"/>
</pattern>
```

#### Building Shell & Corridor
```xml
<!-- Outer shell -->
<rect x="50" y="105" width="1460" height="1000" rx="6" fill="#d8e0e8" stroke="#8a9aaa" stroke-width="2" filter="url(#shadow)"/>
<!-- Horizontal corridor splitting top/bottom rooms -->
<rect x="50" y="470" width="1460" height="120" fill="url(#corridorFloor)" stroke="#a0aab4" stroke-width="1"/>
<text x="780" y="542" text-anchor="middle" fill="#6a7a8a" font-size="30" font-weight="bold" letter-spacing="4" opacity="0.5">MAIN CORRIDOR</text>
```

#### Room Layout (8 rooms, 4 top + 4 bottom)
Top rooms (y=115, height=345, with door openings into corridor via small rect at bottom):
| Room | translate | width | header color | header text color |
|------|-----------|-------|-------------|-------------------|
| Patient Rm 201 | (65, 115) | 335 | `#c8d8e8` | `#4a6a8a` |
| ICU Bay A | (415, 115) | 310 | `#e8c8c8` | `#8a4a4a` |
| Operating Room 1 | (740, 115) | 355 | `#c8e8c8` | `#3a6a3a` |
| Supply / Pharmacy | (1110, 115) | 385 | `#e8e0c8` | `#6a5a3a` |

Bottom rooms (y=600, height=330, with door openings into corridor via small rect at top):
| Room | translate | width | header color | header text color |
|------|-----------|-------|-------------|-------------------|
| Patient Rm 202 | (65, 600) | 335 | `#c8d8e8` | `#4a6a8a` |
| Nurse Station | (415, 600) | 310 | `#d8c8e8` | `#5a4a6a` |
| HVAC / Mechanical | (740, 600) | 355 | `#d8d8d8` | `#555` |
| Waiting Area | (1110, 600) | 385 | `#e8e8c8` | `#6a6a3a` |

#### Room Pattern
Each room is a `<g>` with `transform="translate(X, Y)"`:
```xml
<g transform="translate(65, 115)">
  <!-- Background with tile pattern -->
  <rect x="0" y="0" width="335" height="345" rx="3" fill="url(#tileFloor)" stroke="#a0aab4" stroke-width="1.5"/>
  <!-- Colored header strip (42px tall) -->
  <rect x="0" y="0" width="335" height="42" fill="#c8d8e8"/>
  <!-- Room name centered in header -->
  <text x="168" y="30" text-anchor="middle" fill="#4a6a8a" font-size="26" font-weight="bold">PATIENT RM 201</text>
  <!-- Door opening (small rect bridging into corridor) -->
  <rect x="130" y="335" width="75" height="14" fill="url(#corridorFloor)"/>
  <!-- Furniture inside... -->
</g>
```

#### Drawing Furniture & Equipment

**Hospital bed:**
```xml
<rect x="25" y="70" width="110" height="160" rx="5" fill="#d8e0e8" stroke="#a0b0c0" stroke-width="1"/>
<rect x="30" y="64" width="100" height="26" rx="8" fill="#b8c8d8"/>  <!-- pillow -->
```

**Patient (head + blanket):**
```xml
<circle cx="80" cy="130" r="12" fill="#f0d0b0" stroke="#d0a080" stroke-width="0.8"/>
<rect x="48" y="144" width="64" height="65" rx="3" fill="#a0d0e8" opacity="0.4"/>
```

**Bedside monitor with heartbeat line:**
```xml
<rect x="165" y="90" width="55" height="45" rx="3" fill="#2a3a4a" stroke="#4a6a8a" stroke-width="1"/>
<polyline points="172,110 180,102 188,118 196,106 204,114 210,110" fill="none" stroke="#44dd66" stroke-width="1.5"/>
<text x="192" y="155" text-anchor="middle" fill="#6a8a9a" font-size="22">Vitals</text>
```

**IV stand:**
```xml
<line x1="230" y1="68" x2="230" y2="170" stroke="#999" stroke-width="1.5"/>
<rect x="220" y="58" width="20" height="18" rx="2" fill="#c8d8e8" stroke="#999" stroke-width="0.8"/>
```

**Ventilator (ICU):**
```xml
<rect x="165" y="80" width="55" height="70" rx="4" fill="#ccc" stroke="#999" stroke-width="1"/>
<text x="192" y="122" text-anchor="middle" fill="#555" font-size="22">VENT</text>
<line x1="165" y1="118" x2="135" y2="125" stroke="#999" stroke-width="1.5"/>  <!-- tube to patient -->
```

**OR table + overhead light:**
```xml
<rect x="75" y="100" width="130" height="70" rx="5" fill="#c0d0e0" stroke="#8a9aaa" stroke-width="1.5"/>
<circle cx="140" cy="80" r="28" fill="none" stroke="#ddd" stroke-width="2"/>
<circle cx="140" cy="80" r="16" fill="#fffff0" stroke="#eee" stroke-width="1" opacity="0.5"/>
```

**Shelving (Supply room):**
```xml
<rect x="25" y="58" width="310" height="20" rx="2" fill="#c8c0b0" stroke="#a09880" stroke-width="0.8"/>
<!-- Repeat rows at y=90, y=122, etc. -->
<!-- Small colored items on shelves: -->
<rect x="35" y="46" width="22" height="16" rx="2" fill="#e0d8c8"/>
```

**Nurse station U-shaped desk:**
```xml
<rect x="40" y="90" width="220" height="20" rx="2" fill="#b0a898" stroke="#9a8a78" stroke-width="1"/>
<rect x="40" y="90" width="20" height="110" rx="2" fill="#b0a898" stroke="#9a8a78" stroke-width="1"/>
<rect x="240" y="90" width="20" height="110" rx="2" fill="#b0a898" stroke="#9a8a78" stroke-width="1"/>
```

**HVAC unit + biofilter bank:**
```xml
<rect x="35" y="70" width="165" height="110" rx="6" fill="#b0b8c0" stroke="#8a9aaa" stroke-width="2"/>
<text x="118" y="122" text-anchor="middle" fill="#555" font-size="28" font-weight="bold">HVAC</text>
<!-- Ducts: small horizontal bars -->
<rect x="210" y="95" width="110" height="15" rx="3" fill="#c0c8d0" stroke="#a0a8b0" stroke-width="0.8"/>
<!-- Biofilter bank -->
<rect x="35" y="215" width="280" height="55" rx="4" fill="#d8e0d8" stroke="#8aaa8a" stroke-width="1"/>
<text x="175" y="250" text-anchor="middle" fill="#4a6a4a" font-size="22" font-weight="bold">Probiotic Biofilter Bank</text>
```

**Waiting area chairs (rows of small rounded rects):**
```xml
<rect x="25" y="75" width="45" height="38" rx="4" fill="#a0b8c8" stroke="#8a9aaa" stroke-width="0.8"/>
<!-- Repeat at x+53 intervals for each seat -->
```

**Window:**
```xml
<rect x="195" y="75" width="90" height="70" fill="#c8e8f8" stroke="#8a9aaa" stroke-width="1" rx="2"/>
<line x1="240" y1="75" x2="240" y2="145" stroke="#8a9aaa" stroke-width="0.5"/>  <!-- mullion -->
```

#### MRSA Hotspot (pathogen indicator)
```xml
<g transform="translate(270, 210)">
  <circle cx="0" cy="0" r="14" fill="#dd4444" opacity="0.15"/>
  <circle cx="0" cy="0" r="9" fill="#dd4444" opacity="0.25"/>
  <circle cx="0" cy="0" r="4" fill="#dd4444" opacity="0.5"/>
  <text x="0" y="28" text-anchor="middle" fill="#cc3333" font-size="22" font-weight="bold">MRSA</text>
</g>
```

#### Hospital Robots (4 types)

**1. Sensor Bot (blue #0077b6)** — corridor patrol, has scan lines + movement arrow:
```xml
<g transform="translate(260, 530)">
  <!-- Body -->
  <rect x="-28" y="-18" width="56" height="36" rx="12" fill="#2a3a5a" stroke="#0077b6" stroke-width="2.5"/>
  <!-- Eyes (2 circles + 2 smaller pupils) -->
  <circle cx="-10" cy="-4" r="6" fill="#0077b6" opacity="0.9"/>
  <circle cx="10" cy="-4" r="6" fill="#0077b6" opacity="0.9"/>
  <circle cx="-8" cy="-4" r="3" fill="#004a80"/>
  <circle cx="12" cy="-4" r="3" fill="#004a80"/>
  <!-- Wheels (2 small rounded rects below body) -->
  <rect x="-20" y="18" width="16" height="9" rx="3" fill="#3a3a44"/>
  <rect x="4" y="18" width="16" height="9" rx="3" fill="#3a3a44"/>
  <!-- Antenna (line + circle tip) -->
  <line x1="0" y1="-18" x2="0" y2="-35" stroke="#0077b6" stroke-width="2"/>
  <circle cx="0" cy="-38" r="5" fill="#0077b6"/>
  <!-- Scan lines (dashed, radiating from body center outward) -->
  <line x1="0" y1="-4" x2="-65" y2="-65" stroke="#0077b6" stroke-width="1.2" stroke-dasharray="6,3" opacity="0.5"/>
  <line x1="0" y1="-4" x2="-25" y2="-72" stroke="#0077b6" stroke-width="1.2" stroke-dasharray="6,3" opacity="0.5"/>
  <line x1="0" y1="-4" x2="18" y2="-72" stroke="#0077b6" stroke-width="1.2" stroke-dasharray="6,3" opacity="0.5"/>
  <!-- Movement arrow -->
  <path d="M35,0 L80,0" fill="none" stroke="#0077b6" stroke-width="2.5" marker-end="url(#arrowData)"/>
  <!-- Name label -->
  <text x="0" y="44" text-anchor="middle" fill="#0077b6" font-size="22" font-weight="bold">SENSOR BOT A</text>
</g>
```

**2. Sterilize Bot (green #2dc653)** — in ICU, has UV-C arm:
```xml
<g transform="translate(570, 340)">
  <rect x="-26" y="-16" width="52" height="32" rx="10" fill="#1a3a1a" stroke="#2dc653" stroke-width="2.5"/>
  <!-- Eyes + pupils (same pattern as Sensor Bot, green instead of blue) -->
  <!-- Wheels -->
  <!-- UV-C arm: 2 line segments + joint circles + glowing tip -->
  <line x1="26" y1="-4" x2="56" y2="-22" stroke="#4a7a4a" stroke-width="5" stroke-linecap="round"/>
  <circle cx="56" cy="-22" r="4" fill="#3a6a3a"/>  <!-- elbow joint -->
  <line x1="56" y1="-22" x2="82" y2="-12" stroke="#4a7a4a" stroke-width="4" stroke-linecap="round"/>
  <circle cx="82" cy="-12" r="9" fill="#aa88ff" opacity="0.2"/>  <!-- UV glow outer -->
  <circle cx="82" cy="-12" r="4.5" fill="#aa88ff" opacity="0.4"/>  <!-- UV glow inner -->
  <text x="84" y="-28" fill="#8866cc" font-size="22" font-weight="bold">UV-C</text>
  <text x="0" y="40" text-anchor="middle" fill="#2dc653" font-size="22" font-weight="bold">STERILIZE BOT</text>
</g>
```

**3. Air Monitor (orange #e8960a)** — corridor near HVAC, has sensor array + air particles:
```xml
<g transform="translate(930, 535)">
  <rect x="-26" y="-16" width="52" height="32" rx="10" fill="#4a3a1a" stroke="#e8960a" stroke-width="2.5"/>
  <!-- Eyes + pupils (orange theme) -->
  <!-- Wheels -->
  <!-- Sensor array (small rect on top with 3 indicator circles) -->
  <rect x="-16" y="-28" width="32" height="10" rx="2" fill="#c87a08" stroke="#e8960a" stroke-width="1"/>
  <circle cx="-8" cy="-23" r="3" fill="#f4c430"/>
  <circle cx="0" cy="-23" r="3" fill="#f4c430"/>
  <circle cx="8" cy="-23" r="3" fill="#f4c430"/>
  <!-- Air particles (small circles floating nearby) -->
  <circle cx="35" cy="-14" r="2.5" fill="#e8960a" opacity="0.4"/>
  <circle cx="42" cy="-6" r="2" fill="#e8960a" opacity="0.35"/>
  <text x="0" y="42" text-anchor="middle" fill="#e8960a" font-size="22" font-weight="bold">AIR MONITOR</text>
</g>
```

**4. Spray Bot (blue #4a9eff)** — waiting area, has spray arm with mist:
```xml
<g transform="translate(1300, 780)">
  <rect x="-26" y="-16" width="52" height="32" rx="10" fill="#2a3a5a" stroke="#4a9eff" stroke-width="2.5"/>
  <!-- Eyes + wheels (blue theme) -->
  <!-- Spray arm (extends LEFT from body): 2 line segments + joint circles -->
  <line x1="-26" y1="-4" x2="-55" y2="-22" stroke="#5a6a8a" stroke-width="4" stroke-linecap="round"/>
  <circle cx="-55" cy="-22" r="4" fill="#4a5a7a"/>
  <line x1="-55" y1="-22" x2="-80" y2="-12" stroke="#5a6a8a" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="-80" cy="-12" r="4" fill="#2dc653"/>  <!-- nozzle -->
  <!-- Spray mist (small green circles scattered near nozzle) -->
  <circle cx="-88" cy="-20" r="2.5" fill="#2dc653" opacity="0.45"/>
  <circle cx="-95" cy="-14" r="2" fill="#3ae663" opacity="0.35"/>
  <circle cx="-84" cy="-28" r="2.8" fill="#2dc653" opacity="0.4"/>
  <text x="0" y="42" text-anchor="middle" fill="#4a9eff" font-size="22" font-weight="bold">SPRAY BOT</text>
</g>
```

#### Local AI Hub
Positioned below the floor plan (y≈975):
```xml
<g transform="translate(600, 975)">
  <!-- Dark housing -->
  <rect x="-70" y="-40" width="140" height="80" rx="10" fill="#0d2a4a" stroke="#4a9eff" stroke-width="3" filter="url(#shadow)"/>
  <rect x="-58" y="-30" width="116" height="60" rx="6" fill="#0a1628" stroke="#2a5a8a" stroke-width="1"/>
  <!-- AI face: 2 circle eyes with inner pupils + curved smile -->
  <circle cx="-20" cy="-10" r="8" fill="none" stroke="#00d4ff" stroke-width="1.8"/>
  <circle cx="20" cy="-10" r="8" fill="none" stroke="#00d4ff" stroke-width="1.8"/>
  <circle cx="-20" cy="-10" r="3" fill="#00d4ff"/>
  <circle cx="20" cy="-10" r="3" fill="#00d4ff"/>
  <path d="M-12,8 Q0,20 12,8" fill="none" stroke="#00d4ff" stroke-width="1.8"/>
  <!-- Status bars (green/orange/cyan) -->
  <rect x="-46" y="18" width="26" height="5" rx="2" fill="#2dc653" opacity="0.8"/>
  <rect x="-14" y="18" width="18" height="5" rx="2" fill="#f48c06" opacity="0.8"/>
  <rect x="10" y="18" width="34" height="5" rx="2" fill="#00d4ff" opacity="0.8"/>
  <text x="0" y="62" text-anchor="middle" fill="#4a9eff" font-size="24" font-weight="bold">LOCAL AI HUB</text>
  <text x="0" y="86" text-anchor="middle" fill="#6a8aaa" font-size="20">"Ward Sentinel"</text>
</g>
```

#### Communication Lines
Dashed lines from each robot to the AI Hub, plus an alert line (red) from Sensor Bot to the MRSA:
```xml
<!-- Robot → Hub data lines (blue dashed with arrow) -->
<line x1="260" y1="555" x2="550" y2="945" stroke="#3a7aba" stroke-width="2" stroke-dasharray="6,4" opacity="0.4" marker-end="url(#arrowData)"/>
<!-- One per robot... -->

<!-- Alert line: Sensor Bot → MRSA (red dashed with arrow) -->
<path d="M245,512 L325,335" fill="none" stroke="#cc3333" stroke-width="2.5" stroke-dasharray="5,3" opacity="0.6" marker-end="url(#arrowAlert)"/>
```

#### Uplink Badge
Small pill-shaped badge below the hub pointing to central AI:
```xml
<g transform="translate(600, 1080)">
  <rect x="-95" y="-18" width="190" height="36" rx="18" fill="#0d2a4a" stroke="#3a7aba" stroke-width="1.5"/>
  <!-- WiFi-like arcs -->
  <path d="M-45,8 Q-45,-8 -30,0" fill="none" stroke="#4a9eff" stroke-width="2"/>
  <path d="M-38,8 Q-38,-2 -28,3" fill="none" stroke="#4a9eff" stroke-width="2"/>
  <circle cx="-48" cy="8" r="3" fill="#4a9eff"/>
  <text x="15" y="7" text-anchor="middle" fill="#4a9eff" font-size="22" font-weight="bold">TO CENTRAL AI HUB</text>
</g>
<line x1="600" y1="1040" x2="600" y2="1062" stroke="#3a7aba" stroke-width="2.5" stroke-dasharray="5,3" opacity="0.5" marker-end="url(#arrowData)"/>
```

#### Dashboard Panel (Hospital — Blue Theme)
```xml
<g transform="translate(1560, 105)">
  <!-- Panel background -->
  <rect x="0" y="0" width="800" height="1000" rx="8" fill="#f0f4f8" stroke="#c0c8d0" stroke-width="1.5" filter="url(#shadow)"/>

  <!-- Dark header -->
  <rect x="0" y="0" width="800" height="65" rx="8" fill="#0d2a4a"/>
  <rect x="0" y="30" width="800" height="35" fill="#0d2a4a"/>  <!-- cover bottom radius -->
  <text x="400" y="46" text-anchor="middle" fill="#4ac0ff" font-size="34" font-weight="bold">WARD SENTINEL DASHBOARD</text>

  <!-- Health Score (SVG arc circle) -->
  <g transform="translate(400, 140)">
    <circle cx="0" cy="0" r="52" fill="none" stroke="#e0e4e8" stroke-width="8"/>  <!-- background ring -->
    <circle cx="0" cy="0" r="52" fill="none" stroke="#2dc653" stroke-width="8"
            stroke-dasharray="244 326" stroke-dashoffset="-82" stroke-linecap="round"/>
    <!-- dasharray = (score/100) * circumference, remaining -->
    <!-- circumference = 2*pi*52 ≈ 326.7; for score 74: 74% of 326 ≈ 241 -->
    <text x="0" y="-4" text-anchor="middle" fill="#2a4a2a" font-size="50" font-weight="bold">74</text>
    <text x="0" y="22" text-anchor="middle" fill="#5a7a5a" font-size="22">/100</text>
    <text x="0" y="68" text-anchor="middle" fill="#4a6a4a" font-size="24" font-weight="bold">MICROBIOME HEALTH</text>
  </g>

  <!-- Alert box -->
  <rect x="25" y="230" width="750" height="110" rx="6" fill="#fff0f0" stroke="#dd6666" stroke-width="1.5"/>
  <circle cx="60" cy="262" r="18" fill="#dd4444"/>
  <text x="60" y="270" text-anchor="middle" fill="white" font-size="26" font-weight="bold">!</text>
  <text x="90" y="268" fill="#aa3333" font-size="26" font-weight="bold">ACTIVE ALERT</text>
  <text x="38" y="300" fill="#884444" font-size="22">MRSA on door handle, Rm 201. Sensor Bot responding.</text>
  <text x="38" y="326" fill="#cc5555" font-size="20" font-style="italic">Sterilize Bot dispatched to ICU Bay A</text>

  <!-- Room Status list (colored dot + room name + status text) -->
  <text x="25" y="378" fill="#3a4a5a" font-size="28" font-weight="bold">Room Status</text>
  <line x1="25" y1="390" x2="775" y2="390" stroke="#c0c8d0" stroke-width="0.8"/>
  <!-- Each row: circle r=9 at cx=50, room name at x=72, status text at x=250, spaced 42px apart -->
  <circle cx="50" cy="422" r="9" fill="#dd4444"/>
  <text x="72" y="430" fill="#4a5a6a" font-size="24" font-weight="bold">Rm 201</text>
  <text x="250" y="430" fill="#aa3333" font-size="24">MRSA — intervention active</text>
  <!-- ...repeat for each room, incrementing cy by 42... -->

  <!-- Robot Fleet Status (progress bar rows) -->
  <text x="25" y="738" fill="#3a4a5a" font-size="28" font-weight="bold">Robot Fleet Status</text>
  <!-- Each bot: colored bg rect (750x50), color square, name, task text, progress bar, percentage -->
  <rect x="25" y="755" width="750" height="50" rx="5" fill="#e8f0f8" stroke="#c0d0e0" stroke-width="0.5"/>
  <rect x="35" y="764" width="18" height="18" rx="5" fill="#0077b6"/>  <!-- color indicator -->
  <text x="65" y="782" fill="#0077b6" font-size="22" font-weight="bold">SENSOR BOT A</text>
  <text x="370" y="782" fill="#4a6a8a" font-size="20">Scanning Rm 201</text>
  <!-- Progress bar: gray track + colored fill -->
  <rect x="35" y="792" width="260" height="7" rx="3" fill="#e0e0e0"/>
  <rect x="35" y="792" width="213" height="7" rx="3" fill="#0077b6"/>  <!-- 82% of 260 -->
  <text x="700" y="798" fill="#5a7a9a" font-size="20">82%</text>
  <!-- ...repeat for each bot, incrementing y by 60... -->
</g>
```

#### Caption & Legend
```xml
<!-- Caption box below floor plan -->
<rect x="50" y="1150" width="1460" height="115" rx="6" fill="#f0f2f5" stroke="#c0c8d0" stroke-width="1"/>
<text x="780" y="1188" text-anchor="middle" fill="#3a4a5a" font-size="26" font-weight="bold">
  Figure 3.  Hospital Microbiome Sentinel Network — Ward-Level Autonomous Operations
</text>
<text x="780" y="1220" text-anchor="middle" fill="#6a7a8a" font-size="22">
  Four robot agents patrol a hospital ward...
</text>

<!-- Legend: 2 side-by-side boxes -->
<g transform="translate(50, 1295)">
  <rect x="0" y="0" width="710" height="110" rx="5" fill="#f8f8fc" stroke="#ccc" stroke-width="0.8"/>
  <text x="20" y="30" fill="#3a4a5a" font-size="24" font-weight="bold">ROBOT AGENT TYPES</text>
  <circle cx="35" cy="58" r="8" fill="#0077b6"/>
  <text x="55" y="65" fill="#555" font-size="22">Sensor / Patrol Bot — environmental scanning</text>
  <!-- more entries... -->
</g>
<g transform="translate(780, 1295)">
  <rect x="0" y="0" width="710" height="110" rx="5" fill="#f8f8fc" stroke="#ccc" stroke-width="0.8"/>
  <text x="20" y="30" fill="#3a4a5a" font-size="24" font-weight="bold">STATUS INDICATORS</text>
  <!-- Green/orange/red indicators with descriptions... -->
</g>
```

---

### Figure 3B: Residential Basement (figure3B_residential_basement.html)

**Source**: `figure3B_residential_basement.html` → rendered to `figure3B_residential_basement.png`
**Theme**: Green — header gradient `#3a4a2a → #5a7a3a`, page background `#f8faf6`

#### Defs — Floor Patterns (Basement-specific)
```xml
<!-- Concrete floor -->
<pattern id="concreteFloor" width="20" height="20" patternUnits="userSpaceOnUse">
  <rect width="20" height="20" fill="#d4d4d8"/>
  <rect width="10" height="10" fill="#ccccd0" x="2" y="2"/>
  <rect width="6" height="6" fill="#d8d8dc" x="11" y="12"/>
</pattern>
<!-- Cinder block wall texture -->
<pattern id="cinderBlock" width="40" height="20" patternUnits="userSpaceOnUse">
  <rect width="40" height="20" fill="#b0b0b8"/>
  <rect x="1" y="1" width="38" height="8" rx="1" fill="#bbbbc0" stroke="#a0a0a8" stroke-width="0.5"/>
  <rect x="1" y="11" width="18" height="8" rx="1" fill="#bbbbc0" stroke="#a0a0a8" stroke-width="0.5"/>
  <rect x="21" y="11" width="18" height="8" rx="1" fill="#bbbbc0" stroke="#a0a0a8" stroke-width="0.5"/>
</pattern>
```

#### Building Shell (no corridor — open basement layout)
```xml
<!-- Concrete floor slab -->
<rect x="50" y="105" width="1460" height="940" rx="4" fill="url(#concreteFloor)" stroke="#7a7a80" stroke-width="3" filter="url(#shadow)"/>
<!-- Thick foundation walls (20px stroke simulates masonry) -->
<rect x="50" y="105" width="1460" height="940" rx="4" fill="none" stroke="#8a8a90" stroke-width="20"/>
<!-- Inner wall texture accent line -->
<rect x="60" y="115" width="1440" height="920" rx="2" fill="none" stroke="#a0a0a8" stroke-width="1" stroke-dasharray="2,2"/>
```

#### Ceiling Joists & Pipes (background details)
```xml
<!-- Horizontal wood joists (faint) -->
<g opacity="0.15" stroke="#6a5a40" stroke-width="3">
  <line x1="60" y1="160" x2="1500" y2="160"/>
  <!-- repeat every ~110px -->
</g>
<!-- Overhead pipes -->
<g stroke="#888890" stroke-width="5" opacity="0.25">
  <line x1="70" y1="200" x2="1500" y2="200"/>  <!-- horizontal -->
  <line x1="400" y1="120" x2="400" y2="1040"/>  <!-- vertical -->
</g>
```

#### Zone Layout (4 zones, divided by dashed lines)
No corridor — the basement is divided into 4 quadrants with dashed zone dividers:
```xml
<line x1="760" y1="115" x2="760" y2="1035" stroke="#9a9aa0" stroke-width="1.5" stroke-dasharray="8,5" opacity="0.4"/>
<line x1="60" y1="575" x2="1500" y2="575" stroke="#9a9aa0" stroke-width="1.5" stroke-dasharray="8,5" opacity="0.4"/>
```

| Zone | translate | size | header color | header text |
|------|-----------|------|-------------|------------|
| A: Laundry Area | (100, 130) | 620x420 | `#d8e0e8` | `#4a5a6a` |
| B: HVAC / Furnace | (800, 130) | 640x420 | `#e8dcd0` | `#6a5a4a` |
| C: Storage / Workshop | (100, 600) | 620x415 | `#e0d8c8` | `#6a5a3a` |
| D: Entry / Stairwell | (800, 600) | 640x415 | `#d8dce0` | `#4a5a6a` |

#### Drawing Basement Equipment

**Washer (front-load, with drum circle):**
```xml
<rect x="30" y="70" width="120" height="130" rx="8" fill="#e8e8e8" stroke="#bbb" stroke-width="2"/>
<circle cx="90" cy="130" r="35" fill="none" stroke="#999" stroke-width="2"/>  <!-- drum door -->
<circle cx="90" cy="130" r="25" fill="#c8dae8" stroke="#aabbc8" stroke-width="1" opacity="0.5"/>  <!-- water -->
<text x="90" y="225" text-anchor="middle" fill="#5a6a7a" font-size="22">Washer</text>
```

**Dryer:**
```xml
<rect x="170" y="70" width="120" height="130" rx="8" fill="#e8e8e8" stroke="#bbb" stroke-width="2"/>
<rect x="195" y="95" width="70" height="70" rx="4" fill="#ddd" stroke="#bbb" stroke-width="1"/>  <!-- door window -->
<text x="230" y="225" text-anchor="middle" fill="#5a6a7a" font-size="22">Dryer</text>
```

**Utility Sink (with faucet):**
```xml
<rect x="340" y="80" width="100" height="80" rx="4" fill="#e0e4e8" stroke="#a0aab0" stroke-width="2"/>
<rect x="355" y="92" width="70" height="50" rx="3" fill="#c8d8e4" stroke="#8a9aa8" stroke-width="1"/>  <!-- basin -->
<line x1="390" y1="80" x2="390" y2="65" stroke="#888" stroke-width="3" stroke-linecap="round"/>  <!-- faucet pipe -->
<circle cx="390" cy="62" r="5" fill="#999"/>  <!-- faucet knob -->
```

**Furnace (large labeled box + return air filter):**
```xml
<rect x="40" y="75" width="160" height="200" rx="6" fill="#b8b8b8" stroke="#8a8a8a" stroke-width="2"/>
<rect x="55" y="90" width="130" height="80" rx="4" fill="#a0a0a0" stroke="#888" stroke-width="1"/>
<text x="120" y="142" text-anchor="middle" fill="#555" font-size="28" font-weight="bold">FURNACE</text>
<!-- Return Air Filter below -->
<rect x="60" y="280" width="140" height="32" rx="4" fill="#d0d4d8" stroke="#a8acb0" stroke-width="1"/>
<text x="130" y="302" text-anchor="middle" fill="#5a6a5a" font-size="20">Return Air Filter</text>
```

**Water Heater (cylindrical, shown as ellipse top-down):**
```xml
<ellipse cx="370" cy="170" rx="55" ry="55" fill="#e4e4e4" stroke="#bbb" stroke-width="2"/>
<ellipse cx="370" cy="170" rx="42" ry="42" fill="#eee" stroke="#ccc" stroke-width="1"/>
<text x="370" y="160" text-anchor="middle" fill="#555" font-size="22" font-weight="bold">WATER</text>
<text x="370" y="184" text-anchor="middle" fill="#555" font-size="22" font-weight="bold">HEATER</text>
<!-- Hot/cold pipes coming up -->
<line x1="355" y1="115" x2="355" y2="80" stroke="#888" stroke-width="4"/>
<line x1="385" y1="115" x2="385" y2="80" stroke="#888" stroke-width="4"/>
```

**Electrical Panel:**
```xml
<rect x="530" y="80" width="80" height="120" rx="4" fill="#a0a0a0" stroke="#777" stroke-width="2"/>
<rect x="540" y="95" width="60" height="35" rx="2" fill="#888" stroke="#666" stroke-width="1"/>  <!-- top breakers -->
<rect x="540" y="140" width="60" height="35" rx="2" fill="#888" stroke="#666" stroke-width="1"/>  <!-- bottom breakers -->
```

**Shelving with items (Storage zone):**
```xml
<!-- 4 horizontal shelf boards -->
<rect x="30" y="65" width="200" height="22" rx="2" fill="#b8a888" stroke="#9a8a70" stroke-width="1"/>
<!-- repeat at y=100, y=135, y=170 -->
<!-- Vertical uprights -->
<rect x="30" y="65" width="5" height="130" fill="#8a7a60"/>
<rect x="125" y="65" width="5" height="130" fill="#8a7a60"/>
<rect x="225" y="65" width="5" height="130" fill="#8a7a60"/>
<!-- Small items on shelves (colored rects) -->
<rect x="45" y="53" width="30" height="15" rx="2" fill="#c8b898"/>
```

**Workbench (with legs):**
```xml
<rect x="290" y="80" width="200" height="60" rx="3" fill="#b0a088" stroke="#9a8a70" stroke-width="1.5"/>
<rect x="295" y="140" width="15" height="70" fill="#9a8a70"/>  <!-- left leg -->
<rect x="470" y="140" width="15" height="70" fill="#9a8a70"/>  <!-- right leg -->
```

**Sump Pit (with water):**
```xml
<rect x="500" y="260" width="90" height="90" rx="6" fill="#8a9aa8" stroke="#6a7a88" stroke-width="2"/>
<rect x="512" y="272" width="66" height="66" rx="4" fill="#5a6a78" stroke="#4a5a68" stroke-width="1"/>
<circle cx="545" cy="305" r="12" fill="#4a6a88" opacity="0.5"/>  <!-- water surface -->
<!-- Moisture halo around sump -->
<ellipse cx="545" cy="305" rx="65" ry="55" fill="#6688aa" opacity="0.08"/>
```

**Staircase (series of step rects):**
```xml
<g transform="translate(400, 80)">
  <rect x="0" y="0" width="180" height="300" rx="4" fill="#c8c0b0" stroke="#a8a098" stroke-width="1.5"/>
  <!-- 8 steps, each 160x28, spaced 35px apart -->
  <rect x="10" y="10" width="160" height="28" rx="2" fill="#b8b0a0" stroke="#a09888" stroke-width="0.8"/>
  <rect x="10" y="45" width="160" height="28" rx="2" fill="#b8b0a0" stroke="#a09888" stroke-width="0.8"/>
  <!-- ...continue at y=80, 115, 150, 185, 220, 255... -->
  <text x="90" y="-10" text-anchor="middle" fill="#6a6a6a" font-size="22" font-style="italic">to ground floor</text>
</g>
```

**Charging Dock (dark with LED indicators):**
```xml
<rect x="40" y="120" width="110" height="65" rx="6" fill="#1a1a22" stroke="#4a9eff" stroke-width="2"/>
<rect x="55" y="132" width="80" height="20" rx="3" fill="#0a1628" stroke="#2a5a8a" stroke-width="1"/>
<circle cx="75" cy="142" r="5" fill="#2dc653"/>  <!-- LED 1 -->
<circle cx="95" cy="142" r="5" fill="#2dc653"/>  <!-- LED 2 -->
<circle cx="115" cy="142" r="5" fill="#4a9eff"/>  <!-- LED 3 -->
<rect x="70" y="160" width="50" height="12" rx="2" fill="#0a2a1a" stroke="#2dc653" stroke-width="0.8"/>
<text x="95" y="210" text-anchor="middle" fill="#4a9eff" font-size="22" font-weight="bold">Charging Dock</text>
```

**Home Hub / Router:**
```xml
<rect x="40" y="280" width="100" height="60" rx="5" fill="#2a2a34" stroke="#4a6a8a" stroke-width="1.5"/>
<rect x="52" y="292" width="76" height="30" rx="3" fill="#1a1a2a" stroke="#3a5a7a" stroke-width="0.8"/>
<circle cx="70" cy="307" r="4" fill="#00d4ff" opacity="0.8"/>
<circle cx="90" cy="307" r="4" fill="#2dc653" opacity="0.8"/>
<circle cx="110" cy="307" r="4" fill="#2dc653" opacity="0.8"/>
<text x="90" y="360" text-anchor="middle" fill="#4a6a8a" font-size="22">Home Hub</text>
```

#### Moisture Indicators
Soft elliptical halos — used near sinks, water heater, sump pit:
```xml
<ellipse cx="430" cy="300" rx="60" ry="45" fill="#6688aa" opacity="0.1"/>
<ellipse cx="430" cy="300" rx="35" ry="28" fill="#6688aa" opacity="0.15"/>
<text x="430" y="360" text-anchor="middle" fill="#6688aa" font-size="20" font-style="italic">moisture</text>
```

#### Mold Colonies (green concentric circles + spores)
**Large colony (primary):**
```xml
<g transform="translate(180, 870)">
  <circle cx="0" cy="0" r="35" fill="#2a6a1a" opacity="0.12"/>
  <circle cx="0" cy="0" r="22" fill="#2a6a1a" opacity="0.2"/>
  <circle cx="0" cy="0" r="12" fill="#3a8a2a" opacity="0.35"/>
  <!-- Additional satellite circles for organic shape -->
  <circle cx="15" cy="-12" r="8" fill="#2a7a1a" opacity="0.3"/>
  <circle cx="-10" cy="14" r="10" fill="#1a5a0e" opacity="0.28"/>
  <circle cx="22" cy="8" r="6" fill="#4a9a38" opacity="0.25"/>
  <!-- Spore dots (tiny, scattered) -->
  <circle cx="30" cy="-25" r="2" fill="#5aaa48" opacity="0.4"/>
  <circle cx="-22" cy="-18" r="2.5" fill="#5aaa48" opacity="0.35"/>
  <text x="0" y="52" text-anchor="middle" fill="#3a7a2a" font-size="24" font-weight="bold">MOLD</text>
  <text x="0" y="75" text-anchor="middle" fill="#3a7a2a" font-size="20">Aspergillus</text>
</g>
```

**Small/early colony:**
```xml
<g transform="translate(1250, 430)">
  <circle cx="0" cy="0" r="25" fill="#2a6a1a" opacity="0.1"/>
  <circle cx="0" cy="0" r="14" fill="#2a6a1a" opacity="0.18"/>
  <circle cx="0" cy="0" r="7" fill="#3a8a2a" opacity="0.3"/>
  <text x="0" y="40" text-anchor="middle" fill="#5a8a3a" font-size="20" font-weight="bold">early mold</text>
</g>
```

#### Basement Robots (2 types, use scale(1.35))

**1. Patrol Bot (blue #0077b6)** — sensing arm + scan lines:
```xml
<g transform="translate(550, 810) scale(1.35)">
  <!-- Same body/eyes/wheels/antenna pattern as hospital Sensor Bot -->
  <!-- Sensing arm (extends RIGHT): 2 segments + joint + glowing tip -->
  <line x1="28" y1="-4" x2="58" y2="-22" stroke="#5a6a8a" stroke-width="4" stroke-linecap="round"/>
  <circle cx="58" cy="-22" r="4" fill="#4a5a7a"/>
  <line x1="58" y1="-22" x2="82" y2="-10" stroke="#5a6a8a" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="82" cy="-10" r="6" fill="#0099ff" opacity="0.5"/>
  <circle cx="82" cy="-10" r="3" fill="#0099ff" opacity="0.8"/>
  <text x="85" y="-22" fill="#0077b6" font-size="20">Sensor</text>
  <!-- Scan lines (pointing toward mold area) -->
  <line x1="0" y1="-4" x2="-85" y2="-45" stroke="#0077b6" stroke-width="1.2" stroke-dasharray="6,3" opacity="0.5"/>
  <!-- Movement arrow -->
  <path d="M35,8 L90,8" fill="none" stroke="#0077b6" stroke-width="2.5" marker-end="url(#arrowData)"/>
  <text x="0" y="46" text-anchor="middle" fill="#0077b6" font-size="22" font-weight="bold">PATROL BOT</text>
  <text x="0" y="68" text-anchor="middle" fill="#4a7a9a" font-size="18">VOC + spore detection</text>
</g>
```

**2. Spray Bot (green #2dc653)** — spray arm with mist toward mold:
```xml
<g transform="translate(320, 810) scale(1.35)">
  <!-- Same body pattern but green theme: fill="#1a3a1a" stroke="#2dc653" -->
  <!-- Spray arm (extends LEFT): same arm pattern as hospital Spray Bot -->
  <!-- Spray mist (5 small green circles near nozzle) -->
  <text x="0" y="42" text-anchor="middle" fill="#2dc653" font-size="22" font-weight="bold">SPRAY BOT</text>
  <text x="0" y="64" text-anchor="middle" fill="#4a8a4a" font-size="18">antifungal treatment</text>
</g>
```

#### Basement AI Hub (green theme)
Same structure as hospital hub but green colors:
```xml
<g transform="translate(780, 1075)">
  <rect x="-70" y="-40" width="140" height="80" rx="10" fill="#1a2a1a" stroke="#4a9e4a" stroke-width="3" filter="url(#shadow)"/>
  <rect x="-58" y="-30" width="116" height="60" rx="6" fill="#0a1a0a" stroke="#2a5a2a" stroke-width="1"/>
  <!-- AI face: same pattern, green #44dd66 instead of cyan -->
  <!-- Status bars -->
  <text x="0" y="62" text-anchor="middle" fill="#4a9e4a" font-size="24" font-weight="bold">LOCAL AI HUB</text>
  <text x="0" y="86" text-anchor="middle" fill="#6a8a6a" font-size="20">"Basement Guardian"</text>
</g>
```

#### Basement Dashboard (Green Theme)
Same structure as hospital dashboard with these differences:
- Panel fill: `#f4f8f4`, stroke: `#b8c8b8`
- Header fill: `#1a3a1a`, text color: `#66dd88`
- Title: "BASEMENT GUARDIAN DASHBOARD"
- Health score: 61/100 (orange arc `#f4a020` instead of green)
- Alert: "Aspergillus colony on foundation wall" (orange `#dd8844` alert icon, softer warning)
- **Zone Status** (not "Room Status"): Laundry, HVAC/Furnace, Storage, Entry, Sump Pit, Foundation
- **Robot Fleet**: 2 bots (Patrol Bot 75%, Spray Bot 45%)
- **Environmental Readings** section (unique to basement): Temperature, Humidity, VOC Level, Spore Count
```xml
<!-- Environmental readings (below robot fleet) -->
<line x1="25" y1="840" x2="775" y2="840" stroke="#c0c8c0" stroke-width="0.8"/>
<text x="25" y="872" fill="#3a4a3a" font-size="28" font-weight="bold">Environmental Readings</text>
<!-- 2x2 grid of readings -->
<text x="40" y="906" fill="#4a5a4a" font-size="22">Temperature</text>
<text x="300" y="906" fill="#3a6a3a" font-size="22" font-weight="bold">68 F</text>
<text x="420" y="906" fill="#4a5a4a" font-size="22">Humidity</text>
<text x="620" y="906" fill="#aa6a20" font-size="22" font-weight="bold">67% RH</text>
<text x="40" y="936" fill="#4a5a4a" font-size="22">VOC Level</text>
<text x="300" y="936" fill="#3a6a3a" font-size="22" font-weight="bold">0.18 ppm</text>
<text x="420" y="936" fill="#4a5a4a" font-size="22">Spore Count</text>
<text x="620" y="936" fill="#aa3333" font-size="22" font-weight="bold">1,240 /m3</text>
```

#### Basement Caption & Legend
Same pattern as hospital but green theme (`#f2f4f0`, `#b8c0b8`). Legend includes "Mold colony (Aspergillus)" entry with green dot `#3a8a2a`.

---

## Rendering SVG to PNG

**Requires**: Node.js + `sharp` (`npm install sharp` in the figures directory)

### Render Script Pattern
```js
// render_svg.js (or render_3B.js, etc.)
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const htmlFile = path.join(__dirname, 'YOUR_FILE.html');
const outputFile = path.join(__dirname, 'YOUR_FILE.png');

const html = fs.readFileSync(htmlFile, 'utf8');
const svgMatch = html.match(/<svg[\s\S]*<\/svg>/);
if (!svgMatch) { console.error('No SVG found'); process.exit(1); }

let svg = svgMatch[0];
// Ensure width/height for sharp
if (!svg.includes('width=') || !svg.includes('height=')) {
  svg = svg.replace(/viewBox="0 0 (\d+) (\d+)"/, 'width="$1" height="$2" viewBox="0 0 $1 $2"');
}

sharp(Buffer.from(svg), { density: 150 })
  .png()
  .toFile(outputFile)
  .then(info => console.log('PNG created:', info))
  .catch(err => console.error('Error:', err));
```

Run: `node render_svg.js`

Output is ~5000x2979 pixels at density 150 for a 2400x1430 viewBox.

**Note**: Chrome headless screenshots were tried but had quality issues. `sharp` is the reliable method.

---

## User Preferences (Critical)

- Labels WITHOUT numbers — text-only with colored border accent
- Labels should be spread out to avoid overlap
- Labels in room scenes should be INSIDE the room, not floating outside
- Mold should be very prominent (large, bright, emissive materials)
- Robots should have personality (eyebrows, face plates, antenna)
- Bots should be animated/moving on patrol paths, not static
- Fonts in SVG figures must be LARGE (minimum 20pt body, 26pt headers)
- When creating new versions, preserve originals in `keep/` directory
- Bot-attached labels should follow the bot (parent CSS2DObject to the bot group)
- Do NOT use invisible hitbox meshes for hover detection — they break raycasting
