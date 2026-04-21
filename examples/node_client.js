const BASE_URL = "http://127.0.0.1:8000";
const API_KEY = "";

async function post(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
    },
    body: JSON.stringify(body),
  });
  return await res.json();
}

async function main() {
  const state = {
    agent_id: "bot_node_001",
    tick: 1,
    state: {
      hp: 70,
      mp: 25,
      x: 320,
      y: 180,
      map_id: 1,
      heading: 2,
      target_id: "mob_3",
      target_distance: 2,
      target_hp: 80,
      is_under_attack: false,
      nearby_enemies: 1,
      nearby_allies: 0,
      safe_zone: false,
      can_teleport: false,
      weight_percent: 30,
      cooldowns: { heal: 0 },
      inventory: { potion: 1 },
      buffs: [],
      debuffs: [],
      aggro_targets: [],
      extras: {},
    },
  };

  console.log(await post("/observe", state));
  console.log(await post("/decide", state));
}

main();
