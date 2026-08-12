import * as THREE from "three";
import {
  createFabricTexture,
  createMetalTexture,
  createWoodTexture,
} from "./textures.js";

const SPAN = 12.3;
const CHORD = 2.0;
const GAP = 1.82;
const LOWER_Y = 1.12;
const UPPER_Y = LOWER_Y + GAP;
const STATIONS = [-5.55, -3.7, -1.85, 0, 1.85, 3.7, 5.55];
const FRONT_Z = 0.72;
const REAR_Z = -0.72;

export function createWrightFlyer() {
  const group = new THREE.Group();
  const woodMap = createWoodTexture();
  const fabricMap = createFabricTexture();
  const metalMap = createMetalTexture();

  const wood = new THREE.MeshStandardMaterial({
    map: woodMap,
    color: 0xc4a06a,
    roughness: 0.72,
    metalness: 0.02,
  });
  const darkWood = new THREE.MeshStandardMaterial({
    map: woodMap,
    color: 0x7a4e28,
    roughness: 0.78,
  });
  const fabric = new THREE.MeshStandardMaterial({
    map: fabricMap,
    color: 0xf2e6cc,
    roughness: 0.92,
    metalness: 0,
    side: THREE.DoubleSide,
  });
  const metal = new THREE.MeshStandardMaterial({
    map: metalMap,
    color: 0x8a9098,
    roughness: 0.35,
    metalness: 0.7,
  });
  const darkMetal = new THREE.MeshStandardMaterial({
    color: 0x2a2c30,
    roughness: 0.4,
    metalness: 0.8,
  });
  const wireMat = new THREE.LineBasicMaterial({
    color: 0xb7bec6,
    transparent: true,
    opacity: 0.72,
  });

  const lowerWing = createWing(fabric, wood, 0);
  lowerWing.position.y = LOWER_Y;
  const upperWing = createWing(fabric, wood, 0.02);
  upperWing.position.y = UPPER_Y;
  group.add(lowerWing, upperWing);

  addStruts(group, wood);
  const wirePositions = [];
  addBracingWires(wirePositions);
  addCanard(group, fabric, wood, wirePositions);
  addRudders(group, fabric, wood, wirePositions);
  addSkids(group, darkWood);
  addEngine(group, metal, darkMetal, darkWood);
  const props = addPropellers(group, wood, darkMetal);
  addChains(group, darkMetal);
  addPilot(group);
  const wilbur = createWilbur();

  const wireGeo = new THREE.BufferGeometry();
  wireGeo.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(wirePositions, 3)
  );
  group.add(new THREE.LineSegments(wireGeo, wireMat));

  group.traverse((obj) => {
    if (obj.isMesh) {
      obj.castShadow = true;
      obj.receiveShadow = true;
    }
  });

  const leftProp = props.left;
  const rightProp = props.right;

  return {
    group,
    leftProp,
    rightProp,
    wilbur,
    update(dt, { spin = true, flightT = -1 } = {}) {
      const flying = flightT >= 0 && flightT < 20;
      const spinRate = spin || flying ? (flying ? 16 : 3.2) : 0;
      leftProp.rotation.z -= dt * spinRate;
      rightProp.rotation.z += dt * spinRate;
    },
  };
}

function createWing(fabric, wood, camberExtra) {
  const wing = new THREE.Group();
  const geo = createCamberedWingGeometry(SPAN, CHORD, 0.12 + camberExtra, 0.055);
  const mesh = new THREE.Mesh(geo, fabric);
  wing.add(mesh);

  const sparGeo = new THREE.CylinderGeometry(0.035, 0.035, SPAN - 0.15, 8);
  const frontSpar = new THREE.Mesh(sparGeo, wood);
  frontSpar.rotation.z = Math.PI / 2;
  frontSpar.position.set(0, 0.02, FRONT_Z);
  const rearSpar = new THREE.Mesh(sparGeo, wood);
  rearSpar.rotation.z = Math.PI / 2;
  rearSpar.position.set(0, 0.0, REAR_Z);
  wing.add(frontSpar, rearSpar);

  const ribGeo = new THREE.BoxGeometry(0.025, 0.03, CHORD - 0.12);
  for (let i = 0; i < 31; i++) {
    const x = -SPAN / 2 + 0.25 + (i / 30) * (SPAN - 0.5);
    const rib = new THREE.Mesh(ribGeo, wood);
    rib.position.set(x, 0.015, 0);
    wing.add(rib);
  }

  return wing;
}

function createCamberedWingGeometry(span, chord, camber, thickness) {
  const spanSegs = 56;
  const chordSegs = 14;
  const positions = [];
  const uvs = [];
  const indices = [];

  const point = (s, c, extra = 0) => {
    const x = (s - 0.5) * span;
    let z = (0.5 - c) * chord;
    const xc = c;
    const camberY = camber * 4 * xc * (1 - xc);
    const scallop = Math.abs(Math.sin(s * Math.PI * 30)) * 0.035 * xc * xc;
    z += scallop;
    const y = camberY - scallop * 0.4 + extra;
    return [x, y, z];
  };

  const pushVertex = (p, u, v) => {
    positions.push(p[0], p[1], p[2]);
    uvs.push(u, v);
  };

  for (let is = 0; is <= spanSegs; is++) {
    for (let ic = 0; ic <= chordSegs; ic++) {
      const s = is / spanSegs;
      const c = ic / chordSegs;
      pushVertex(point(s, c, thickness * 0.5), s * 8, c);
    }
  }
  const lowerOffset = (spanSegs + 1) * (chordSegs + 1);
  for (let is = 0; is <= spanSegs; is++) {
    for (let ic = 0; ic <= chordSegs; ic++) {
      const s = is / spanSegs;
      const c = ic / chordSegs;
      pushVertex(point(s, c, -thickness * 0.5), s * 8, c);
    }
  }

  const indexOf = (is, ic, lower) =>
    (lower ? lowerOffset : 0) + is * (chordSegs + 1) + ic;

  for (let is = 0; is < spanSegs; is++) {
    for (let ic = 0; ic < chordSegs; ic++) {
      const a = indexOf(is, ic, false);
      const b = indexOf(is + 1, ic, false);
      const c = indexOf(is + 1, ic + 1, false);
      const d = indexOf(is, ic + 1, false);
      indices.push(a, b, d, b, c, d);
      const al = indexOf(is, ic, true);
      const bl = indexOf(is + 1, ic, true);
      const cl = indexOf(is + 1, ic + 1, true);
      const dl = indexOf(is, ic + 1, true);
      indices.push(al, dl, bl, bl, dl, cl);
    }
  }

  // Close leading and trailing edges
  for (let is = 0; is < spanSegs; is++) {
    const leA = indexOf(is, 0, false);
    const leB = indexOf(is + 1, 0, false);
    const leC = indexOf(is + 1, 0, true);
    const leD = indexOf(is, 0, true);
    indices.push(leA, leD, leB, leB, leD, leC);
    const teA = indexOf(is, chordSegs, false);
    const teB = indexOf(is + 1, chordSegs, false);
    const teC = indexOf(is + 1, chordSegs, true);
    const teD = indexOf(is, chordSegs, true);
    indices.push(teA, teB, teD, teB, teC, teD);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();
  return geo;
}

function addStruts(group, wood) {
  const strutGeo = new THREE.CylinderGeometry(0.028, 0.032, GAP, 8);
  for (const x of STATIONS) {
    for (const z of [FRONT_Z, REAR_Z]) {
      const strut = new THREE.Mesh(strutGeo, wood);
      strut.position.set(x, LOWER_Y + GAP / 2, z);
      group.add(strut);
    }
  }
}

function addBracingWires(pts) {
  const line = (a, b) => pts.push(a[0], a[1], a[2], b[0], b[1], b[2]);

  for (let i = 0; i < STATIONS.length - 1; i++) {
    const x0 = STATIONS[i];
    const x1 = STATIONS[i + 1];
    for (const z of [FRONT_Z, REAR_Z]) {
      line([x0, LOWER_Y + 0.04, z], [x1, UPPER_Y - 0.04, z]);
      line([x0, UPPER_Y - 0.04, z], [x1, LOWER_Y + 0.04, z]);
    }
  }

  for (const x of STATIONS) {
    line([x, LOWER_Y + 0.04, FRONT_Z], [x, UPPER_Y - 0.04, REAR_Z]);
    line([x, UPPER_Y - 0.04, FRONT_Z], [x, LOWER_Y + 0.04, REAR_Z]);
  }
}

function addCanard(group, fabric, wood, wirePts) {
  const canard = new THREE.Group();
  canard.position.set(0, LOWER_Y + GAP * 0.42, 3.35);

  const surfaceGeo = createCamberedWingGeometry(2.55, 0.72, 0.05, 0.03);
  const lower = new THREE.Mesh(surfaceGeo, fabric);
  const upper = new THREE.Mesh(surfaceGeo, fabric);
  lower.position.y = -0.22;
  upper.position.y = 0.22;
  canard.add(lower, upper);

  const postGeo = new THREE.CylinderGeometry(0.018, 0.018, 0.44, 6);
  for (const x of [-1.05, 0, 1.05]) {
    const post = new THREE.Mesh(postGeo, wood);
    post.position.set(x, 0, 0.2);
    canard.add(post);
  }

  const boomGeo = new THREE.CylinderGeometry(0.02, 0.02, 3.55, 6);
  for (const [x, y] of [
    [-0.55, LOWER_Y + 0.08],
    [0.55, LOWER_Y + 0.08],
    [-0.55, UPPER_Y - 0.08],
    [0.55, UPPER_Y - 0.08],
  ]) {
    const boom = new THREE.Mesh(boomGeo, wood);
    boom.rotation.x = Math.PI / 2;
    boom.position.set(x, y, 1.7);
    group.add(boom);
  }

  const line = (a, b) => wirePts.push(a[0], a[1], a[2], b[0], b[1], b[2]);
  line([-0.55, LOWER_Y + 0.08, FRONT_Z], [-0.55, LOWER_Y + 0.2, 3.35]);
  line([0.55, LOWER_Y + 0.08, FRONT_Z], [0.55, LOWER_Y + 0.2, 3.35]);
  line([-0.55, UPPER_Y - 0.08, FRONT_Z], [-0.55, UPPER_Y - 0.5, 3.35]);
  line([0.55, UPPER_Y - 0.08, FRONT_Z], [0.55, UPPER_Y - 0.5, 3.35]);

  group.add(canard);
}

function addRudders(group, fabric, wood, wirePts) {
  const rudderGroup = new THREE.Group();
  rudderGroup.position.set(0, LOWER_Y + GAP * 0.5, -3.15);

  const rudderGeo = new THREE.BoxGeometry(0.04, 1.35, 0.58);
  const left = new THREE.Mesh(rudderGeo, fabric);
  const right = new THREE.Mesh(rudderGeo, fabric);
  left.position.x = -0.28;
  right.position.x = 0.28;
  rudderGroup.add(left, right);

  const bar = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.04, 0.04), wood);
  bar.position.y = 0.4;
  rudderGroup.add(bar);

  const boomGeo = new THREE.CylinderGeometry(0.02, 0.02, 3.3, 6);
  for (const [x, y] of [
    [-0.45, LOWER_Y + 0.08],
    [0.45, LOWER_Y + 0.08],
    [-0.45, UPPER_Y - 0.08],
    [0.45, UPPER_Y - 0.08],
  ]) {
    const boom = new THREE.Mesh(boomGeo, wood);
    boom.rotation.x = Math.PI / 2;
    boom.position.set(x, y, -2.05);
    group.add(boom);
  }

  const line = (a, b) => wirePts.push(a[0], a[1], a[2], b[0], b[1], b[2]);
  line([-0.45, LOWER_Y + 0.08, REAR_Z], [-0.28, LOWER_Y + 0.2, -3.15]);
  line([0.45, LOWER_Y + 0.08, REAR_Z], [0.28, LOWER_Y + 0.2, -3.15]);
  line([-0.45, UPPER_Y - 0.08, REAR_Z], [-0.28, UPPER_Y - 0.3, -3.15]);
  line([0.45, UPPER_Y - 0.08, REAR_Z], [0.28, UPPER_Y - 0.3, -3.15]);

  group.add(rudderGroup);
}

function addSkids(group, wood) {
  const skidShape = new THREE.Shape();
  skidShape.moveTo(-2.6, 0);
  skidShape.lineTo(2.4, 0);
  skidShape.quadraticCurveTo(3.3, 0.05, 3.5, 0.55);
  skidShape.lineTo(3.35, 0.62);
  skidShape.quadraticCurveTo(3.15, 0.18, 2.4, 0.1);
  skidShape.lineTo(-2.6, 0.1);
  skidShape.closePath();

  const skidGeo = new THREE.ExtrudeGeometry(skidShape, {
    depth: 0.06,
    bevelEnabled: false,
  });
  skidGeo.rotateY(-Math.PI / 2);
  skidGeo.translate(0.03, 0, 0);

  for (const x of [-0.72, 0.72]) {
    const skid = new THREE.Mesh(skidGeo, wood);
    skid.position.set(x, 0.02, 0.15);
    group.add(skid);

    const stiltGeo = new THREE.CylinderGeometry(0.025, 0.03, 1.05, 6);
    for (const z of [0.55, -0.55]) {
      const stilt = new THREE.Mesh(stiltGeo, wood);
      stilt.position.set(x, 0.58, z);
      stilt.rotation.z = x > 0 ? -0.12 : 0.12;
      group.add(stilt);
    }
  }

  const cross = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.05, 0.06), wood);
  cross.position.set(0, 0.12, 0.4);
  group.add(cross);
}

function addEngine(group, metal, darkMetal, wood) {
  const engine = new THREE.Group();
  engine.position.set(0.62, LOWER_Y + 0.28, 0.05);

  const brass = new THREE.MeshStandardMaterial({
    color: 0xb08a4a,
    roughness: 0.35,
    metalness: 0.75,
  });
  const crank = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.24, 1.02), metal);
  engine.add(crank);

  const cylGeo = new THREE.CylinderGeometry(0.085, 0.09, 0.26, 12);
  for (let i = 0; i < 4; i++) {
    const cyl = new THREE.Mesh(cylGeo, brass);
    cyl.position.set(0.2, 0.16, -0.38 + i * 0.25);
    engine.add(cyl);
    const head = new THREE.Mesh(
      new THREE.BoxGeometry(0.16, 0.06, 0.16),
      darkMetal
    );
    head.position.set(0.2, 0.31, -0.38 + i * 0.25);
    engine.add(head);
  }

  const flywheel = new THREE.Mesh(
    new THREE.CylinderGeometry(0.18, 0.18, 0.05, 20),
    darkMetal
  );
  flywheel.rotation.x = Math.PI / 2;
  flywheel.position.set(0, 0, 0.55);
  engine.add(flywheel);

  const tank = new THREE.Mesh(
    new THREE.CylinderGeometry(0.09, 0.09, 0.32, 12),
    wood
  );
  tank.rotation.z = Math.PI / 2;
  tank.position.set(-0.05, 0.28, -0.15);
  engine.add(tank);

  const radiator = new THREE.Mesh(
    new THREE.BoxGeometry(0.06, 0.42, 0.55),
    metal
  );
  radiator.position.set(0.28, 0.22, 0.05);
  engine.add(radiator);

  for (let i = 0; i < 8; i++) {
    const fin = new THREE.Mesh(
      new THREE.BoxGeometry(0.01, 0.4, 0.04),
      darkMetal
    );
    fin.position.set(0.32, 0.22, -0.22 + i * 0.06);
    engine.add(fin);
  }

  group.add(engine);
}

function addPropellers(group, wood, hubMat) {
  const bladeMat = wood.clone();
  bladeMat.color.set(0xe6c48a);
  bladeMat.roughness = 0.45;
  bladeMat.metalness = 0.04;
  bladeMat.side = THREE.DoubleSide;

  const makeProp = (x) => {
    const prop = new THREE.Group();
    prop.position.set(x, LOWER_Y + GAP * 0.5, -1.22);
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.08, 0.12, 12),
      hubMat
    );
    hub.rotation.x = Math.PI / 2;
    prop.add(hub);
    const bladeGeo = createBladeGeometry();
    const b1 = new THREE.Mesh(bladeGeo, bladeMat);
    const b2 = new THREE.Mesh(bladeGeo, bladeMat);
    b2.rotation.z = Math.PI;
    prop.add(b1, b2);
    group.add(prop);
    return prop;
  };

  return { left: makeProp(-2.55), right: makeProp(2.55) };
}

function createBladeGeometry() {
  const geo = new THREE.BoxGeometry(0.28, 1.26, 0.04, 1, 20, 1);
  geo.translate(0, 0.72, 0);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    const t = THREE.MathUtils.clamp((y - 0.08) / 1.26, 0, 1);
    const taper = 0.35 + Math.sin(t * Math.PI) * 0.75;
    const twist = t * 0.65;
    const x = pos.getX(i) * taper;
    const z = pos.getZ(i) * (1 - t * 0.35);
    const c = Math.cos(twist);
    const s = Math.sin(twist);
    pos.setXYZ(i, x * c - z * s, y, x * s + z * c);
  }
  geo.computeVertexNormals();
  return geo;
}

function addChains(group, metal) {
  const tubeGeo = new THREE.CylinderGeometry(0.018, 0.018, 2.4, 8);
  const left = new THREE.Mesh(tubeGeo, metal);
  left.rotation.z = Math.PI / 2;
  left.position.set(-1.15, LOWER_Y + GAP * 0.5, -1.18);
  const right = new THREE.Mesh(tubeGeo, metal);
  right.rotation.z = Math.PI / 2;
  right.position.set(1.55, LOWER_Y + GAP * 0.5, -1.18);
  group.add(left, right);

  const sprocketGeo = new THREE.TorusGeometry(0.09, 0.018, 8, 16);
  for (const x of [-2.55, 2.55, 0.62]) {
    const s = new THREE.Mesh(sprocketGeo, metal);
    s.position.set(x, LOWER_Y + GAP * 0.5, -1.18);
    group.add(s);
  }
}

function addPilot(group) {
  const pilot = createPerson({ clothing: 0x1d1f2a, cap: 0x2b2b2b });
  pilot.rotation.x = -Math.PI / 2 + 0.12;
  pilot.position.set(-0.42, LOWER_Y + 0.16, 0.15);
  group.add(pilot);

  const cradle = new THREE.Mesh(
    new THREE.TorusGeometry(0.18, 0.025, 8, 16, Math.PI),
    new THREE.MeshStandardMaterial({ color: 0x6b4423, roughness: 0.7 })
  );
  cradle.rotation.x = Math.PI / 2;
  cradle.position.set(-0.42, LOWER_Y + 0.2, -0.05);
  group.add(cradle);

  const lever = new THREE.Mesh(
    new THREE.CylinderGeometry(0.015, 0.015, 1.1, 6),
    new THREE.MeshStandardMaterial({ color: 0x8a6239, roughness: 0.7 })
  );
  lever.rotation.x = Math.PI / 2;
  lever.position.set(-0.42, LOWER_Y + 0.28, 1.15);
  group.add(lever);
}

function createWilbur() {
  const wilbur = createPerson({ clothing: 0x2a241c, cap: 0x3a3328, standing: true });
  wilbur.name = "wilbur";
  wilbur.position.set(6.6, 0, 1.2);
  wilbur.rotation.y = Math.PI;
  wilbur.traverse((obj) => {
    if (obj.isMesh) {
      obj.castShadow = true;
      obj.receiveShadow = true;
    }
  });
  return wilbur;
}

function createPerson({ clothing, cap, standing = false }) {
  const g = new THREE.Group();
  const cloth = new THREE.MeshStandardMaterial({
    color: clothing,
    roughness: 0.85,
  });
  const skin = new THREE.MeshStandardMaterial({
    color: 0xc4a07a,
    roughness: 0.7,
  });
  const capMat = new THREE.MeshStandardMaterial({ color: cap, roughness: 0.8 });

  const torso = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.22, 0.55), cloth);
  torso.position.y = standing ? 1.15 : 0;
  g.add(torso);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 10), skin);
  head.position.set(0, standing ? 1.48 : 0.02, standing ? 0 : 0.38);
  g.add(head);

  const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.13, 0.08, 12), capMat);
  hat.position.copy(head.position);
  hat.position.y += standing ? 0.08 : 0.08;
  g.add(hat);

  const brim = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.02, 12), capMat);
  brim.position.copy(hat.position);
  brim.position.y -= 0.04;
  g.add(brim);

  const armGeo = new THREE.BoxGeometry(0.08, 0.08, 0.42);
  const leftArm = new THREE.Mesh(armGeo, cloth);
  const rightArm = new THREE.Mesh(armGeo, cloth);
  if (standing) {
    leftArm.position.set(-0.22, 1.12, 0.05);
    rightArm.position.set(0.22, 1.12, 0.05);
    leftArm.rotation.x = 0.35;
    rightArm.rotation.x = -0.35;
  } else {
    leftArm.position.set(-0.22, 0.02, 0.28);
    rightArm.position.set(0.22, 0.02, 0.28);
    leftArm.rotation.x = -0.15;
    rightArm.rotation.x = -0.15;
  }
  g.add(leftArm, rightArm);

  const legGeo = new THREE.BoxGeometry(0.1, standing ? 0.7 : 0.1, standing ? 0.1 : 0.45);
  const leftLeg = new THREE.Mesh(legGeo, cloth);
  const rightLeg = new THREE.Mesh(legGeo, cloth);
  leftLeg.name = "leftLeg";
  rightLeg.name = "rightLeg";
  if (standing) {
    leftLeg.position.set(-0.09, 0.45, 0);
    rightLeg.position.set(0.09, 0.45, 0);
  } else {
    leftLeg.position.set(-0.1, 0, -0.42);
    rightLeg.position.set(0.1, 0, -0.42);
  }
  g.add(leftLeg, rightLeg);

  return g;
}
