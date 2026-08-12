(() => {
  "use strict";

  const canvas = document.getElementById("game");
  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;

  const W = canvas.width;
  const H = canvas.height;
  const SCREEN_COUNT = 10;
  const WORLD_W = W * SCREEN_COUNT;
  const GROUND_Y = H - 78;
  const GRAVITY = 0.72;
  const JUMP_V = -14.5;
  const MOVE_SPEED = 4.6;
  const FIRE_COOLDOWN = 220;
  const MAX_HP = 3;

  const overlay = document.getElementById("overlay");
  const startPanel = document.getElementById("start-panel");
  const pausePanel = document.getElementById("pause-panel");
  const winPanel = document.getElementById("win-panel");
  const losePanel = document.getElementById("lose-panel");
  const winStats = document.getElementById("win-stats");

  const keys = new Set();
  const sprites = {};

  let state = "title"; // title | playing | paused | won | lost
  let lastTime = 0;
  let rafId = 0;
  let cameraX = 0;
  let particles = [];
  let projectiles = [];
  let enemies = [];
  let score = 0;
  let antsDefeated = 0;
  let runTime = 0;
  let flash = 0;

  const player = {
    x: 80,
    y: GROUND_Y,
    w: 78,
    h: 92,
    vx: 0,
    vy: 0,
    onGround: true,
    facing: 1,
    hp: MAX_HP,
    invuln: 0,
    anim: "idle",
    frameT: 0,
    shootCD: 0,
  };

  const ASSET_LIST = {
    bg: "assets/sprites/bg.png",
    playerIdle: "assets/sprites/player-gun.png",
    playerHop: "assets/sprites/player-hop.png",
    playerAir: "assets/sprites/player-air.png",
    playerCrouch: "assets/sprites/player-crouch.png",
    antStand: "assets/sprites/ant-stand.png",
    antWalk: "assets/sprites/ant-walk.png",
    fireball: "assets/sprites/fireball.png",
    finish: "assets/sprites/finish.png",
  };

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }

  async function loadAssets() {
    const entries = Object.entries(ASSET_LIST);
    await Promise.all(
      entries.map(async ([key, src]) => {
        sprites[key] = await loadImage(src);
      })
    );
  }

  function resetGame() {
    player.x = 80;
    player.y = GROUND_Y - player.h;
    player.vx = 0;
    player.vy = 0;
    player.onGround = true;
    player.facing = 1;
    player.hp = MAX_HP;
    player.invuln = 0;
    player.anim = "idle";
    player.frameT = 0;
    player.shootCD = 0;
    cameraX = 0;
    particles = [];
    projectiles = [];
    score = 0;
    antsDefeated = 0;
    runTime = 0;
    flash = 0;
    spawnEnemies();
  }

  function spawnEnemies() {
    enemies = [];
    // Scatter ants across 10 screens (skip first half-screen for breathing room)
    const count = 22;
    for (let i = 0; i < count; i++) {
      const t = (i + 1) / (count + 1);
      const x = 420 + t * (WORLD_W - 700) + (Math.random() * 80 - 40);
      const patrol = 70 + Math.random() * 90;
      enemies.push({
        x,
        y: GROUND_Y - 70,
        w: 70,
        h: 70,
        vx: Math.random() > 0.5 ? 1.4 : -1.4,
        home: x,
        patrol,
        hp: 2,
        frameT: Math.random() * 10,
        hitFlash: 0,
        alive: true,
      });
    }
  }

  function showPanel(which) {
    overlay.classList.remove("hidden");
    for (const el of [startPanel, pausePanel, winPanel, losePanel]) {
      el.classList.add("hidden");
    }
    if (which) which.classList.remove("hidden");
  }

  function hideOverlay() {
    overlay.classList.add("hidden");
  }

  function startPlaying() {
    resetGame();
    state = "playing";
    hideOverlay();
    lastTime = performance.now();
    if (!rafId) rafId = requestAnimationFrame(loop);
  }

  function aabb(a, b) {
    return (
      a.x < b.x + b.w &&
      a.x + a.w > b.x &&
      a.y < b.y + b.h &&
      a.y + a.h > b.y
    );
  }

  function spawnBurst(x, y, color, n = 10) {
    for (let i = 0; i < n; i++) {
      const ang = Math.random() * Math.PI * 2;
      const sp = 1.5 + Math.random() * 3.5;
      particles.push({
        x,
        y,
        vx: Math.cos(ang) * sp,
        vy: Math.sin(ang) * sp - 1,
        life: 0.4 + Math.random() * 0.5,
        max: 0.9,
        color,
        size: 2 + Math.random() * 3,
      });
    }
  }

  function tryShoot() {
    if (player.shootCD > 0) return;
    player.shootCD = FIRE_COOLDOWN;
    const muzzleX = player.facing > 0 ? player.x + player.w - 8 : player.x + 8;
    const muzzleY = player.y + player.h * 0.42;
    projectiles.push({
      x: muzzleX,
      y: muzzleY - 8,
      w: 56,
      h: 34,
      vx: player.facing * 8.5,
      life: 2.2,
      spin: 0,
    });
    spawnBurst(muzzleX, muzzleY, "#ffcc33", 10);
    spawnBurst(muzzleX, muzzleY, "#ff2200", 8);
  }

  function hurtPlayer() {
    if (player.invuln > 0) return;
    player.hp -= 1;
    player.invuln = 1.2;
    flash = 0.25;
    player.vy = -8;
    player.vx = -player.facing * 5;
    spawnBurst(player.x + player.w / 2, player.y + player.h / 2, "#ff5555", 14);
    if (player.hp <= 0) {
      state = "lost";
      showPanel(losePanel);
    }
  }

  function update(dt) {
    if (state !== "playing") return;
    runTime += dt;
    player.frameT += dt;
    if (player.shootCD > 0) player.shootCD -= dt * 1000;
    if (player.invuln > 0) player.invuln -= dt;
    if (flash > 0) flash -= dt;

    // Movement (arrows / WASD)
    let moving = false;
    player.vx = 0;
    if (keys.has("ArrowLeft") || keys.has("KeyA")) {
      player.vx = -MOVE_SPEED;
      player.facing = -1;
      moving = true;
    }
    if (keys.has("ArrowRight") || keys.has("KeyD")) {
      player.vx = MOVE_SPEED;
      player.facing = 1;
      moving = true;
    }

    // Jump (Space / W / Up)
    if (
      (keys.has("Space") || keys.has("KeyW") || keys.has("ArrowUp")) &&
      player.onGround
    ) {
      player.vy = JUMP_V;
      player.onGround = false;
      spawnBurst(player.x + player.w / 2, player.y + player.h, "#9dffb0", 5);
    }

    // Shoot (X / Z / Ctrl — standard action keys)
    if (
      keys.has("KeyX") ||
      keys.has("KeyZ") ||
      keys.has("ControlLeft") ||
      keys.has("ControlRight")
    ) {
      tryShoot();
    }

    player.vy += GRAVITY;
    player.x += player.vx;
    player.y += player.vy;

    if (player.x < 0) player.x = 0;
    if (player.x + player.w > WORLD_W) player.x = WORLD_W - player.w;

    if (player.y + player.h >= GROUND_Y) {
      player.y = GROUND_Y - player.h;
      player.vy = 0;
      player.onGround = true;
    } else {
      player.onGround = false;
    }

    if (!player.onGround) {
      player.anim = player.vy < -2 ? "air" : "hop";
    } else if (moving) {
      player.anim = "run";
    } else {
      player.anim = "idle";
    }

    // Camera follows player, clamp to world
    cameraX = player.x + player.w / 2 - W * 0.35;
    cameraX = Math.max(0, Math.min(cameraX, WORLD_W - W));

    // Projectiles
    for (const p of projectiles) {
      p.x += p.vx;
      p.life -= dt;
      p.spin += dt * 14;
      // trail particles
      if (Math.random() < 0.7) {
        particles.push({
          x: p.x + (p.vx > 0 ? 0 : p.w),
          y: p.y + p.h / 2 + (Math.random() * 8 - 4),
          vx: -Math.sign(p.vx) * (0.5 + Math.random()),
          vy: Math.random() * 1.2 - 0.6,
          life: 0.25 + Math.random() * 0.2,
          max: 0.45,
          color: Math.random() > 0.45 ? "#ff2200" : "#ffee33",
          size: 2 + Math.random() * 3,
        });
      }
    }
    projectiles = projectiles.filter(
      (p) => p.life > 0 && p.x > cameraX - 40 && p.x < cameraX + W + 40
    );

    // Enemies
    for (const e of enemies) {
      if (!e.alive) continue;
      e.frameT += dt;
      if (e.hitFlash > 0) e.hitFlash -= dt;
      e.x += e.vx;
      if (e.x > e.home + e.patrol || e.x < e.home - e.patrol) {
        e.vx *= -1;
      }
      // Keep on ground
      e.y = GROUND_Y - e.h;

      // Player collision
      if (aabb(player, e) && player.invuln <= 0) {
        hurtPlayer();
      }

      // Projectile hits
      for (const p of projectiles) {
        if (aabb(p, e)) {
          e.hp -= 1;
          e.hitFlash = 0.15;
          p.life = 0;
          spawnBurst(e.x + e.w / 2, e.y + e.h / 2, "#ffaa22", 12);
          if (e.hp <= 0) {
            e.alive = false;
            antsDefeated += 1;
            score += 100;
            spawnBurst(e.x + e.w / 2, e.y + e.h / 2, "#ff4444", 20);
          }
        }
      }
    }

    // Particles
    for (const pt of particles) {
      pt.x += pt.vx;
      pt.y += pt.vy;
      pt.vy += 0.08;
      pt.life -= dt;
    }
    particles = particles.filter((pt) => pt.life > 0);

    // Win: reach finish line near world end
    const finishX = WORLD_W - 180;
    if (player.x + player.w >= finishX) {
      state = "won";
      score += Math.max(0, 500 - Math.floor(runTime) * 5);
      winStats.textContent = `Time ${runTime.toFixed(1)}s · Ants ${antsDefeated} · Score ${score}`;
      showPanel(winPanel);
    }
  }

  function drawBg() {
    const bg = sprites.bg;
    const parallax = cameraX * 0.35;
    const tileW = W;
    // Sky gradient
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#6eb6ef");
    g.addColorStop(0.55, "#a8d8f0");
    g.addColorStop(1, "#5cbf5a");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    if (bg) {
      const scale = H / bg.height;
      const drawW = bg.width * scale;
      let start = -((parallax * scale) % drawW);
      for (let x = start - drawW; x < W + drawW; x += drawW) {
        ctx.drawImage(bg, x, 0, drawW, H);
      }
    }

    // Ground strip (32-bit chunky)
    ctx.fillStyle = "#3d9a3a";
    ctx.fillRect(0, GROUND_Y, W, H - GROUND_Y);
    ctx.fillStyle = "#2f7a2e";
    for (let i = 0; i < W; i += 16) {
      const wx = Math.floor(cameraX + i);
      const h = 6 + ((wx * 7) % 10);
      ctx.fillRect(i, GROUND_Y, 12, h);
    }
    ctx.fillStyle = "#6b3f1f";
    ctx.fillRect(0, GROUND_Y + 28, W, H - GROUND_Y - 28);
    ctx.fillStyle = "#8a552c";
    for (let i = 0; i < W; i += 24) {
      ctx.fillRect(i, GROUND_Y + 34, 10, 4);
    }

    // Distance markers every screen
    ctx.save();
    ctx.translate(-cameraX, 0);
    for (let s = 1; s < SCREEN_COUNT; s++) {
      const x = s * W;
      ctx.strokeStyle = "rgba(255,255,255,0.25)";
      ctx.setLineDash([6, 8]);
      ctx.beginPath();
      ctx.moveTo(x, GROUND_Y - 120);
      ctx.lineTo(x, GROUND_Y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "rgba(255,255,255,0.55)";
      ctx.font = "10px 'Press Start 2P', monospace";
      ctx.fillText(`${s}/${SCREEN_COUNT}`, x + 8, GROUND_Y - 128);
    }
    ctx.restore();
  }

  function drawSprite(img, x, y, w, h, flip) {
    if (!img) return;
    ctx.save();
    if (flip) {
      ctx.translate(x + w, y);
      ctx.scale(-1, 1);
      ctx.drawImage(img, 0, 0, w, h);
    } else {
      ctx.drawImage(img, x, y, w, h);
    }
    ctx.restore();
  }

  function drawPlayer() {
    const screenX = player.x - cameraX;
    const screenY = player.y;
    let img = sprites.playerIdle;
    if (player.anim === "air") img = sprites.playerAir;
    else if (player.anim === "hop") img = sprites.playerHop;
    else if (player.anim === "run") {
      img = Math.floor(player.frameT * 8) % 2 === 0 ? sprites.playerIdle : sprites.playerHop;
    }

    if (player.invuln > 0 && Math.floor(player.invuln * 20) % 2 === 0) {
      ctx.globalAlpha = 0.45;
    }
    const flip = player.facing < 0;
    // Ants face left in art; player art faces right — flip when facing left
    drawSprite(img, screenX, screenY, player.w, player.h, flip);
    ctx.globalAlpha = 1;

    // Tiny gun muzzle glow when cooling down recently
    if (player.shootCD > FIRE_COOLDOWN - 80) {
      const mx = screenX + (player.facing > 0 ? player.w - 4 : 4);
      const my = screenY + player.h * 0.42;
      const rg = ctx.createRadialGradient(mx, my, 0, mx, my, 18);
      rg.addColorStop(0, "rgba(255,230,80,0.9)");
      rg.addColorStop(0.5, "rgba(255,60,20,0.5)");
      rg.addColorStop(1, "rgba(255,0,0,0)");
      ctx.fillStyle = rg;
      ctx.beginPath();
      ctx.arc(mx, my, 18, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function drawEnemies() {
    for (const e of enemies) {
      if (!e.alive) continue;
      const sx = e.x - cameraX;
      if (sx < -100 || sx > W + 100) continue;
      const walk = Math.floor(e.frameT * 6) % 2 === 0;
      const img = walk ? sprites.antWalk : sprites.antStand;
      if (e.hitFlash > 0) ctx.globalAlpha = 0.5;
      // Sprites face left; flip when moving right
      const flip = e.vx > 0;
      drawSprite(img, sx, e.y, e.w, e.h, flip);
      ctx.globalAlpha = 1;

      // HP pips
      ctx.fillStyle = "#111";
      ctx.fillRect(sx + 18, e.y - 8, 34, 5);
      ctx.fillStyle = "#e23";
      ctx.fillRect(sx + 18, e.y - 8, 17 * e.hp, 5);
    }
  }

  function drawFire(p) {
    const sx = p.x - cameraX;
    const sy = p.y;
    ctx.save();
    ctx.translate(sx + p.w / 2, sy + p.h / 2);
    if (p.vx < 0) ctx.scale(-1, 1);

    // Outer red glow
    const glow = ctx.createRadialGradient(4, 0, 2, 4, 0, 36);
    glow.addColorStop(0, "rgba(255,240,120,0.95)");
    glow.addColorStop(0.35, "rgba(255,170,30,0.85)");
    glow.addColorStop(0.65, "rgba(255,40,10,0.55)");
    glow.addColorStop(1, "rgba(180,0,0,0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.ellipse(0, 0, 34, 22, 0, 0, Math.PI * 2);
    ctx.fill();

    if (sprites.fireball) {
      ctx.drawImage(sprites.fireball, -30, -18, 60, 36);
    }

    // Bright yellow core
    ctx.fillStyle = "#ffe566";
    ctx.beginPath();
    ctx.ellipse(8, 0, 12, 8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ff2200";
    for (let i = 0; i < 4; i++) {
      const tx = -16 - i * 7 - Math.random() * 5;
      const ty = (Math.random() - 0.5) * 16;
      ctx.beginPath();
      ctx.moveTo(tx + 8, ty);
      ctx.lineTo(tx - 12, ty - 6);
      ctx.lineTo(tx - 8, ty + 6);
      ctx.fill();
      ctx.fillStyle = i % 2 ? "#ffee33" : "#ff2200";
    }
    ctx.restore();
  }

  function drawFinish() {
    const finishX = WORLD_W - 200;
    const sx = finishX - cameraX;
    if (sx > -120 && sx < W + 40) {
      if (sprites.finish) {
        ctx.drawImage(sprites.finish, sx, GROUND_Y - 160, 110, 160);
      } else {
        ctx.fillStyle = "#111";
        ctx.fillRect(sx + 48, GROUND_Y - 140, 8, 140);
        for (let r = 0; r < 5; r++) {
          for (let c = 0; c < 4; c++) {
            ctx.fillStyle = (r + c) % 2 === 0 ? "#fff" : "#111";
            ctx.fillRect(sx + 56 + c * 14, GROUND_Y - 140 + r * 16, 14, 16);
          }
        }
      }
      ctx.fillStyle = "#ffcc33";
      ctx.font = "12px 'Press Start 2P', monospace";
      ctx.fillText("FINISH", sx + 8, GROUND_Y - 170);
    }
  }

  function drawHUD() {
    // Progress across 10 screens
    const progress = Math.min(1, player.x / (WORLD_W - 200));
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillRect(12, 12, 220, 46);
    ctx.strokeStyle = "#ffcc33";
    ctx.lineWidth = 2;
    ctx.strokeRect(12, 12, 220, 46);

    ctx.fillStyle = "#9dcea8";
    ctx.font = "8px 'Press Start 2P', monospace";
    ctx.fillText("DISTANCE", 20, 28);
    ctx.fillStyle = "#234";
    ctx.fillRect(20, 36, 160, 10);
    ctx.fillStyle = "#3d9a3a";
    ctx.fillRect(20, 36, 160 * progress, 10);
    ctx.fillStyle = "#fff";
    ctx.fillText(`${Math.floor(progress * 10)}/10`, 188, 45);

    // HP
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillRect(W - 132, 12, 120, 34);
    ctx.strokeStyle = "#ff6644";
    ctx.strokeRect(W - 132, 12, 120, 34);
    ctx.fillStyle = "#ffaa99";
    ctx.font = "8px 'Press Start 2P', monospace";
    ctx.fillText("HP", W - 120, 28);
    for (let i = 0; i < MAX_HP; i++) {
      ctx.fillStyle = i < player.hp ? "#ff3b1f" : "#442222";
      ctx.fillRect(W - 120 + i * 28, 32, 22, 8);
    }

    // Score / ants
    ctx.fillStyle = "rgba(0,0,0,0.4)";
    ctx.fillRect(W / 2 - 90, 12, 180, 28);
    ctx.fillStyle = "#ffcc33";
    ctx.font = "8px 'Press Start 2P', monospace";
    ctx.textAlign = "center";
    ctx.fillText(`SCORE ${score}  ANTS ${antsDefeated}`, W / 2, 30);
    ctx.textAlign = "left";

    // Controls hint
    ctx.fillStyle = "rgba(255,255,255,0.55)";
    ctx.font = "7px 'Press Start 2P', monospace";
    ctx.fillText("SPACE jump   X fire", 14, H - 14);

    if (flash > 0) {
      ctx.fillStyle = `rgba(255,40,40,${flash * 0.45})`;
      ctx.fillRect(0, 0, W, H);
    }
  }

  function drawParticles() {
    for (const pt of particles) {
      const a = Math.max(0, pt.life / pt.max);
      ctx.globalAlpha = a;
      ctx.fillStyle = pt.color;
      ctx.fillRect(pt.x - cameraX, pt.y, pt.size, pt.size);
    }
    ctx.globalAlpha = 1;
  }

  function draw() {
    drawBg();
    drawFinish();
    drawEnemies();
    drawPlayer();
    for (const p of projectiles) drawFire(p);
    drawParticles();
    drawHUD();

    // Soft CRT scanlines for 32-bit flavor
    ctx.fillStyle = "rgba(0,0,0,0.08)";
    for (let y = 0; y < H; y += 3) {
      ctx.fillRect(0, y, W, 1);
    }
  }

  function loop(now) {
    rafId = 0;
    const dt = Math.min(0.033, (now - lastTime) / 1000 || 0.016);
    lastTime = now;
    if (state === "playing") update(dt);
    draw();
    if (state === "playing" || state === "paused" || state === "won" || state === "lost") {
      rafId = requestAnimationFrame(loop);
    }
  }

  // Input — use KeyboardEvent.code for layout-independent bindings
  const CONTROL_CODES = new Set([
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "Space",
    "KeyA",
    "KeyD",
    "KeyW",
    "KeyX",
    "KeyZ",
    "ControlLeft",
    "ControlRight",
  ]);

  window.addEventListener("keydown", (e) => {
    if (CONTROL_CODES.has(e.code) || e.code === "KeyP") {
      e.preventDefault();
    }
    keys.add(e.code);

    if (e.code === "KeyP") {
      if (state === "playing") {
        state = "paused";
        showPanel(pausePanel);
      } else if (state === "paused") {
        state = "playing";
        hideOverlay();
        lastTime = performance.now();
      }
    }
  });

  window.addEventListener("keyup", (e) => {
    keys.delete(e.code);
  });

  document.getElementById("btn-start").addEventListener("click", startPlaying);
  document.getElementById("btn-resume").addEventListener("click", () => {
    state = "playing";
    hideOverlay();
    lastTime = performance.now();
  });
  document.getElementById("btn-again").addEventListener("click", startPlaying);
  document.getElementById("btn-retry").addEventListener("click", startPlaying);

  // Boot
  loadAssets()
    .then(() => {
      resetGame();
      draw();
      showPanel(startPanel);
    })
    .catch((err) => {
      console.error(err);
      startPanel.querySelector("h2").textContent = "LOAD ERROR";
    });
})();
