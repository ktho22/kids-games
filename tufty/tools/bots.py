# Bots for the Tufty game under the CPython simulator (sim.py).
#   python3 bots.py monkey 20        random buttons, 40k frames per seed; reports crashes
#   python3 bots.py smart 1          plays a whole game to the ending; reports progress
import sys, random, traceback, json
sys.path.insert(0, __import__("os").path.dirname(__file__))
import sim


def tap(b, want):
  """Press `want` for one frame, releasing in between so every press is an edge."""
  if not want:
    return ()
  if want in b.prev:
    return ()
  return (want,)


# ------------------------------------------------------------ monkey

def monkey(ns, b):
  r = random.random()
  if r < 0.45:
    return tap(b, "B")
  if r < 0.6:
    return tap(b, "DOWN")
  if r < 0.7:
    return tap(b, "UP")
  if r < 0.8:
    return tap(b, "A")
  if r < 0.83:
    return tap(b, "C")
  return ()


# ------------------------------------------------------------ smart

log = []


def menu_go(b, menu, idx):
  if menu.cur == idx:
    return tap(b, "B")
  return tap(b, "DOWN" if (idx - menu.cur) % len(menu.items) <= len(menu.items) // 2 else "UP")


def find(menu, label):
  for i, it in enumerate(menu.items):
    if it[0] == label:
      return i
  return None


def story_strong(ns):
  """Is the team ready for the current story battle?"""
  s = ns["step"]()
  party = sorted(m["lv"] for m in ns["G"]["party"])[-3:]
  return sum(party) / len(party) >= max(lv for _, lv in s[6]) + 2


def smart(ns, b):
  G = ns.get("G")
  scene = ns.get("scene")
  if ns.get("task"):
    return tap(b, "B")              # skip messages
  if ns.get("confirm"):
    return tap(b, "B")
  if ns.get("notice"):
    log.append(ns["notice"])
    return tap(b, "B")
  if scene == "story":
    return tap(b, "B" if ns["story_ready"]() and story_strong(ns) else "A")
  if scene in ("title", "starter", "evolve", "win", "info", "talk"):
    if scene == "win" and "WIN" not in log:
      log.append("WIN")
      log.append("win at frame %d" % b.frames)
    return tap(b, "B")
  if scene == "battle":
    B = ns["B"]
    if B.menu == "main":
      my, e = ns["active"](), B.enemy
      want = 0
      if ns["catch_phase"]() and e["hp"] == 1:
        want = 1
      elif not B.trainer and e["id"] not in G["dex"] and G["balls"] > 0 \
          and (e["hp"] / ns["boss_max"](e) < 0.45 or my["lv"] > e["lv"] + 8) \
          and (len(G["party"]) < 6 or len(G["box"]) < 40):
        want = 1
      if B.mcur != want:
        return tap(b, "DOWN")
      return tap(b, "B")
    if B.menu == "fight":
      items = ns["fight_items"]()
      my, e = ns["active"](), B.enemy
      best, bi = -1, 0
      for i, (lab, _) in enumerate(items):
        if lab in ("MEGA!", "DYNAMAX!"):
          best, bi = 10 ** 9, i
          break
        t, pw, acc = ns["D"].MOVES[lab][:3]
        v = pw * acc * ns["type_mult"](t, ns["form"](e)[1])
        if v > best:
          best, bi = v, i
      if B.fcur != bi:
        return tap(b, "DOWN")
      return tap(b, "B")
    return tap(b, "B")
  if scene == "menu":
    stack = ns["stack"]
    top = stack[-1]
    if top.title and ("Who goes next" in top.title or "Switch" in top.title):
      return tap(b, "B")
    if getattr(top, "town", False):
      party = G["party"]
      lvls = sorted(m["lv"] for m in party)
      hurt = any(m["hp"] < ns["max_hp"](m) * 0.6 for m in party)
      if hurt:
        return menu_go(b, top, find(top, "Pokemon Center"))
      nb = len(G["badges"])
      if G["story"] >= int(__import__("os").environ.get("BOT_STORY_END", 20)):
        if "DONE" not in log:
          log.append("story done at frame %d" % b.frames)
        log.append("DONE")
        return ()
      if ns["story_ready"]() and story_strong(ns):
        return menu_go(b, top, find(top, "Story"))
      # team: keep the 6 strongest, rest go to the box (strongest leads)
      lead = party[0]
      if lead is not max(party, key=lambda m: m["lv"]):
        return menu_go(b, top, find(top, "Team"))
      top3 = sorted(lvls)[-3:]
      avg = sum(top3) / len(top3)
      D = ns["D"]
      if nb < 5:
        cave = D.CAVES[nb]
        need = max(l for _, l in cave[3]) + 2
        if ns["cave_open"](nb) and avg >= need:
          b.goal = ("cave", nb)
          return menu_go(b, top, find(top, "Caves"))
      elif not G["bossCaught"] and ns["cave_open"](5) and avg >= ns["D"].MEWTWO_LV + 2:
        b.goal = ("cave", 5)
        return menu_go(b, top, find(top, "Caves"))
      # train: the toughest open land that is still beatable; while the
      # story wants more kinds, the beatable land with most still to catch
      best = 0
      for i, a in enumerate(D.AREAS):
        if nb >= a[3] and a[2] <= avg + 1:
          best = i
      s = ns["step"]()
      if s and s[0] == "goal" and s[1][0] == "dex" and not ns["cond_met"](s[1]):
        def missing(a):
          return len([p for p in a[4] if p not in G["dex"]])
        open_ = [i for i, a in enumerate(D.AREAS) if nb >= a[3] and a[1] <= avg]
        if open_:
          best = max(open_, key=lambda i: (missing(D.AREAS[i]), i))
      b.goal = ("area", best)
      return menu_go(b, top, find(top, "Explore"))
    goal = getattr(b, "goal", None)
    if top.title and top.title.startswith("Team"):
      party = ns["G"]["party"]
      i = party.index(max(party, key=lambda m: m["lv"]))
      if i == 0:
        return tap(b, "A")
      return menu_go(b, top, i)
    if top.items and top.items[0][0] == "Lead the team":
      return menu_go(b, top, 0)
    if goal and top.title and top.title.startswith("Explore"):
      return menu_go(b, top, goal[1])
    if goal and top.title and top.title.startswith("Caves"):
      return menu_go(b, top, goal[1])
    return tap(b, "A")
  return tap(b, "B")


if __name__ == "__main__":
  mode = sys.argv[1]
  if mode == "monkey":
    bad = 0
    for seed in range(int(sys.argv[2])):
      sim.store.clear()
      if seed % 3 == 1:
        # start from a strong late-game save so the endgame paths get poked too
        party = [{"id": i, "lv": 48, "exp": 0, "hp": 999, "uid": "x%d" % n} for n, i in
                 enumerate(("rizamong", "garados", "ditto", "eevee", "pikachu", "mewtwoX"))]
        box = [{"id": "gugu", "lv": 3, "exp": 0, "hp": 1, "uid": "b%d" % n} for n in range(39)]
        sim.store["pocket_mini_adventure"] = json.dumps({"party": party, "box": box, "balls": 9, "dex": ["rizamong", "gugu"],
                                                         "badges": ["rock", "ice", "fire", "ghost", "dragon"], "masterBall": seed % 2 == 0, "bossCaught": False})
      try:
        ns = sim.play(monkey, 40000, seed)
        print("seed", seed, "frames", sim.badge.frames, "scene", ns.get("scene"), "quits", getattr(sim.play, "exits", 0))
      except Exception:
        bad += 1
        print("seed", seed)
        traceback.print_exc()
        if bad > 3:
          break
    print("monkey done, crashes:", bad)
  else:
    seed = int(sys.argv[2])
    sim.store.clear()
    sim.badge.goal = None
    log.clear()
    ns = None
    frames = int(sys.argv[3]) if len(sys.argv) > 3 else 600000
    def hook():
      pass
    try:
      ns = sim.play(smart, frames, seed)
    except Exception:
      traceback.print_exc()
    g = json.loads(sim.store.get("pocket_mini_adventure", "{}"))
    print("frames", sim.badge.frames, "minutes at 60fps ~", round(sim.badge.frames / 60 / 60, 1))
    print("story", g.get("story"), "badges", g.get("badges"), "boss", g.get("bossCaught"), "dex", len(g.get("dex", [])),
          "team", [(m["id"], m["lv"]) for m in g.get("party", [])])
    notes = [l for l in log if "badge" in l or "WIN" in l or "Champion" in l or "frame" in l or "goal" in l]
    print("\n".join(dict.fromkeys(notes)))
