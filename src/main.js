import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { createEnvironment } from "./environment.js";
import { createWrightFlyer } from "./wrightFlyer.js";

const canvas = document.querySelector("#c");
const flightBtn = document.querySelector("#flight-btn");
const spinToggle = document.querySelector("#spin-toggle");
const followToggle = document.querySelector("#follow-toggle");
const caption = document.querySelector("#flight-caption");

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: "high-performance",
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(46, 2, 0.1, 2000);
const introFrom = new THREE.Vector3(3.2, 1.8, 2.4);
const introTo = new THREE.Vector3(9.5, 3.6, 8.4);
camera.position.copy(introFrom);

const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 1.45, 0.2);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI / 2 - 0.04;
controls.minDistance = 3.2;
controls.maxDistance = 48;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.45;

createEnvironment(scene);

const flyer = createWrightFlyer();
scene.add(flyer.group);
scene.add(flyer.wilbur);

const clock = new THREE.Clock();
let intro = 0;
let flightT = -1;

const followOffset = new THREE.Vector3(7.5, 3.2, 6.5);
const followLook = new THREE.Vector3();
const camScratch = new THREE.Vector3();
const chasePos = new THREE.Vector3();

flightBtn.addEventListener("click", () => {
  if (flightT >= 0) {
    resetFlight();
    return;
  }
  startFlight();
});

function startFlight() {
  flightT = 0;
  intro = 99;
  controls.autoRotate = false;
  followToggle.checked = true;
  flightBtn.textContent = "Reset";
  flightBtn.classList.add("active");
  caption.classList.remove("hidden");
}

function resetFlight() {
  flightT = -1;
  flyer.group.position.set(0, 0, 0);
  flyer.group.rotation.set(0, 0, 0);
  flyer.wilbur.position.set(6.6, 0, 1.2);
  flyer.wilbur.visible = true;
  flightBtn.textContent = "Replay First Flight";
  flightBtn.classList.remove("active");
  caption.classList.add("hidden");
  caption.textContent = "";
}

function flightPose(t) {
  const spinUp = 2.2;
  const ground = 3.2;
  const air = 12;
  const settle = 2.2;
  let z = 0;
  let y = 0;
  let pitch = 0;
  let roll = 0;
  let phase = "Spinning up the 12-horsepower engine";

  if (t < spinUp) {
    z = 0;
  } else if (t < spinUp + ground) {
    const u = (t - spinUp) / ground;
    z = THREE.MathUtils.lerp(0, 16.5, u * u);
    phase = "Rolling along the wooden monorail";
  } else if (t < spinUp + ground + air) {
    const u = (t - spinUp - ground) / air;
    z = 16.5 + u * 36.5;
    y = Math.sin(u * Math.PI) * 3.1;
    pitch = Math.sin(u * Math.PI * 2.2) * 0.06 - 0.03;
    roll = Math.sin(u * Math.PI * 3.1) * 0.08;
    phase =
      u < 0.15
        ? "Lift-off — 10:35 a.m., December 17, 1903"
        : u < 0.85
          ? "Airborne: 12 seconds, 120 feet, Orville at the hip cradle"
          : "Settling back toward the dunes";
  } else {
    const u = Math.min(1, (t - spinUp - ground - air) / settle);
    z = 16.5 + 36.5;
    y = THREE.MathUtils.lerp(0.15, 0, u);
    pitch = THREE.MathUtils.lerp(-0.04, 0, u);
    phase = "The first flight is over. The world has changed.";
  }

  return { z, y, pitch, roll, phase, done: t > spinUp + ground + air + settle };
}

function resize() {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (canvas.width !== w || canvas.height !== h) {
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
}

function animateWilbur(t) {
  const wilbur = flyer.wilbur;
  const left = wilbur.getObjectByName("leftLeg");
  const right = wilbur.getObjectByName("rightLeg");

  if (t < 0) {
    wilbur.position.set(6.6, 0, 1.2);
    if (left) left.rotation.x = 0;
    if (right) right.rotation.x = 0;
    return;
  }

  const running = t > 2.2 && t < 8.5;
  wilbur.visible = t < 10;
  if (running) {
    const runZ = (t - 2.2) * 7.2;
    wilbur.position.set(6.4, 0, 1.2 + runZ);
    const swing = Math.sin(t * 14) * 0.55;
    if (left) left.rotation.x = swing;
    if (right) right.rotation.x = -swing;
  }
}

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  intro += dt;

  if (intro < 5) {
    const k = 1 - Math.pow(1 - intro / 5, 3);
    camera.position.lerpVectors(introFrom, introTo, k);
  }

  if (flightT >= 0) {
    flightT += dt;
    const pose = flightPose(flightT);
    flyer.group.position.set(0, pose.y, pose.z);
    flyer.group.rotation.set(pose.pitch, 0, pose.roll);
    caption.textContent = pose.phase;
    if (pose.done) {
      flightT = 22;
    }
  }

  flyer.update(dt, {
    spin: spinToggle.checked || flightT >= 0,
    flightT,
  });
  animateWilbur(flightT);

  if (flightT >= 0) {
    camScratch.set(
      flyer.group.position.x,
      flyer.group.position.y + 1.5,
      flyer.group.position.z
    );
    followLook.lerp(camScratch, 1 - Math.pow(0.02, dt));
    controls.target.copy(followLook);
    if (followToggle.checked) {
      camera.position.lerp(
        camScratch.clone().add(followOffset),
        1 - Math.pow(0.04, dt)
      );
    }
  }

  controls.update();
  resize();
  renderer.render(scene, camera);
}

animate();

window.addEventListener("pointerdown", () => {
  if (flightT < 0) controls.autoRotate = false;
  intro = 99;
});
