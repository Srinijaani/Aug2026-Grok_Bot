import * as THREE from "three";

function makeCanvas(size = 512) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  return [canvas, canvas.getContext("2d")];
}

function noise(ctx, size, alpha, scale = 1) {
  const image = ctx.getImageData(0, 0, size, size);
  const data = image.data;
  for (let i = 0; i < data.length; i += 4) {
    const n = (Math.random() - 0.5) * alpha * scale;
    data[i] = Math.max(0, Math.min(255, data[i] + n));
    data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + n));
    data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + n));
  }
  ctx.putImageData(image, 0, 0);
}

export function createWoodTexture() {
  const size = 512;
  const [canvas, ctx] = makeCanvas(size);
  ctx.fillStyle = "#8a5a32";
  ctx.fillRect(0, 0, size, size);

  for (let y = 0; y < size; y++) {
    const wobble =
      Math.sin(y * 0.11) * 10 + Math.sin(y * 0.37) * 5 + Math.sin(y * 0.02) * 18;
    const shade = 0.08 + ((y * 17) % 11) * 0.008;
    ctx.strokeStyle = `rgba(42, 22, 8, ${shade})`;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.bezierCurveTo(140, y + wobble, 360, y - wobble, size, y);
    ctx.stroke();
  }

  for (let i = 0; i < 18; i++) {
    const y = Math.random() * size;
    ctx.strokeStyle = `rgba(210, 170, 110, ${0.04 + Math.random() * 0.05})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(size, y + (Math.random() - 0.5) * 8);
    ctx.stroke();
  }

  noise(ctx, size, 18);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = 8;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export function createFabricTexture() {
  const size = 512;
  const [canvas, ctx] = makeCanvas(size);
  ctx.fillStyle = "#efe6d2";
  ctx.fillRect(0, 0, size, size);

  ctx.strokeStyle = "rgba(120, 100, 70, 0.12)";
  ctx.lineWidth = 1;
  for (let i = 0; i < size; i += 4) {
    ctx.beginPath();
    ctx.moveTo(i, 0);
    ctx.lineTo(i, size);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, i);
    ctx.lineTo(size, i);
    ctx.stroke();
  }

  // Rib shadows along the chord
  for (let i = 0; i < 16; i++) {
    const x = (i / 16) * size;
    const gradient = ctx.createLinearGradient(x - 6, 0, x + 6, 0);
    gradient.addColorStop(0, "rgba(90, 70, 40, 0)");
    gradient.addColorStop(0.5, "rgba(90, 70, 40, 0.16)");
    gradient.addColorStop(1, "rgba(90, 70, 40, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(x - 6, 0, 12, size);
  }

  noise(ctx, size, 14);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(1, 1);
  texture.anisotropy = 8;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export function createSandTexture() {
  const size = 512;
  const [canvas, ctx] = makeCanvas(size);
  ctx.fillStyle = "#d2b48a";
  ctx.fillRect(0, 0, size, size);

  for (let i = 0; i < 9000; i++) {
    const x = Math.random() * size;
    const y = Math.random() * size;
    const r = Math.random() * 1.8;
    const shade = 150 + Math.random() * 80;
    ctx.fillStyle = `rgba(${shade}, ${shade - 30}, ${shade - 70}, 0.35)`;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  noise(ctx, size, 22);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(40, 40);
  texture.anisotropy = 8;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export function createMetalTexture() {
  const size = 256;
  const [canvas, ctx] = makeCanvas(size);
  const gradient = ctx.createLinearGradient(0, 0, size, size);
  gradient.addColorStop(0, "#6a6e74");
  gradient.addColorStop(0.5, "#9aa0a8");
  gradient.addColorStop(1, "#4c5056");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);
  noise(ctx, size, 28);
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}
