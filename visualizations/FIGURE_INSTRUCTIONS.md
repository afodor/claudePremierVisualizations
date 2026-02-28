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

### SVG Structure
```html
<svg viewBox="0 0 2400 1430" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI, ...">
  <defs>
    <!-- linearGradient for header bar -->
    <!-- filter for drop shadow -->
    <!-- patterns for floor tiles -->
    <!-- marker for arrow heads -->
  </defs>
  <rect width="2400" height="1430" fill="#f8fafc"/>  <!-- background -->
  <rect ... fill="url(#headerBar)"/>                   <!-- title bar, h=85 -->
  <text ... font-size="46" font-weight="bold">Title</text>

  <!-- Floor plan: x=50, y=105, w=1460, h=~940-1000 -->
  <!-- Dashboard panel: x=1560, y=105, w=800, h=~940 -->
  <!-- Caption: below floor plan -->
  <!-- Legend: bottom -->
</svg>
```

### Layout Grid
- **Total**: 2400 x 1430
- **Header bar**: full width, height 85px
- **Floor plan area**: x=50, y=105, width=1460
- **Dashboard panel**: x=1560, y=105, width=800
- **Caption**: x=50, y=~1200, height=~100
- **Legend**: x=50, y=~1320, two boxes side by side (710px each)

### Color Themes
- **Hospital (figure3)**: Blue header gradient (#1a4a6a → #2a7aaa), blue accents
- **Basement (figure3B)**: Green header gradient (#3a4a2a → #5a7a3a), green accents

### Room/Zone Pattern
```xml
<g transform="translate(X, Y)">
  <rect ... fill="url(#tileFloor)" stroke="#a0aab4"/>  <!-- room bg -->
  <rect ... fill="#c8d8e8"/>                              <!-- header strip -->
  <text ... font-size="26" font-weight="bold">ROOM NAME</text>
  <!-- furniture, equipment inside -->
</g>
```

### Robot Agent Drawing
```xml
<g transform="translate(X, Y) scale(1.35)">
  <!-- Body: rounded rect -->
  <rect x="-28" y="-18" width="56" height="36" rx="12" fill="#2a3a5a" stroke="#0077b6" stroke-width="2.5"/>
  <!-- Eyes: 2 circles with pupils -->
  <circle cx="-10" cy="-4" r="6" fill="#0077b6"/>
  <circle cx="10" cy="-4" r="6" fill="#0077b6"/>
  <!-- Wheels: 2 small rects -->
  <!-- Antenna: line + circle -->
  <!-- Arms (optional): lines + circles for joints -->
  <!-- Scan lines (optional): dashed lines from eyes -->
  <!-- Label below -->
  <text ... font-size="22" font-weight="bold">BOT NAME</text>
</g>
```
Use `scale(1.35)` on the group transform for larger bots.

### Dashboard Panel
```xml
<g transform="translate(1560, 105)">
  <rect ... fill="#f0f4f8" stroke="#c0c8d0" filter="url(#shadow)"/>
  <!-- Header bar (dark) -->
  <!-- Health score circle (SVG arc via stroke-dasharray) -->
  <!-- Alert box -->
  <!-- Room/Zone status list (colored dots + text) -->
  <!-- Robot fleet status (progress bars) -->
  <!-- Environmental readings (if applicable) -->
</g>
```

### Status Indicators
- Green `#2dc653` = healthy/nominal
- Orange `#f4a020` = caution/elevated
- Red `#dd4444` = alert/pathogen detected

### Font Sizes (IMPORTANT)
Use LARGE fonts — minimum 20pt for body text, 22-26pt for labels, 28-34pt for section headers, 46pt for main title. The user found 6-10pt unreadable.

### Communication Lines
```xml
<!-- Dashed data lines from robots to AI Hub -->
<line x1="..." y1="..." x2="..." y2="..." stroke="#3a7aba" stroke-width="2"
      stroke-dasharray="6,4" opacity="0.4" marker-end="url(#arrowData)"/>
<!-- Alert lines (red) -->
<path d="M... L..." stroke="#cc3333" stroke-width="2.5" stroke-dasharray="5,3"
      opacity="0.6" marker-end="url(#arrowAlert)"/>
```

### Mold/Pathogen Hotspots
```xml
<g transform="translate(X, Y)">
  <!-- Concentric circles with decreasing opacity -->
  <circle r="35" fill="#2a6a1a" opacity="0.12"/>
  <circle r="22" fill="#2a6a1a" opacity="0.2"/>
  <circle r="12" fill="#3a8a2a" opacity="0.35"/>
  <!-- Scattered spore dots -->
  <text ... font-size="24" font-weight="bold">MOLD</text>
  <text ... font-size="20">Aspergillus</text>
</g>
```

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
