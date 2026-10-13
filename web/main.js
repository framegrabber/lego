// LEGO model preview and step player.
//
// Query parameters:
//   model=<url>    LDraw file to show (required)
//   step=<n>       1-based building step to show (default: last)
//   view=<name>    front | side | top | iso — fixed camera, no UI (used by `lego render`)
//
// For headless rendering the page sets `window.legoReady = true` once the frame is drawn,
// or `window.legoError = "<message>"` if loading failed.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LDrawLoader } from 'three/addons/loaders/LDrawLoader.js';
import { LDrawConditionalLineMaterial } from 'three/addons/materials/LDrawConditionalLineMaterial.js';

const LDRAW_LIBRARY = '/ldraw/';
// Camera directions in three.js space (the model is flipped so +Y is up; LDraw's front faces +Z).
const VIEWS = {
  front: [0, 0, 1],
  side: [1, 0, 0],
  top: [0, 1, 0.0001],
  iso: [1, 0.8, 1],
};

const params = new URLSearchParams(location.search);
const modelUrl = params.get('model');
const viewName = params.get('view');
const headless = viewName !== null;
document.body.classList.toggle('headless', headless);

const statusEl = document.getElementById('status');

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('viewport').appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf4f4f4);
scene.add(new THREE.HemisphereLight(0xffffff, 0xaaaaaa, 2.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.8);
sun.position.set(1, 2, 1.5);
scene.add(sun);

const perspective = new THREE.PerspectiveCamera(35, window.innerWidth / window.innerHeight, 1, 100000);
// Straight views (front/side/top) in renders are orthographic so lengths and alignments read true.
const orthographic = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 100000);
let camera = perspective;
const controls = new OrbitControls(perspective, renderer.domElement);
controls.enableDamping = true;

function render() {
  renderer.render(scene, camera);
}

function frameModel(model, direction) {
  const sphere = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere());
  const dir = new THREE.Vector3(...direction).normalize();
  if (camera === orthographic) {
    const aspect = window.innerWidth / window.innerHeight;
    const half = sphere.radius * 1.05;
    Object.assign(orthographic, {
      left: -half * Math.max(aspect, 1),
      right: half * Math.max(aspect, 1),
      top: half / Math.min(aspect, 1),
      bottom: -half / Math.min(aspect, 1),
      near: sphere.radius / 100,
      far: sphere.radius * 10,
    });
    orthographic.position.copy(sphere.center).addScaledVector(dir, sphere.radius * 3);
    orthographic.lookAt(sphere.center);
    orthographic.updateProjectionMatrix();
    return;
  }
  const fov = THREE.MathUtils.degToRad(perspective.fov);
  const halfAngle = Math.min(fov, 2 * Math.atan(Math.tan(fov / 2) * perspective.aspect)) / 2;
  const distance = (sphere.radius / Math.sin(halfAngle)) * 1.05;
  perspective.position.copy(sphere.center).addScaledVector(dir, distance);
  perspective.near = distance / 100;
  perspective.far = distance * 100;
  perspective.updateProjectionMatrix();
  controls.target.copy(sphere.center);
  controls.update();
}

// Children of a group, each tagged with its step number: LDrawLoader flags the first object after
// every `0 STEP` line with userData.startingBuildingStep.
function numberSteps(group) {
  let step = 0;
  return group.children.map((child) => {
    if (child.userData.startingBuildingStep) step++;
    return { object: child, step };
  });
}

// Sub-assemblies are submodels (.ldr); library parts are .dat files.
const isSubassembly = (object) => object.name.toLowerCase().endsWith('.ldr');

function subassemblyName(object) {
  const stem = object.name.replace(/\.ldr$/i, '');
  return stem.slice(stem.indexOf('__') + 2).replace(/_/g, ' ');
}

// The instruction sequence: before each main step, the steps of every sub-assembly it attaches
// (shown on their own, once per kind with a "2×" count for copies), then the main step itself.
function buildSequence(model) {
  const top = numberSteps(model);
  const mainSteps = Math.max(0, ...top.map((t) => t.step)) + 1;
  const sequence = [];
  for (let s = 0; s < mainSteps; s++) {
    const kinds = new Map(); // submodel file -> first copy and number of copies in this step
    for (const t of top) {
      if (t.step !== s || !isSubassembly(t.object)) continue;
      const kind = kinds.get(t.object.name);
      if (kind) kind.copies++;
      else kinds.set(t.object.name, { object: t.object, copies: 1 });
    }
    for (const { object, copies } of kinds.values()) {
      const inner = numberSteps(object);
      const count = Math.max(0, ...inner.map((i) => i.step)) + 1;
      for (let k = 0; k < count; k++) {
        sequence.push({ sub: object, inner, upto: k, count, copies, name: subassemblyName(object) });
      }
    }
    sequence.push({ sub: null, upto: s });
  }
  return { top, sequence };
}

// Instruction data written by `lego build` next to the model: parts per step, weak points.
async function loadInstructions(url) {
  try {
    const response = await fetch(url.replace(/\.(mpd|ldr)$/i, '.json'), { cache: 'no-store' });
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

function stepInfo(info, entry) {
  if (!info) return null;
  return (entry.sub ? info.subs?.[entry.sub.name] : info.main)?.[entry.upto] ?? null;
}

const FADED_OPACITY = 0.3;

// look: 'normal' | 'faded' (built in earlier steps)
function setLook(object, look) {
  object.traverse((child) => {
    if (!child.isMesh && !child.isLine) return;
    if (!child.userData.ownMaterial) {
      // Materials are shared between parts of one color; give each object its own copy and
      // remember its own transparency (see-through bricks).
      child.material = [child.material].flat().map((m) => {
        const own = m.clone();
        own.userData.base = { opacity: m.opacity, transparent: m.transparent, depthWrite: m.depthWrite };
        return own;
      });
      if (child.material.length === 1) child.material = child.material[0];
      child.userData.ownMaterial = true;
    }
    for (const m of [child.material].flat()) {
      const base = m.userData.base;
      const faded = look === 'faded';
      m.transparent = faded || base.transparent;
      m.opacity = faded ? base.opacity * FADED_OPACITY : base.opacity;
      m.depthWrite = faded ? false : base.depthWrite;
    }
  });
}

// Magenta outline around the weakest joint of a step: a colour no brick has.
const weakMarker = new THREE.BoxHelper(undefined, 0xff00ff);
weakMarker.material.depthTest = false;
weakMarker.renderOrder = 10;

function resolvePath(top, path) {
  const object = top[path[0]]?.object;
  return path.length === 1 ? object : object?.children[path[1]];
}

// Show one instruction step; returns true if a weak part is marked.
function showEntry(top, entry, isLast, info) {
  scene.remove(weakMarker);
  if (entry.sub) {
    for (const t of top) t.object.visible = t.object === entry.sub;
    for (const i of entry.inner) {
      i.object.visible = i.step <= entry.upto;
      if (i.object.visible) setLook(i.object, isLast || i.step === entry.upto ? 'normal' : 'faded');
    }
    return false;
  }
  for (const t of top) {
    t.object.visible = t.step <= entry.upto;
    if (isSubassembly(t.object)) for (const c of t.object.children) c.visible = true;
    if (t.object.visible) setLook(t.object, isLast || t.step === entry.upto ? 'normal' : 'faded');
  }
  const weakest = (info?.weak ?? [])
    .filter((w) => w.step === entry.upto && resolvePath(top, w.path)?.visible)
    .sort((a, b) => a.score - b.score)[0];
  if (!weakest) return false;
  const object = resolvePath(top, weakest.path);
  setLook(object, 'normal');
  weakMarker.setFromObject(object);
  scene.add(weakMarker);
  return true;
}

function describeEntry(entry, index, total, info) {
  const base = `Step ${index} / ${total}`;
  if (entry.sub) {
    const times = entry.copies > 1 ? `${entry.copies}× ` : '';
    return `${base} · Build ${times}the ${entry.name} (${entry.upto + 1}/${entry.count})`;
  }
  const attach = stepInfo(info, entry)?.attach ?? [];
  if (!attach.length) return base;
  const what = attach.map((a) => `${a.count > 1 ? `${a.count}× ` : ''}the ${a.name}`).join(' and ');
  return `${base} · Attach ${what}`;
}

// What the kid adds in this step: parts, plus finished sub-assemblies being attached.
function newItems(info, entry) {
  const step = stepInfo(info, entry);
  return [
    ...(step?.parts ?? []).map((p) => `${p.count}× ${p.part} · ${p.color}`),
    ...(step?.attach ?? []).map((a) => `${a.count}× ${a.name} (built in the steps before)`),
  ];
}

function showCallout(info, entry) {
  const callout = document.getElementById('callout');
  const items = newItems(info, entry);
  callout.replaceChildren(
    ...items.map((text) => {
      const row = document.createElement('div');
      row.textContent = text;
      return row;
    }),
  );
  callout.hidden = items.length === 0;
}

function setupStepControls(model, top, sequence, info, initialStep, direction) {
  const slider = document.getElementById('step');
  const label = document.getElementById('step-label');
  const warning = document.getElementById('warning');
  const total = sequence.length;
  slider.max = String(total);
  let framed = null;
  const go = (step) => {
    step = Math.max(1, Math.min(total, step));
    const entry = sequence[step - 1];
    slider.value = String(step);
    label.textContent = describeEntry(entry, step, total, info);
    warning.hidden = !showEntry(top, entry, step === total, info);
    showCallout(info, entry);
    const target = entry.sub ?? model;
    if (target !== framed) {
      frameModel(target, direction);
      framed = target;
    }
  };
  slider.addEventListener('input', () => go(Number(slider.value)));
  document.getElementById('prev').addEventListener('click', () => go(Number(slider.value) - 1));
  document.getElementById('next').addEventListener('click', () => go(Number(slider.value) + 1));
  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') go(Number(slider.value) - 1);
    if (e.key === 'ArrowRight') go(Number(slider.value) + 1);
  });
  document.getElementById('controls').hidden = false;
  go(initialStep);
}

async function main() {
  if (!modelUrl) throw new Error('missing ?model= parameter');
  if (headless && !(viewName in VIEWS)) throw new Error(`unknown view "${viewName}"`);

  const loader = new LDrawLoader();
  loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
  loader.setPartsLibraryPath(LDRAW_LIBRARY);
  await loader.preloadMaterials(LDRAW_LIBRARY + 'LDConfig.ldr');

  const started = performance.now();
  const [model, info] = await Promise.all([loader.loadAsync(modelUrl), loadInstructions(modelUrl)]);
  model.rotation.x = Math.PI; // LDraw is -Y up
  scene.add(model);
  // Bounding boxes of sub-assemblies need the flipped world matrices before the first render.
  model.updateMatrixWorld(true);

  const { top, sequence } = buildSequence(model);
  const numSteps = sequence.length;
  const requested = params.has('step') ? Number(params.get('step')) : numSteps;
  if (!Number.isInteger(requested) || requested < 1 || requested > numSteps) {
    throw new Error(`step must be 1..${numSteps}, got "${params.get('step')}"`);
  }
  const direction = VIEWS[viewName ?? 'iso'];

  if (headless) {
    const entry = sequence[requested - 1];
    const weak = showEntry(top, entry, requested === numSteps, info);
    if (viewName !== 'iso') camera = orthographic;
    frameModel(entry.sub ?? model, direction);
    render();
    const items = newItems(info, entry);
    window.legoStep = [
      describeEntry(entry, requested, numSteps, info),
      items.length ? `new: ${items.join(', ')}` : '',
      weak ? 'pink box = part not well supported yet (hold carefully)' : '',
    ].filter(Boolean).join(' | ');
    window.legoReady = true;
    return;
  }

  statusEl.textContent = `Loaded in ${((performance.now() - started) / 1000).toFixed(1)} s`;
  setupStepControls(model, top, sequence, info, requested, direction);
  renderer.setAnimationLoop(() => {
    controls.update();
    render();
  });
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
  window.legoReady = true;
}

main().catch((err) => {
  console.error(err);
  statusEl.textContent = `Error: ${err.message}`;
  window.legoError = String(err.message ?? err);
});
