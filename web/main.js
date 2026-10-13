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
scene.add(new THREE.HemisphereLight(0xffffff, 0x888888, 2.0));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(1, 2, 1.5);
scene.add(sun);

const camera = new THREE.PerspectiveCamera(35, window.innerWidth / window.innerHeight, 1, 100000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

function render() {
  renderer.render(scene, camera);
}

function frameModel(model, direction) {
  const sphere = new THREE.Box3().setFromObject(model).getBoundingSphere(new THREE.Sphere());
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const halfAngle = Math.min(fov, 2 * Math.atan(Math.tan(fov / 2) * camera.aspect)) / 2;
  const distance = (sphere.radius / Math.sin(halfAngle)) * 1.05;
  const dir = new THREE.Vector3(...direction).normalize();
  camera.position.copy(sphere.center).addScaledVector(dir, distance);
  camera.near = distance / 100;
  camera.far = distance * 100;
  camera.updateProjectionMatrix();
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

function showEntry(top, entry) {
  for (const t of top) {
    if (entry.sub) {
      t.object.visible = t.object === entry.sub;
    } else {
      t.object.visible = t.step <= entry.upto;
    }
  }
  if (entry.sub) {
    for (const i of entry.inner) i.object.visible = i.step <= entry.upto;
  } else {
    for (const t of top) {
      if (isSubassembly(t.object)) for (const c of t.object.children) c.visible = true;
    }
  }
}

function describeEntry(entry, index, total) {
  const base = `Step ${index} / ${total}`;
  if (!entry.sub) return base;
  const times = entry.copies > 1 ? `${entry.copies}× ` : '';
  return `${base} · Build ${times}the ${entry.name} (${entry.upto + 1}/${entry.count})`;
}

function setupStepControls(model, top, sequence, initialStep, direction) {
  const slider = document.getElementById('step');
  const label = document.getElementById('step-label');
  const total = sequence.length;
  slider.max = String(total);
  let framed = null;
  const go = (step) => {
    step = Math.max(1, Math.min(total, step));
    const entry = sequence[step - 1];
    slider.value = String(step);
    label.textContent = describeEntry(entry, step, total);
    showEntry(top, entry);
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
  const model = await loader.loadAsync(modelUrl);
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
    showEntry(top, entry);
    frameModel(entry.sub ?? model, direction);
    render();
    window.legoStep = describeEntry(entry, requested, numSteps);
    window.legoReady = true;
    return;
  }

  statusEl.textContent = `Loaded in ${((performance.now() - started) / 1000).toFixed(1)} s`;
  setupStepControls(model, top, sequence, requested, direction);
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
