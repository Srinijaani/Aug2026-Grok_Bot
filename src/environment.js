import * as THREE from "three";
import { Sky } from "three/addons/objects/Sky.js";
import { createSandTexture } from "./textures.js";

export function createEnvironment(scene) {
  scene.fog = new THREE.FogExp2(0xb7c7d6, 0.012);

  const sky = new Sky();
  sky.scale.setScalar(450000);
  scene.add(sky);

  const sun = new THREE.Vector3();
  const elevation = 22;
  const azimuth = 148;
  const phi = THREE.MathUtils.degToRad(90 - elevation);
  const theta = THREE.MathUtils.degToRad(azimuth);
  sun.setFromSphericalCoords(1, phi, theta);

  sky.material.uniforms.turbidity.value = 4;
  sky.material.uniforms.rayleigh.value = 1.6;
  sky.material.uniforms.mieCoefficient.value = 0.005;
  sky.material.uniforms.mieDirectionalG.value = 0.8;
  sky.material.uniforms.sunPosition.value.copy(sun);

  const hemi = new THREE.HemisphereLight(0xcfe4f7, 0xc4a574, 0.7);
  scene.add(hemi);

  const sunLight = new THREE.DirectionalLight(0xfff1d6, 2.15);
  sunLight.position.copy(sun).multiplyScalar(80);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.set(2048, 2048);
  sunLight.shadow.camera.near = 1;
  sunLight.shadow.camera.far = 160;
  sunLight.shadow.camera.left = -30;
  sunLight.shadow.camera.right = 30;
  sunLight.shadow.camera.top = 20;
  sunLight.shadow.camera.bottom = -20;
  sunLight.shadow.bias = -0.0004;
  scene.add(sunLight);

  const fill = new THREE.DirectionalLight(0x9bb8d4, 0.35);
  fill.position.set(-20, 12, -10);
  scene.add(fill);

  const sandTex = createSandTexture();
  const groundGeo = new THREE.PlaneGeometry(420, 420, 160, 160);
  groundGeo.rotateX(-Math.PI / 2);
  const pos = groundGeo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const z = pos.getZ(i);
    const dunes =
      Math.sin(x * 0.028) * 2.4 +
      Math.sin(z * 0.021 + 0.4) * 1.9 +
      Math.sin(x * 0.07 + z * 0.045) * 0.7 +
      Math.sin(x * 0.13 - z * 0.09) * 0.25;
    const dist = Math.hypot(x, z);
    const flatten = THREE.MathUtils.smoothstep(dist, 10, 28);
    pos.setY(i, dunes * flatten);
  }
  groundGeo.computeVertexNormals();

  const ground = new THREE.Mesh(
    groundGeo,
    new THREE.MeshStandardMaterial({
      map: sandTex,
      color: 0xe2c899,
      roughness: 0.95,
      metalness: 0.0,
    })
  );
  ground.receiveShadow = true;
  scene.add(ground);

  // Distant Atlantic
  const ocean = new THREE.Mesh(
    new THREE.PlaneGeometry(500, 180, 1, 1),
    new THREE.MeshStandardMaterial({
      color: 0x3a6f8f,
      roughness: 0.35,
      metalness: 0.15,
    })
  );
  ocean.rotation.x = -Math.PI / 2;
  ocean.position.set(0, -0.6, -220);
  scene.add(ocean);

  const rail = createLaunchRail();
  scene.add(rail);

  return { sun, sunLight, rail };
}

function createLaunchRail() {
  const group = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({
    color: 0x6b4a2b,
    roughness: 0.85,
  });

  const beam = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.08, 18.3), wood);
  beam.position.set(0, 0.06, 4.2);
  beam.castShadow = true;
  beam.receiveShadow = true;
  group.add(beam);

  const tieGeo = new THREE.BoxGeometry(0.55, 0.05, 0.08);
  for (let i = 0; i < 24; i++) {
    const tie = new THREE.Mesh(tieGeo, wood);
    tie.position.set(0, 0.03, -4.5 + i * 0.78);
    tie.receiveShadow = true;
    group.add(tie);
  }

  return group;
}
