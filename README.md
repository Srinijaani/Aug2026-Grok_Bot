# Wright Flyer, 1903

An interactive 3D reconstruction of the Wright brothers' first successful airplane, built with [Three.js](https://threejs.org/).

The scene is set on the dunes at Kill Devil Hills, North Carolina, on the morning of December 17, 1903. Orville lies prone at the hip cradle. Twin pusher propellers, a forward canard, and a 12-horsepower four-cylinder engine are modeled to the Flyer's distinctive layout. Press **Replay First Flight** to watch the 12-second, 120-foot hop — with Wilbur running alongside, as in the famous photograph.

## Run locally

```bash
npm install
npm run dev
```

Then open the URL Vite prints (default `http://localhost:5173`).

## Controls

- Drag to orbit, scroll to zoom, right-drag to pan
- **Replay First Flight** — recreates the first powered flight
- **Propellers** — spin the carved spruce blades
- **Follow camera** — track the Flyer during the hop

## Stack

- Three.js (procedural geometry, physically based materials, ACES tone mapping)
- Vite
- No external 3D assets — wood, muslin, and sand are generated at runtime
