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

function showStep(model, step) {
  // LDrawLoader numbers steps from 0; the UI and URL use 1-based steps.
  model.traverse((c) => {
    if (c.isGroup) c.visible = c.userData.buildingStep <= step - 1;
  });
}

function setupStepControls(model, numSteps, initialStep) {
  const slider = document.getElementById('step');
  const label = document.getElementById('step-label');
  slider.max = String(numSteps);
  const go = (step) => {
    step = Math.max(1, Math.min(numSteps, step));
    slider.value = String(step);
    label.textContent = `Step ${step} / ${numSteps}`;
    showStep(model, step);
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

  const numSteps = model.userData.numBuildingSteps;
  const requested = params.has('step') ? Number(params.get('step')) : numSteps;
  if (!Number.isInteger(requested) || requested < 1 || requested > numSteps) {
    throw new Error(`step must be 1..${numSteps}, got "${params.get('step')}"`);
  }

  // Frame the finished model so the camera stays put while stepping.
  frameModel(model, VIEWS[viewName ?? 'iso']);

  if (headless) {
    showStep(model, requested);
    render();
    window.legoReady = true;
    return;
  }

  statusEl.textContent = `Loaded in ${((performance.now() - started) / 1000).toFixed(1)} s`;
  setupStepControls(model, numSteps, requested);
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
