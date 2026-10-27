"""
Catch Pokemon, win all five cave badges, beat the Champion and catch Mega
Mewtwo X. The Tufty edition of Pocket Mini Adventure.

Controls:
* Up / Down = Choose
* B = OK / next message
* A = Back
* Hold Up + Down = Save and back to the launcher

The rules, numbers and Pokemon all come from the web version (pkdata.py is
generated from it), so both play the same. The story (story.py) is the
badge's own: a rival, Team Grumble, and goals that lead to the Champion.
"""

import math
import random

from badgeware import State

import pkdata as D
import story as ST


badge.mode(LORES | VSYNC)

APP = "/system/apps/pocket_mini_adventure"
MENU = "/system/apps/menu"
SAVE = "pocket_mini_adventure"
SLOTS = 5
W, H = 160, 120

# how long battle messages stay up, relative to the web game; B skips ahead
PACE = 1.4

# species tuple fields (see pkdata.py)
NAME, TYPE, HP, ATK, DEF, SPD, EVLV, EVTO, MV, STAGE = range(10)

STARTERS = ("pairi", "kkobugi", "isanghae")

BODY = font.nope        # 13px: names, menus
SMALL = font.yolk       # 11px: messages
TINY = font.desert      # 10px: tags and numbers
TITLE = font.smart

INK = color.rgb(34, 32, 52)
PAPER = color.rgb(250, 248, 240)
PANEL = color.rgb(255, 255, 255)
SHADE = color.rgb(214, 220, 232)
MUTED = color.rgb(120, 128, 150)
FAINT = color.rgb(176, 182, 198)
WHITE = color.rgb(255, 255, 255)
RED = color.rgb(232, 64, 64)
GREEN = color.rgb(72, 196, 96)
YELLOW = color.rgb(250, 200, 50)
BLUE = color.rgb(70, 120, 230)
PURPLE = color.rgb(150, 90, 230)
GOLD = color.rgb(240, 180, 40)
HILITE = color.rgb(255, 236, 160)

TYPE_COLOR = {
  "Fire": color.rgb(240, 128, 48), "Water": color.rgb(90, 140, 240),
  "Grass": color.rgb(100, 190, 70), "Electric": color.rgb(240, 196, 30),
  "Normal": color.rgb(160, 160, 120), "Flying": color.rgb(150, 130, 240),
  "Psychic": color.rgb(240, 80, 130), "Rock": color.rgb(184, 160, 56),
  "Ghost": color.rgb(112, 88, 152), "Dragon": color.rgb(112, 56, 248),
  "Fighting": color.rgb(192, 48, 40),
}

STATUS = {
  "brn": ("BRN", color.rgb(240, 110, 40), "got burned!"),
  "psn": ("PSN", color.rgb(160, 70, 170), "got poisoned!"),
  "par": ("PAR", color.rgb(230, 190, 20), "got all zappy and stiff!"),
  "slp": ("SLP", color.rgb(120, 130, 160), "fell fast asleep!"),
}

# each land gets its own sky and ground behind the battle
AREA_BG = (
  (color.rgb(170, 220, 250), color.rgb(120, 200, 100)),   # Grass
  (color.rgb(250, 214, 236), color.rgb(150, 210, 120)),   # Flower Woods
  (color.rgb(150, 210, 250), color.rgb(240, 220, 150)),   # Beach
  (color.rgb(90, 110, 100), color.rgb(50, 90, 60)),       # Dark Forest
  (color.rgb(150, 170, 140), color.rgb(100, 120, 80)),    # Swamp
  (color.rgb(180, 200, 220), color.rgb(160, 140, 110)),   # Mountain
  (color.rgb(220, 236, 250), color.rgb(240, 248, 255)),   # Snowy Peak
  (color.rgb(120, 60, 50), color.rgb(90, 50, 40)),        # Volcano
)
CAVE_BG = (color.rgb(80, 70, 90), color.rgb(120, 100, 90))
LEGEND_BG = (color.rgb(50, 30, 80), color.rgb(110, 60, 140))
PLAZA_BG = (color.rgb(250, 220, 170), color.rgb(210, 170, 120))


# ---------------------------------------------------------------- helpers

def rand(n):
  return int(random.random() * n) if n > 0 else 0


def rnd(x):
  """Math.round, which rounds halves up (Python's round goes to even)."""
  return int(math.floor(x + 0.5))


def rid():
  return "%x%x" % (badge.ticks, rand(0xFFFFFF))


def sp(m):
  return D.SPECIES[m["id"]]


def form(m):
  """The shape a Pokemon fights as: its own, or a transformed Ditto's copy."""
  tf = m.get("tf")
  return D.SPECIES[tf] if tf and tf in D.SPECIES else D.SPECIES[m["id"]]


def max_hp(m):
  return D.SPECIES[m["id"]][HP] * m["lv"] // 50 + m["lv"] + 10


def atk_of(m):
  return form(m)[ATK] * m["lv"] // 50 + 5


def def_of(m):
  d = form(m)[DEF] * m["lv"] // 50 + 5
  return rnd(d * 1.3) if m.get("mega") else d


def exp_need(m):
  return m["lv"] * 12 + m["lv"] * m["lv"] // 4


def new_mon(i, lv):
  m = {"id": i, "lv": lv, "exp": 0, "hp": 0, "uid": rid()}
  m["hp"] = max_hp(m)
  return m


def boss_max(m):
  return m.get("bossMaxHp") or max_hp(m)


def label(m):
  if m.get("mega") and m["id"] in D.MEGA and not m.get("tf"):
    return D.MEGA[m["id"]]
  if m.get("gmax"):
    return "G-Max " + form(m)[NAME]
  return form(m)[NAME]


def sprite_key(m):
  if m.get("mega") and m["id"] in D.MEGA and not m.get("tf"):
    return m["id"] + "_mega"
  return m.get("tf") or m["id"]


def type_mult(mt, dt):
  strong, weak, barely = D.TYPES[mt]
  if dt in barely:
    return 0.4
  if dt in strong:
    return 1.5
  if dt in weak:
    return 0.7
  return 1


def calc_damage(att, dfn, pw, f):
  base = ((2 * att["lv"] / 5 + 2) * 45 * pw * atk_of(att) / def_of(dfn)) / 50 + 2
  return max(1, rnd(base * (0.85 + random.random() * 0.15) * f))


def clear_status(m):
  m.pop("st", None)
  m.pop("stT", None)


def apply_status(m, st):
  if st not in STATUS or m.get("st"):
    return False
  if st == "brn" and form(m)[TYPE] == "Fire":
    return False
  m["st"] = st
  if st == "slp":
    m["stT"] = 2 + rand(2)
  return True


# ---------------------------------------------------------------- save

G = None


def sanitize(g):
  if not g or not g.get("party"):
    return None
  g["party"] = [m for m in g["party"] if m and m.get("id") in D.SPECIES][:6]
  g["box"] = [m for m in (g.get("box") or []) if m and m.get("id") in D.SPECIES][:D.BOX_MAX]
  g["dex"] = [i for i in (g.get("dex") or []) if i in D.SPECIES]
  g["badges"] = list(g.get("badges") or [])
  g.setdefault("balls", 5)
  g.setdefault("masterBall", False)
  g.setdefault("bossCaught", False)
  if not g["party"]:
    return None
  # saves from before the story pick it up where their badges leave off
  if not isinstance(g.get("story"), int):
    if g["bossCaught"]:
      g["story"] = ST.RESUME_AFTER_BOSS
    else:
      g["story"] = ST.RESUME_AT_BADGES[min(5, len(g["badges"]))]
  if g.get("rival") not in D.SPECIES:
    mine = [i for i in g["dex"] if i in ST.RIVAL_OF]
    g["rival"] = ST.RIVAL_OF[mine[0]] if mine else "pairi"
  for m in g["party"] + g["box"]:
    for k in ("mega", "gmax", "tf", "st", "stT", "bossMaxHp"):
      m.pop(k, None)
    m["lv"] = max(1, min(100, int(m.get("lv") or 1)))
    m["exp"] = max(0, int(m.get("exp") or 0))
    mh = max_hp(m)
    hp = m.get("hp")
    m["hp"] = mh if hp is None else max(0, min(mh, int(hp)))
    m.setdefault("uid", rid())
  for m in g["box"]:
    m["hp"] = max_hp(m)
  return g


SLOT = 1


def slot_key(n):
  """Slot 1 keeps the original name, so saves from before slots still load."""
  return SAVE if n == 1 else "%s_%d" % (SAVE, n)


def load_slot(n):
  g = {}
  try:
    State.load(slot_key(n), g)
  except Exception:
    return None
  return sanitize(g)


def save():
  if G:
    State.save(slot_key(SLOT), G)


def last_slot():
  meta = {"last": 1}
  try:
    State.load(SAVE + "_meta", meta)
  except Exception:
    pass
  return meta["last"] if 1 <= meta.get("last", 1) <= SLOTS else 1


def active():
  for m in G["party"]:
    if m["hp"] > 0:
      return m
  return G["party"][0]


def rest_box():
  for m in G["box"]:
    m["hp"] = max_hp(m)
    clear_status(m)


# ---------------------------------------------------------------- sprites

_sprites = {}


def sprite(key):
  if key in _sprites:
    return _sprites[key]
  if len(_sprites) > 40:
    _sprites.clear()
  try:
    img = image.load("%s/sprites/%s.png" % (APP, key))
  except OSError:
    img = None
  _sprites[key] = img
  return img


def flipped(key):
  """The sprite facing the other way, built once a column at a time."""
  fkey = key + "<"
  if fkey in _sprites:
    return _sprites[fkey]
  src = sprite(key)
  img = None
  if src:
    img = image(48, 48)
    img.pen = color.rgb(0, 0, 0, 0)
    img.clear()
    for x in range(48):
      img.blit(src, rect(x, 0, 1, 48), rect(47 - x, 0, 1, 48))
  _sprites[fkey] = img
  return img


def draw_sprite(key, x, y, size=48, flip=False):
  img = flipped(key) if flip else sprite(key)
  if not img:
    return
  x, y = int(x), int(y)
  if size == 48:
    screen.blit(img, x, y)
  else:
    screen.blit(img, rect(0, 0, 48, 48), rect(x, y, size, size))


# ---------------------------------------------------------------- drawing

def text(s, x, y, pen=INK, face=BODY):
  screen.font = face
  screen.pen = pen
  screen.text(s, int(x), int(y))


def width_of(s, face=BODY):
  screen.font = face
  return screen.measure_text(s)[0]


def text_fit(s, x, y, maxw, pen=INK, face=BODY):
  """Draw in `face`, dropping to the smaller fonts when it would not fit."""
  for f in (face, SMALL, TINY):
    if width_of(s, f) <= maxw:
      text(s, x, y, pen, f)
      return
  text(s, x, y, pen, TINY)


def text_right(s, right, y, pen=INK, face=BODY):
  text(s, right - width_of(s, face), y, pen, face)


def text_center(s, y, pen=INK, face=BODY, cx=W / 2, maxw=None):
  if maxw:
    for f in (face, SMALL, TINY):
      if width_of(s, f) <= maxw:
        face = f
        break
    else:
      face = TINY
  text(s, cx - width_of(s, face) / 2, y, pen, face)


_wrap_cache = {}


def wrap(s, face, maxw):
  key = (s, id(face), maxw)
  if key in _wrap_cache:
    return _wrap_cache[key]
  if len(_wrap_cache) > 30:
    _wrap_cache.clear()
  lines = []
  for para in s.split("\n"):
    line = ""
    for word in para.split():
      cand = word if not line else line + " " + word
      if not line or width_of(cand, face) <= maxw:
        line = cand
      else:
        lines.append(line)
        line = word
    lines.append(line)
  _wrap_cache[key] = lines
  return lines


def box(x, y, w, h, fill=PANEL, edge=INK, r=3):
  screen.pen = edge
  screen.shape(shape.rounded_rectangle(x, y, w, h, r))
  screen.pen = fill
  screen.shape(shape.rounded_rectangle(x + 1, y + 1, w - 2, h - 2, max(0, r - 1)))


def hp_bar(x, y, w, hp, mx, h=4):
  k = max(0, min(1, hp / mx)) if mx else 0
  screen.pen = SHADE
  screen.rectangle(x, y, w, h)
  screen.pen = GREEN if k > 0.5 else YELLOW if k > 0.25 else RED
  if hp > 0:
    screen.rectangle(x, y, max(1, int(w * k)), h)


def type_tag(t, x, y):
  wd = width_of(t, TINY) + 4
  screen.pen = TYPE_COLOR[t]
  screen.shape(shape.rounded_rectangle(x, y, wd, 9, 2))
  text(t, x + 2, y, WHITE, TINY)
  return wd


def status_tag(m, x, y):
  st = m.get("st")
  if st not in STATUS:
    return 0
  name, pen, _ = STATUS[st]
  wd = width_of(name, TINY) + 4
  screen.pen = pen
  screen.shape(shape.rounded_rectangle(x, y, wd, 9, 2))
  text(name, x + 2, y, WHITE, TINY)
  return wd


def ball_icon(x, y, r=3, master=False):
  x, y = int(x), int(y)
  screen.pen = INK
  screen.shape(shape.circle(x, y, r + 1))
  screen.pen = PURPLE if master else RED
  screen.shape(shape.circle(x, y, r))
  # the lower half is white: the same circle again, clipped to that half
  was = screen.clip
  screen.clip = rect(x - r - 1, y, r * 2 + 3, r + 2)
  screen.pen = WHITE
  screen.shape(shape.circle(x, y, r))
  screen.clip = was
  screen.pen = INK
  screen.rectangle(x - r, y, r * 2 + 1, 1)


def badge_icon(x, y, got=True):
  screen.pen = GOLD if got else FAINT
  screen.shape(shape.star(x, y, 5, 2, 4.5))


def message_box(s, y=84, h=36):
  box(1, y, W - 2, h)
  for n, line in enumerate(wrap(s, SMALL, W - 10)[:3]):
    text(line, 5, y + 1 + n * 11, INK, SMALL)


# ---------------------------------------------------------------- input

repeat_at = {}


def repeat(button):
  now = badge.ticks
  if badge.pressed(button):
    repeat_at[button] = now + 300
    return True
  if badge.held(button) and now >= repeat_at.get(button, now + 1):
    repeat_at[button] = now + 90
    return True
  return False


def ok():
  return badge.pressed(BUTTON_B)


def back():
  return badge.pressed(BUTTON_A)


# ---------------------------------------------------------------- tasks
# Battle flow is written as generators: each `yield` hands one frame back to
# the main loop, so messages and effects play out while the screen redraws.

task = None


def run(gen):
  global task
  task = gen


def wait(ms, skip=True):
  end = badge.ticks + ms * PACE
  yield
  while badge.ticks < end:
    if skip and ok():
      return
    yield


def pause(ms):
  end = badge.ticks + ms
  while badge.ticks < end:
    yield


# ---------------------------------------------------------------- menus

class Menu:
  """A scrolling list. Each item is [label, right, enabled, action]."""

  def __init__(self, title, items, on_back=None, row_h=13, draw_row=None, top=16, footer=None):
    self.title = title
    self.items = items
    self.on_back = on_back
    self.row_h = row_h
    self.draw_row = draw_row
    self.top = top
    self.footer = footer
    self.cur = 0
    self.scroll = 0

  def visible(self):
    bottom = H - (12 if self.footer else 0)
    return max(1, (bottom - self.top) // self.row_h)

  def update(self):
    n = len(self.items)
    if n and repeat(BUTTON_DOWN):
      self.cur = (self.cur + 1) % n
    if n and repeat(BUTTON_UP):
      self.cur = (self.cur - 1) % n
    vis = self.visible()
    if self.cur < self.scroll:
      self.scroll = self.cur
    if self.cur >= self.scroll + vis:
      self.scroll = self.cur - vis + 1
    if ok() and n:
      item = self.items[self.cur]
      if item[3]:
        item[3]()
    elif back() and self.on_back:
      self.on_back()

  def draw(self):
    screen.pen = PAPER
    screen.clear()
    if self.title:
      screen.pen = INK
      screen.rectangle(0, 0, W, 14)
      text_fit(self.title, 4, 0, W - 8, WHITE)
    vis = self.visible()
    for k in range(self.scroll, min(len(self.items), self.scroll + vis)):
      y = self.top + (k - self.scroll) * self.row_h
      sel = k == self.cur
      if sel:
        screen.pen = HILITE
        screen.rectangle(0, y, W, self.row_h)
      item = self.items[k]
      if self.draw_row:
        self.draw_row(item, y, sel)
      else:
        pen = INK if item[2] else FAINT
        room = W - 6 - (width_of(item[1], SMALL) + 6 if item[1] else 0)
        text_fit(("> " if sel else "  ") + item[0], 2, y, room, pen)
        if item[1]:
          text_right(item[1], W - 3, y + 1, MUTED if item[2] else FAINT, SMALL)
    # scroll hints
    if self.scroll > 0:
      screen.pen = MUTED
      screen.triangle(W - 6, self.top + 1, W - 9, self.top + 4, W - 3, self.top + 4)
    if self.scroll + vis < len(self.items):
      screen.pen = MUTED
      yb = self.top + vis * self.row_h - 2
      screen.triangle(W - 6, yb, W - 9, yb - 3, W - 3, yb - 3)
    if self.footer:
      screen.pen = SHADE
      screen.rectangle(0, H - 12, W, 12)
      text(self.footer, 3, H - 11, MUTED, TINY)


stack = []          # open menus, top one drawn
scene = "title"
notice = None       # a message waiting to be read on top of the menus
confirm = None      # (question, on_yes)


def push(menu):
  stack.append(menu)


def pop():
  if stack:
    stack.pop()


def say_notice(msg):
  global notice
  notice = msg


def ask(question, on_yes):
  global confirm
  confirm = (question, on_yes)


# ---------------------------------------------------------------- town

def badge_count():
  return len(G["badges"])


def cave_open(i):
  """Caves open as the story reaches them; one already won stays open. 5 = Legend Cave."""
  if i < len(D.CAVES) and D.CAVES[i][1] in G["badges"]:
    return True
  return G["story"] >= ST.CAVE_OPENS_AT[i]


def go_town(msg=None, check=True):
  global scene, notice
  scene = "menu"
  stack.clear()
  push(town_menu())
  if msg:
    say_notice(msg)
  # a story scene that is due takes over from the message
  if check and story_check():
    notice = None


def town_menu():
  items = [
    ["Story", story_label(), True, open_story],
    ["Explore", "", True, lambda: push(area_menu())],
    ["Caves", "%d/5" % badge_count(), True, lambda: push(cave_menu())],
    ["Pokemon Center", "", True, heal_all],
    ["Team", "%d/6" % len(G["party"]), True, lambda: push(team_menu())],
    ["Box", "%d/%d" % (len(G["box"]), D.BOX_MAX), True, lambda: push(box_menu())],
    ["Pokedex", "%d/%d" % (len(G["dex"]), len(D.ORDER)), True, lambda: push(dex_menu())],
    ["Battle Plaza", "" if badge_count() >= 1 else "1 badge", badge_count() >= 1, go_plaza],
    ["Save Slots", "%d" % SLOT, True, lambda: (save(), go_title())],
    ["Save & Quit", "", True, quit_game],
  ]
  m = Menu(None, items, top=44)
  m.town = True
  return m


def draw_town_header():
  screen.pen = INK
  screen.rectangle(0, 0, W, 14)
  text("Town", 4, 0, WHITE)
  x = W - 4
  s = "x%d" % G["balls"]
  x -= width_of(s, SMALL)
  text(s, x, 2, WHITE, SMALL)
  ball_icon(x - 5, 7)
  x -= 16
  s = "%d/5" % badge_count()
  x -= width_of(s, SMALL)
  text(s, x, 2, WHITE, SMALL)
  badge_icon(x - 6, 7)
  # the lead Pokemon
  a = active()
  screen.pen = SHADE
  screen.rectangle(0, 14, W, 28)
  draw_sprite(a["id"], 2, 15, 26)
  s = sp(a)
  text_fit(s[NAME], 32, 15, 74, INK)
  type_tag(s[TYPE], 32, 30)
  text_right("Lv.%d" % a["lv"], W - 4, 15, INK, SMALL)
  hp_bar(W - 52, 29, 48, a["hp"], max_hp(a))
  text_right("%d/%d" % (a["hp"], max_hp(a)), W - 4, 32, MUTED, TINY)


def refresh_town():
  """Rebuild the town menu so its counts are current, keeping the cursor."""
  if stack and getattr(stack[0], "town", False):
    cur = stack[0].cur
    stack[0] = town_menu()
    stack[0].cur = cur


def area_menu():
  items = []
  for i, a in enumerate(D.AREAS):
    open_ = badge_count() >= a[3]
    right = "Lv.%d-%d" % (a[1], a[2]) if open_ else "%d badge%s" % (a[3], "s" if a[3] > 1 else "")
    items.append([a[0], right, open_, (lambda i=i: go_area(i)) if open_ else
                  (lambda a=a: say_notice("Win %d badge%s to open %s!" % (a[3], "s" if a[3] > 1 else "", a[0])))])
  return Menu("Explore - where to?", items, on_back=pop)


def cave_menu():
  items = []
  for i, c in enumerate(D.CAVES):
    open_ = cave_open(i)
    done = c[1] in G["badges"]
    right = "BADGE" if done else ("" if open_ else "locked")
    items.append([c[0], right, open_, (lambda i=i: go_cave(i)) if open_ else story_first])
  boss_open = cave_open(5)
  items.append(["Legend Cave", "BEATEN" if G["bossCaught"] else ("" if boss_open else "locked"), boss_open,
                go_boss if boss_open else story_first])
  return Menu("Caves - %d/5 badges" % badge_count(), items, on_back=pop)


def heal_all():
  run(heal_task())


def heal_task():
  global scene
  scene = "heal"
  yield from pause(1600)
  for m in G["party"] + G["box"]:
    m["hp"] = max_hp(m)
    clear_status(m)
  G["balls"] = max(G["balls"], 5)
  save()
  scene = "menu"
  refresh_town()
  say_notice("All better! Burns, poison, everything gone! Poke Balls are full too!")


def quit_game():
  global exit_to
  save()
  exit_to = MENU


# ---------------------------------------------------------------- team / box / dex

def mon_row(m, y, sel, right=None):
  s = sp(m)
  draw_sprite(m["id"], 2, y + 1, 24)
  text_fit(s[NAME], 28, y, 80, INK if m["hp"] > 0 else MUTED)
  x = 28 + type_tag(s[TYPE], 28, y + 14) + 2
  status_tag(m, x, y + 14)
  text_right("Lv.%d" % m["lv"], W - 4, y, INK, SMALL)
  if right:
    text_right(right, W - 4, y + 14, MUTED, TINY)
  else:
    hp_bar(W - 48, y + 15, 44, m["hp"], max_hp(m))


def team_menu():
  items = [[None, m, True, (lambda i=i: push(team_actions(i)))] for i, m in enumerate(G["party"])]
  return Menu("Team %d/6 - top one battles" % len(G["party"]), items, on_back=lambda: (pop(), refresh_town()),
              row_h=26, draw_row=lambda it, y, sel: mon_row(it[1], y, sel))


def reopen(menu_fn, msg=None):
  pop()
  pop()
  push(menu_fn())
  if msg:
    say_notice(msg)


def team_actions(i):
  m = G["party"][i]
  name = sp(m)[NAME]

  def lead():
    G["party"].insert(0, G["party"].pop(i))
    save()
    reopen(team_menu, "%s leads the team now!" % name)

  def to_box():
    if len(G["party"]) <= 1:
      return say_notice("You need at least 1 Pokemon on your team!")
    if len(G["box"]) >= D.BOX_MAX:
      return say_notice("The Box is full!")
    G["party"].pop(i)
    clear_status(m)
    m["hp"] = max_hp(m)
    G["box"].append(m)
    save()
    reopen(team_menu, "%s is resting in the Box - all healed up!" % name)

  def bye():
    if len(G["party"]) <= 1:
      return say_notice("You need at least 1 Pokemon!")

    def yes():
      G["party"].remove(m)
      G["balls"] += 1
      save()
      reopen(team_menu, "%s waved bye-bye! It left a Poke Ball for you! +1" % name)
    ask("Say bye-bye to %s? It goes back to the wild." % name, yes)

  items = [
    ["Lead the team", "", i > 0, lead if i > 0 else None],
    ["Info & moves", "", True, lambda: show_info(m)],
    ["Rest in the Box", "", len(G["party"]) > 1, to_box],
    ["Say bye-bye", "", len(G["party"]) > 1, bye],
  ]
  return Menu(name, items, on_back=pop)


def box_menu():
  items = [[None, m, True, (lambda i=i: push(box_actions(i)))] for i, m in enumerate(G["box"])]
  menu = Menu("Box %d/%d - always healthy" % (len(G["box"]), D.BOX_MAX), items,
              on_back=lambda: (pop(), refresh_town()), row_h=26, draw_row=lambda it, y, sel: mon_row(it[1], y, sel))
  if not items:
    menu.items = [["The Box is empty!", "", False, None]]
    menu.draw_row = None
    menu.row_h = 13
  return menu


def box_actions(i):
  m = G["box"][i]
  name = sp(m)[NAME]

  def join():
    if len(G["party"]) >= 6:
      return say_notice("Your team is full! Send someone to the Box first.")
    G["box"].pop(i)
    m["hp"] = max_hp(m)
    G["party"].append(m)
    save()
    reopen(box_menu, "%s joined your team!" % name)

  def bye():
    def yes():
      G["box"].remove(m)
      G["balls"] += 1
      save()
      reopen(box_menu, "%s waved bye-bye! It left a Poke Ball for you! +1" % name)
    ask("Say bye-bye to %s? It goes back to the wild." % name, yes)

  return Menu(name, [
    ["Join the team", "%d/6" % len(G["party"]), len(G["party"]) < 6, join],
    ["Info & moves", "", True, lambda: show_info(m)],
    ["Say bye-bye", "", True, bye],
  ], on_back=pop)


def dex_row(item, y, sel):
  i = item[1]
  n = D.ORDER.index(i) + 1
  got = i in G["dex"]
  text("#%03d" % n, 3, y + 7, MUTED, TINY)
  if got:
    draw_sprite(i, 26, y + 1, 24)
    s = D.SPECIES[i]
    text_fit(s[NAME], 54, y, 70, INK)
    type_tag(s[TYPE], 54, y + 14)
    if i in D.LEGENDS or i == "mewtwoX":
      text_right("LEGEND", W - 4, y + 14, GOLD, TINY)
  else:
    screen.pen = SHADE
    screen.shape(shape.circle(38, y + 13, 9))
    text("?", 36, y + 7, MUTED, SMALL)
    text("?????", 54, y + 6, FAINT)


def dex_menu():
  items = [[None, i, True, None] for i in D.ORDER]
  return Menu("Pokedex %d/%d" % (len(G["dex"]), len(D.ORDER)), items, on_back=pop, row_h=26, draw_row=dex_row)


info_mon = None


def show_info(m):
  global scene, info_mon
  info_mon = m
  scene = "info"


def draw_info():
  m = info_mon
  s = sp(m)
  screen.pen = PAPER
  screen.clear()
  screen.pen = TYPE_COLOR[s[TYPE]]
  screen.rectangle(0, 0, W, 52)
  draw_sprite(m["id"], 4, 2)
  text_fit(s[NAME], 56, 2, 100, WHITE)
  text("Lv.%d  #%03d" % (m["lv"], D.ORDER.index(m["id"]) + 1), 56, 16, WHITE, SMALL)
  text("HP %d/%d" % (m["hp"], max_hp(m)), 56, 28, WHITE, SMALL)
  text("Exp %d/%d" % (m["exp"], exp_need(m)), 56, 39, WHITE, SMALL)
  text("Atk %d  Def %d  Spd %d" % (atk_of(m), def_of(m), s[SPD]), 4, 54, INK, SMALL)
  for n, name in enumerate(s[MV]):
    t = D.MOVES[name]
    y = 67 + n * 11
    screen.pen = TYPE_COLOR[t[0]]
    screen.rectangle(4, y + 2, 6, 7)
    text(name, 13, y, INK, SMALL)
    text_right(t[0], W - 4, y + 1, MUTED, TINY)
  if s[EVLV]:
    to = s[EVTO]
    text("Evolves at Lv.%d" % s[EVLV] if isinstance(to, str) else "Evolves at Lv.%d (surprise!)" % s[EVLV],
         4, 110, MUTED, TINY)


# ---------------------------------------------------------------- battle state

class Battle:
  def __init__(self, enemy, trainer=None, cave=None, legend=False, plaza=False, queue=None, bg=None):
    self.enemy = enemy
    self.trainer = trainer       # the trainer's name, None in the wild
    self.cave = cave             # index into D.CAVES
    self.legend = legend
    self.plaza = plaza
    self.queue = queue or []
    self.power_used = False
    self.over = False
    self.gauge = 0
    self.enemy_mega = False
    self.forced = False
    self.msg = ""
    self.menu = "msg"            # msg | main | fight
    self.mcur = 0                # main menu choice, kept between turns
    self.fcur = 0
    self.bg = bg or AREA_BG[0]
    self.story = None            # the story step this battle belongs to


B = None
fx = {}             # live effects: name -> (start, length, data)


def effect(name, ms, data=None):
  fx[name] = (badge.ticks, ms, data)


def effect_part(name):
  e = fx.get(name)
  if not e:
    return None
  k = (badge.ticks - e[0]) / e[1]
  if k >= 1:
    del fx[name]
    return None
  return k


def catch_phase():
  return B.legend and B.enemy["id"] == "mewtwoX" and not G["bossCaught"]


def power_unlocked():
  return badge_count() >= 3


def can_mega():
  if B.over or B.power_used or B.gauge < D.GAUGE_MAX:
    return False
  my = active()
  return badge_count() >= 3 and my["id"] in D.MEGA and not my.get("tf") and not my.get("mega") and not my.get("gmax")


def can_gmax():
  if B.over or B.power_used or B.gauge < D.GAUGE_MAX:
    return False
  my = active()
  return badge_count() >= 5 and not sp(my)[EVLV] and not my.get("mega") and not my.get("gmax")


def add_gauge(n):
  if B and not B.over:
    B.gauge = min(D.GAUGE_MAX, B.gauge + n)


def power_mult(m):
  return 1.4 if m.get("mega") else (1.7 if m.get("gmax") else 1)


def burn_mult(m):
  return 0.75 if m.get("st") == "brn" else 1


def enemy_hit_factor():
  return 0.7 if not B.trainer else (0.85 if B.legend else 0.8)


def clear_battle_flags():
  for m in G["party"]:
    for k in ("mega", "gmax", "tf"):
      m.pop(k, None)
    clear_status(m)


def make_trainer_mon(i, lv):
  m = new_mon(i, lv)
  m["bossMaxHp"] = rnd(max_hp(m) * 1.2)
  m["hp"] = m["bossMaxHp"]
  return m


def ditto_prep():
  my, e = active(), B.enemy
  note = ""
  if my["id"] == "ditto" and e["id"] != "ditto":
    my["tf"] = e.get("tf") or e["id"]
    note += " Your Ditto TRANSFORMED into %s!" % D.SPECIES[my["tf"]][NAME]
  if e["id"] == "ditto" and my["id"] != "ditto":
    e["tf"] = my.get("tf") or my["id"]
    note += " The Ditto TRANSFORMED into %s!" % D.SPECIES[e["tf"]][NAME]
  return note


def start_battle(b, intro):
  global B, scene
  B = b
  fx.clear()
  scene = "battle"
  run(intro_task(intro + ditto_prep()))


def intro_task(msg):
  effect("enter", 500)
  yield from say(msg, 1200)
  B.menu = "main"
  B.mcur = 0


def say(msg, ms=900):
  B.msg = msg
  B.menu = "msg"
  yield from wait(ms)


def all_tired():
  return active()["hp"] == 0


def go_area(i):
  if all_tired():
    return say_notice("Your Pokemon are all tired! Heal them at the Center first.")
  s = step()
  if s and s[0] == "battle" and s[2] == i:
    return run(story_battle_task(G["story"]))
  name, lo, hi, need, pool, rare = D.AREAS[i]
  lv = lo + rand(hi - lo + 1)
  legendary = False
  if rare and random.random() < D.LEGEND_RATE:
    sid = rare[rand(len(rare))]
    legendary = True
    lv = 40 + rand(6)
  else:
    sid = pool[rand(len(pool))]
    s = D.SPECIES[sid]
    while s[EVLV] and lv >= s[EVLV] + 2 and random.random() < 0.6:
      to = s[EVTO]
      sid = to if isinstance(to, str) else to[rand(len(to))]
      s = D.SPECIES[sid]
  b = Battle(new_mon(sid, lv), bg=AREA_BG[i])
  start_battle(b, ("WOW!! A legendary %s appeared!!" if legendary else "Look! A wild %s is here!") % D.SPECIES[sid][NAME])


def go_cave(i):
  if all_tired():
    return say_notice("Your Pokemon are all tired! Heal them at the Center first.")
  name, badge_id, trainer, team = D.CAVES[i]
  queue = [make_trainer_mon(sid, lv) for sid, lv in team]
  b = Battle(queue.pop(0), trainer=trainer, cave=i, queue=queue, bg=CAVE_BG)
  start_battle(b, '%s wants to battle! "Go, %s!"' % (trainer, sp(b.enemy)[NAME]))


def go_boss():
  if all_tired():
    return say_notice("Your Pokemon are all tired! Heal them at the Center first.")
  if not G["masterBall"]:
    G["masterBall"] = True
    save()
    return say_notice("You found a shiny Master Ball! It can catch ANY Pokemon! Choose the cave again to go in!")
  name, _, trainer, team = D.LEGEND
  queue = [make_trainer_mon(sid, lv) for sid, lv in team]
  mw = new_mon("mewtwoX", D.MEWTWO_LV)
  mw["bossMaxHp"] = rnd(max_hp(mw) * 1.5)
  mw["hp"] = mw["bossMaxHp"]
  queue.append(mw)
  b = Battle(queue.pop(0), trainer=trainer, legend=True, queue=queue, bg=LEGEND_BG)
  start_battle(b, '%s wants to battle! "Go, %s!"' % (trainer, sp(b.enemy)[NAME]))


def go_plaza():
  if all_tired():
    return say_notice("Your Pokemon are all tired! Heal them at the Center first.")
  trainer, ttype = D.PLAZA[rand(len(D.PLAZA))]
  my_max = max(m["lv"] for m in G["party"])
  n = 2 + (1 if badge_count() >= 2 else 0) + (1 if badge_count() >= 4 else 0)
  base = [i for i in D.ORDER if i != "mewtwoX" and i not in D.LEGENDS and i not in D.EVOLVED
          and (ttype == "Any" or D.SPECIES[i][TYPE] == ttype)]
  queue = []
  for _ in range(n):
    lv = min(45, max(4, my_max - 1 + rand(4)))
    sid = base[rand(len(base))]
    s = D.SPECIES[sid]
    while s[EVLV] and lv >= s[EVLV]:
      to = s[EVTO]
      sid = to if isinstance(to, str) else to[rand(len(to))]
      s = D.SPECIES[sid]
    queue.append(make_trainer_mon(sid, lv))
  b = Battle(queue.pop(0), trainer=trainer, plaza=True, queue=queue, bg=PLAZA_BG)
  start_battle(b, '%s wants to battle! "Go, %s!"' % (trainer, sp(b.enemy)[NAME]))


# ---------------------------------------------------------------- battle turns

def moves_of(m):
  return form(m)[MV]


def pick_enemy_move(e):
  mv = moves_of(e)
  return mv[rand(len(mv))]


def can_act(m):
  if m.get("st") == "slp":
    if m.get("stT", 0) > 0:
      m["stT"] -= 1
      yield from say("%s is fast asleep..." % label(m), 950)
      return False
    clear_status(m)
    yield from say("%s woke up!" % label(m), 900)
  if m.get("st") == "par" and random.random() < 0.25:
    yield from say("%s is all zappy and can't move!" % label(m), 950)
    return False
  return True


def land_status(mv, target, side):
  t, pw, acc, pri, st, stc = D.MOVES[mv]
  if not st or target["hp"] <= 0 or not random.random() < stc:
    return
  if not apply_status(target, st):
    return
  effect("burst_" + side, 500, STATUS[st][1])
  yield from say("%s %s" % (label(target), STATUS[st][2]), 1050)


def strike_fx(src, dst, mt, big):
  """A lunge for Normal moves, a flying blob of the move's colour otherwise."""
  if mt == "Normal":
    effect("lunge_" + src, 260)
    yield from pause(200)
  else:
    effect("shot", 330, (src, TYPE_COLOR[mt]))
    yield from pause(330)
  effect("shake_" + dst, 380)
  effect("burst_" + dst, 450 if big else 300, TYPE_COLOR[mt] if mt != "Normal" else WHITE)
  if big:
    effect("flash", 160)


def use_move(name):
  my = active()
  emv = pick_enemy_move(B.enemy)
  pa, pb = D.MOVES[name][3], D.MOVES[emv][3]
  me_first = pa > pb if pa != pb else True
  if me_first:
    if (yield from my_action(name)):
      return
    if (yield from enemy_action(emv)):
      return
  else:
    if (yield from enemy_action(emv)):
      return
    if (yield from my_action(name)):
      return
  if (yield from end_of_turn()):
    return
  to_main()


def to_main():
  B.menu = "main"


def my_action(name):
  my, e = active(), B.enemy
  used_gmax = bool(my.get("gmax"))
  if not (yield from can_act(my)):
    return False
  yield from say("%s used %s!" % (label(my), name), 400)
  t, pw, acc, pri, st, stc = D.MOVES[name]
  if random.random() > acc:
    yield from say("Oops, it missed!", 800)
    yield from tick_gmax(my, used_gmax)
    return False
  mult = type_mult(t, form(e)[TYPE])
  big = mult > 1 or power_mult(my) > 1 or sp(my)[STAGE] >= 2
  yield from strike_fx("me", "foe", t, big)
  dmg = calc_damage(my, e, pw, mult * burn_mult(my) * power_mult(my))
  e["hp"] -= dmg
  if catch_phase() and e["hp"] < 1:
    e["hp"] = 1
  add_gauge(18)
  if mult > 1:
    msg = "SUPER hit! %d damage!" % dmg
  elif mult < 0.5:
    msg = "It barely works on %s Pokemon... %d damage" % (form(e)[TYPE], dmg)
  elif mult < 1:
    msg = "Hmm, not so good... %d damage" % dmg
  else:
    msg = "Pow! %d damage!" % dmg
  yield from say(msg, 900)
  if e["hp"] > 0:
    yield from land_status(name, e, "foe")
  yield from tick_gmax(my, used_gmax)
  yield from maybe_enemy_mega()
  if catch_phase() and e["hp"] == 1:
    yield from say("Mega Mewtwo X is wobbly...! Now! Throw the Master Ball!", 1200)
    to_main()
    return True
  if e["hp"] <= 0:
    e["hp"] = 0
    yield from enemy_down()
    return True
  return False


def tick_gmax(my, used):
  if not used or not my.get("gmax"):
    return
  my["gmax"] -= 1
  if my["gmax"] <= 0:
    my.pop("gmax", None)
    yield from say("Dynamax wore off... back to normal size!", 900)


def enemy_action(emv):
  e = B.enemy
  yield from maybe_enemy_mega()
  if not (yield from can_act(e)):
    return False
  my = active()
  yield from say("%s used %s!" % (label(e), emv), 500)
  t, pw, acc, pri, st, stc = D.MOVES[emv]
  if random.random() > acc:
    yield from say("%s's attack missed!" % label(e), 800)
    return False
  mult = type_mult(t, form(my)[TYPE])
  yield from strike_fx("foe", "me", t, mult > 1 or sp(e)[STAGE] >= 2)
  dmg = calc_damage(e, my, pw, mult * burn_mult(e) * power_mult(e) * enemy_hit_factor())
  my["hp"] = max(0, my["hp"] - dmg)
  add_gauge(12)
  yield from say(("Ouch!! Super hit! %d damage!" if mult > 1 else "Ouch! %d damage!") % dmg, 900)
  if my["hp"] > 0:
    yield from land_status(emv, my, "me")
    return False
  return (yield from my_fainted(my))


def end_of_turn():
  for side in ("me", "foe"):
    m = active() if side == "me" else B.enemy
    if not m or m["hp"] <= 0 or m.get("st") not in ("brn", "psn"):
      continue
    mx = max_hp(m) if side == "me" else boss_max(m)
    d = max(1, rnd(mx / 16))
    if side == "foe" and catch_phase():
      d = min(d, m["hp"] - 1)
    if d <= 0:
      continue
    m["hp"] = max(0, m["hp"] - d)
    effect("shake_" + side, 380)
    yield from say("%s is hurt by %s! %d damage" % (label(m), "its burn" if m["st"] == "brn" else "the poison", d), 950)
    if m["hp"] <= 0:
      if side == "me":
        return (yield from my_fainted(m))
      yield from enemy_down()
      return True
  return False


def maybe_enemy_mega():
  e = B.enemy
  behind = len([m for m in B.queue if m["id"] != "mewtwoX"])
  if not B.trainer or behind or B.enemy_mega:
    return False
  if e["id"] not in D.MEGA or e.get("tf") or e.get("mega"):
    return False
  if e["hp"] <= 0 or e["hp"] > boss_max(e) * 0.55:
    return False
  B.enemy_mega = True
  yield from say('%s: "Now! Show them our REAL power!"' % B.trainer, 1000)
  e["mega"] = True
  effect("glow_foe", 900, PURPLE)
  effect("flash", 250)
  yield from say("MEGA EVOLUTION! %s became %s!" % (sp(e)[NAME], D.MEGA[e["id"]]), 1300)
  return True


def enemy_down():
  if B.trainer:
    yield from trainer_mon_down()
  else:
    yield from win_wild("The wild %s fell down!" % label(B.enemy))


def my_fainted(fallen):
  global scene, story_after
  clear_status(fallen)
  fallen.pop("tf", None)
  if any(m["hp"] > 0 for m in G["party"]):
    yield from say("%s is too tired to battle..." % sp(fallen)[NAME], 1200)
    B.forced = True
    open_switch(True)
    return True
  yield from say("All your Pokemon are tired... Time to go home!", 1400)
  B.over = True
  clear_battle_flags()
  for m in G["party"]:
    m["hp"] = max_hp(m)
  if B.story is not None and ST.STEPS[B.story][9] is not None:
    story_after = (B.story, False)     # this one carries on win or lose
  save()
  go_town("The nurse healed everyone! Let's try again!")
  return True


def open_switch(forced):
  global scene
  cur = active()
  picks = [m for m in G["party"] if m["hp"] > 0 and (forced or m is not cur)]
  items = [[None, m, True, (lambda m=m: pick_switch(m, forced))] for m in picks]
  menu = Menu("Who goes next?" if forced else "Switch - uses your turn!", items,
              on_back=None if forced else cancel_switch, row_h=26,
              draw_row=lambda it, y, sel: mon_row(it[1], y, sel))
  stack.append(menu)
  scene = "menu"


def cancel_switch():
  global scene
  stack.pop()
  scene = "battle"
  B.msg = "What will you do?"
  to_main()


def pick_switch(m, forced):
  global scene
  stack.pop()
  scene = "battle"
  out = active()
  G["party"].remove(m)
  G["party"].insert(0, m)
  if out is not m:
    out.pop("tf", None)
  B.forced = False
  B.mcur = 0
  note = ditto_prep()
  effect("enter", 500, "me")
  if forced:
    run(say_then_main("You can do it, %s!%s" % (label(m), note)))
  else:
    run(switch_turn("Come back! Go, %s!%s" % (label(m), note)))


def say_then_main(msg, ms=900):
  yield from say(msg, ms)
  to_main()


def switch_turn(msg):
  yield from say(msg, 1000)
  if (yield from enemy_action(pick_enemy_move(B.enemy))):
    return
  if (yield from end_of_turn()):
    return
  to_main()


def throw_ball():
  e = B.enemy
  master = catch_phase()
  if B.trainer and not master:
    return run(say_then_main("You can't catch a trainer's Pokemon!"))
  if not master and G["balls"] <= 0:
    return run(say_then_main("No balls left! Get more at the Pokemon Center."))
  if not master and len(G["party"]) >= 6 and len(G["box"]) >= D.BOX_MAX:
    return run(say_then_main("Your team AND your Box are full! Say bye-bye to someone first."))
  run(ball_task(master))


def ball_task(master):
  e = B.enemy
  if not master:
    G["balls"] -= 1
  yield from say("You threw the %s!" % ("Master Ball" if master else "Poke Ball"), 400)
  effect("ball", 600, master)
  yield from pause(600)
  effect("caught", 1300, master)
  B.msg = "Wiggle... wiggle... wiggle..."
  yield from pause(1300)
  hp_ratio = e["hp"] / boss_max(e)
  sleepy = 0.20 if e.get("st") == "slp" else 0
  if master:
    chance = 0.05 if hp_ratio > 0.4 else (1 - hp_ratio) * 0.85
    if e["hp"] == 1:
      chance = 0.95
    chance += sleepy
  else:
    chance = 0.25 + (1 - hp_ratio) * 0.65 + sleepy
    if e["id"] in D.LEGENDS:
      chance *= 0.4
  if random.random() < min(1, chance):
    effect("caught", 99999, master)
    if master:
      yield from boss_caught()
      return
    B.over = True
    caught = {"id": e["id"], "lv": e["lv"], "exp": e.get("exp", 0), "hp": max(e["hp"], rnd(max_hp(e) / 2)), "uid": e["uid"]}
    caught["hp"] = min(caught["hp"], max_hp(caught))
    where = ""
    if len(G["party"]) < 6:
      G["party"].append(caught)
    else:
      caught["hp"] = max_hp(caught)
      G["box"].append(caught)
      where = " Your team is full, so it went to the Box! (%d/%d)" % (len(G["box"]), D.BOX_MAX)
    if e["id"] not in G["dex"]:
      G["dex"].append(e["id"])
    yield from say("Click! You caught %s!%s" % (sp(e)[NAME], where), 1600)
    yield from win_wild(None, True)
  else:
    fx.pop("caught", None)
    yield from say("Oh no, it popped out! Make it more sleepy first!" if master
                   else "Oh no, it popped out! Hit it a little, then try again!", 1100)
    if (yield from enemy_action(pick_enemy_move(B.enemy))):
      return
    if (yield from end_of_turn()):
      return
    to_main()


def run_away():
  run(run_task())


def run_task():
  yield from say("You ran away! The trainer will wait for you." if B.trainer else "You ran away!", 900)
  B.over = True
  clear_battle_flags()
  save()
  go_town()


def do_mega():
  run(mega_task())


def mega_task():
  my = active()
  my["mega"] = True
  B.power_used = True
  B.gauge = 0
  effect("glow_me", 900, PURPLE)
  yield from say("%s's Mega Bracelet is shining!" % sp(my)[NAME], 900)
  effect("flash", 250)
  yield from say("MEGA EVOLUTION! It became %s! Attack AND defence up!" % D.MEGA[my["id"]], 1400)
  to_main()


def do_gmax():
  run(gmax_task())


def gmax_task():
  my = active()
  my["gmax"] = 3
  B.power_used = True
  B.gauge = 0
  healed = min(max_hp(my) - my["hp"], rnd(max_hp(my) * 0.25))
  my["hp"] += healed
  effect("glow_me", 900, RED)
  yield from say("%s is getting HUGE!" % sp(my)[NAME], 900)
  effect("flash", 250)
  yield from say("DYNAMAX! G-Max %s is GIANT for 3 moves!%s" % (
    sp(my)[NAME], " It got %d HP back!" % healed if healed > 0 else ""), 1400)
  to_main()


# ---------------------------------------------------------------- winning

def level_up(m):
  before = max_hp(m)
  m["exp"] -= exp_need(m)
  m["lv"] += 1
  m["hp"] = min(max_hp(m), m["hp"] + (max_hp(m) - before))


def grant_exp(defeated, trainer_mon):
  my = active()
  gained = defeated["lv"] * (8 if trainer_mon else 5) + 5
  my["exp"] += gained
  yield from say("%s got %d exp!" % (sp(my)[NAME], gained), 1100)
  while my["exp"] >= exp_need(my):
    level_up(my)
    effect("glow_me", 700, GOLD)
    yield from say("Level up! %s is Level %d now!" % (sp(my)[NAME], my["lv"]), 1100)
  share = gained // 2
  grew = []
  for m in G["party"]:
    if m is my or m["hp"] <= 0 or share <= 0:
      continue
    m["exp"] += share
    up = False
    while m["exp"] >= exp_need(m):
      level_up(m)
      up = True
    if up:
      grew.append("%s Lv.%d" % (sp(m)[NAME], m["lv"]))
  if grew:
    yield from say("The team learned too! " + ", ".join(grew), 1300)


def find_evolution():
  for m in G["party"]:
    s = sp(m)
    if s[EVLV] and m["lv"] >= s[EVLV]:
      to = s[EVTO]
      if not isinstance(to, str):
        to = to[rand(len(to))]
      return (m, m["id"], to)
  return None


evo = None
evo_next = None
evo_at = 0


def finish_battle(msg):
  global scene, evo, evo_next, evo_at
  clear_battle_flags()
  rest_box()
  save()
  e = find_evolution()
  if e:
    evo, evo_next, evo_at = e, msg, badge.ticks
    scene = "evolve"
    return
  go_town(msg)


def win_wild(msg, was_catch=False):
  B.over = True
  if msg:
    yield from say(msg, 1000)
  yield from grant_exp(B.enemy, False)
  if not was_catch and random.random() < 0.4:
    G["balls"] += 1
    yield from say("You found a Poke Ball on the ground! +1", 900)
  finish_battle("You made a new friend! Your Pokedex has %d/%d kinds now!" % (len(G["dex"]), len(D.ORDER))
                if was_catch else "You did it!")


def trainer_mon_down():
  global story_after
  e = B.enemy
  effect("faint_foe", 600)
  yield from say("%s fell down!" % label(e), 900)
  yield from grant_exp(e, True)
  if B.queue:
    B.enemy = B.queue.pop(0)
    fx.pop("faint_foe", None)
    effect("enter", 500, "foe")
    note = ditto_prep()
    yield from say("%s sends out %s!%s" % (B.trainer, sp(B.enemy)[NAME], note), 1100)
    to_main()
    return
  B.over = True
  if B.story is not None:
    story_after = (B.story, True)
    finish_battle("You beat %s!" % B.trainer)
    return
  if B.plaza:
    G["balls"] += 1
    finish_battle("You beat %s! They gave you a Poke Ball! +1" % B.trainer)
    return
  if B.cave is not None and D.CAVES[B.cave][1] not in G["badges"]:
    G["badges"].append(D.CAVES[B.cave][1])
    yield from say("You beat %s! You got the %s badge! %d/5" % (B.trainer, D.CAVES[B.cave][0], badge_count()), 1500)
    if badge_count() == 3:
      yield from say("You found a Mega Bracelet! Now some Pokemon can MEGA EVOLVE in battle!", 1800)
    if badge_count() == 5:
      yield from say("You found a Dynamax Band! Now your best Pokemon can go GIANT in battle!", 1800)
    finish_battle('%s: "Wow, you\'re strong! Come back anytime for a rematch!"' % B.trainer)
    return
  finish_battle("You beat the Champion again! What a team!" if B.legend
                else "You beat %s again! Great practice!" % B.trainer)


def boss_caught():
  global scene
  B.over = True
  clear_battle_flags()
  G["bossCaught"] = True
  if "mewtwoX" not in G["dex"]:
    G["dex"].append("mewtwoX")
  mw = new_mon("mewtwoX", D.MEWTWO_LV)
  if len(G["party"]) < 6:
    G["party"].append(mw)
  elif len(G["box"]) < D.BOX_MAX:
    G["box"].append(mw)
  rest_box()
  save()
  yield from say("Click! You caught Mega Mewtwo X!!", 1600)
  scene = "win"


# ---------------------------------------------------------------- battle screen

def battle_input():
  if B.menu == "main":
    items = main_items()
    n = len(items)
    if repeat(BUTTON_DOWN) or badge.pressed(BUTTON_C):
      B.mcur = (B.mcur + 1) % n
    if repeat(BUTTON_UP):
      B.mcur = (B.mcur - 1) % n
    if ok():
      items[B.mcur][1]()
  elif B.menu == "fight":
    items = fight_items()
    n = len(items)
    if repeat(BUTTON_DOWN) or badge.pressed(BUTTON_C):
      B.fcur = (B.fcur + 1) % n
    if repeat(BUTTON_UP):
      B.fcur = (B.fcur - 1) % n
    if ok():
      items[B.fcur][1]()
    elif back():
      B.menu = "main"


def main_items():
  ball = ("MASTER BALL", throw_ball) if catch_phase() else ("BALL x%d" % G["balls"], throw_ball)
  return [("FIGHT", open_fight), ball, ("TEAM", team_in_battle), ("RUN", run_away)]


# each Pokemon's last move, so B, B repeats it (and the menus stay where you left them)
last_move = {}


def open_fight():
  B.menu = "fight"
  names = [lab for lab, _ in fight_items()]
  want = last_move.get(active()["uid"])
  B.fcur = names.index(want) if want in names else len(names) - len(moves_of(active()))


def pick_move(name):
  last_move[active()["uid"]] = name
  run(use_move(name))


def fight_items():
  items = []
  if can_mega():
    items.append(("MEGA!", do_mega))
  if can_gmax():
    items.append(("DYNAMAX!", do_gmax))
  for name in moves_of(active()):
    items.append((name, lambda name=name: pick_move(name)))
  return items


def team_in_battle():
  cur = active()
  if not any(m["hp"] > 0 and m is not cur for m in G["party"]):
    return run(say_then_main("No one else can battle right now!"))
  open_switch(False)


def shake_dx(side):
  k = effect_part("shake_" + side)
  return int(math.sin(k * 30) * 3 * (1 - k)) if k is not None else 0


def draw_mon(m, x, y, side):
  if effect_part("faint_" + side) is not None and side == "foe":
    k = effect_part("faint_" + side)
    y += int(k * 30)
  k = effect_part("enter")
  if k is not None and fx.get("enter", (0, 0, None))[2] in (None, side):
    x += int((1 - k) * (40 if side == "foe" else -40))
  x += shake_dx(side)
  k = effect_part("lunge_" + side)
  if k is not None:
    d = int(math.sin(k * math.pi) * 10)
    x += d if side == "me" else -d
    y += -d if side == "me" else d
  glow = fx.get("glow_" + side)
  if m.get("mega") or m.get("gmax") or glow:
    pen = (glow[2] if glow else PURPLE if m.get("mega") else RED)
    pulse = 26 + int(math.sin(badge.ticks / 120) * 2)
    screen.pen = color.rgb(255, 255, 255, 90)
    screen.shape(shape.circle(x + 24, y + 26, pulse + 2))
    screen.pen = pen
    screen.alpha = 110
    screen.shape(shape.circle(x + 24, y + 26, pulse))
    screen.alpha = 255
  if fx.get("caught") and side == "foe":
    return
  if m.get("gmax"):
    draw_sprite(sprite_key(m), x - 6, y - 10, 60, flip=(side == "me"))
  else:
    draw_sprite(sprite_key(m), x, y, 48, flip=(side == "me"))
  k = effect_part("burst_" + side)
  if k is not None:
    pen = fx["burst_" + side][2] if ("burst_" + side) in fx else WHITE
    screen.pen = pen
    screen.alpha = int(220 * (1 - k))
    for a in range(8):
      ang = a * math.pi / 4 + k
      r = 8 + k * 18
      screen.shape(shape.circle(x + 24 + math.cos(ang) * r, y + 26 + math.sin(ang) * r, 3 * (1 - k) + 1))
    screen.alpha = 255


ME_X, ME_Y = 6, 34
FOE_X, FOE_Y = 106, 2


def draw_battle():
  e, my = B.enemy, active()
  sky, ground = B.bg
  screen.pen = sky
  screen.clear()
  screen.pen = ground
  screen.rectangle(0, 58, W, 26)
  screen.pen = color.rgb(0, 0, 0, 40)
  screen.shape(shape.ellipse(FOE_X + 24, FOE_Y + 48, 26, 6))
  screen.shape(shape.ellipse(ME_X + 24, ME_Y + 48, 26, 6))

  draw_mon(e, FOE_X, FOE_Y, "foe")
  draw_mon(my, ME_X, ME_Y, "me")

  # a thrown ball or a flying move
  k = effect_part("shot")
  if k is not None:
    src, pen = fx["shot"][2] if "shot" in fx else ("me", WHITE)
    a = (ME_X + 30, ME_Y + 22) if src == "me" else (FOE_X + 18, FOE_Y + 26)
    b = (FOE_X + 24, FOE_Y + 26) if src == "me" else (ME_X + 24, ME_Y + 26)
    screen.pen = pen
    screen.shape(shape.circle(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k - math.sin(k * math.pi) * 10, 5))
  k = effect_part("ball")
  if k is not None:
    master = fx["ball"][2] if "ball" in fx else False
    ball_icon(int(ME_X + 30 + (FOE_X + 24 - ME_X - 30) * k), int(ME_Y + 10 + (FOE_Y + 34 - ME_Y - 10) * k - math.sin(k * math.pi) * 30), 4, master)
  if "caught" in fx:
    wob = int(math.sin(badge.ticks / 90) * 3) if effect_part("caught") is not None and fx["caught"][1] < 9999 else 0
    ball_icon(FOE_X + 24 + wob, FOE_Y + 42, 5, fx["caught"][2])

  # enemy panel
  # name on top, then HP, then level / status / the trainer's balls left
  box(2, 2, 100, 30, PANEL)
  text_fit(label(e), 5, 3, 94)
  hp_bar(5, 17, 94, e["hp"], boss_max(e))
  x = 5 + status_tag(e, 5, 22)
  x += 2 if x > 5 else 0
  text("Lv.%d" % e["lv"], x, 22, INK, TINY)
  if e.get("tf"):
    text("copycat", x + width_of("Lv.%d " % e["lv"], TINY), 22, MUTED, TINY)
  if B.trainer:
    for n in range(1 + len(B.queue)):
      ball_icon(96 - n * 8, 26, 2)

  # my panel
  box(58, 48, 100, 35 if power_unlocked() else 32, PANEL)
  text_fit(label(my), 61, 49, 94)
  hp_bar(61, 63, 94, my["hp"], max_hp(my))
  x = 61 + status_tag(my, 61, 68)
  x += 2 if x > 61 else 0
  text("Lv.%d" % my["lv"], x, 68, INK, TINY)
  # Dynamax moves left, as red dots on the ground by your Pokemon
  for n in range(my.get("gmax") or 0):
    ball_icon(ME_X + 14 + n * 9, ME_Y + 46, 3)
  text_right("%d/%d" % (my["hp"], max_hp(my)), 155, 68, MUTED, TINY)
  if power_unlocked():
    full = B.gauge >= D.GAUGE_MAX
    screen.pen = SHADE
    screen.rectangle(61, 79, 94, 2)
    screen.pen = PURPLE if full and (badge.ticks // 250) % 2 else (PURPLE if full else YELLOW)
    if full and (badge.ticks // 250) % 2 == 0:
      screen.pen = color.rgb(200, 150, 255)
    screen.rectangle(61, 79, int(94 * B.gauge / D.GAUGE_MAX), 2)

  if effect_part("flash") is not None:
    screen.pen = color.rgb(255, 255, 255, 150)
    screen.rectangle(0, 0, W, 84)

  # bottom: message or the choices
  if B.menu == "msg":
    message_box(B.msg)
  elif B.menu == "main":
    box(1, 84, W - 2, 36)
    for n, (lab, _) in enumerate(main_items()):
      x = 6 + (n % 2) * 78
      y = 87 + (n // 2) * 15
      sel = n == B.mcur
      dim = n == 1 and B.trainer and not catch_phase()
      if sel:
        screen.pen = HILITE
        screen.shape(shape.rounded_rectangle(x - 3, y, 76, 14, 2))
        screen.pen = RED
        screen.triangle(x - 1, y + 3, x - 1, y + 10, x + 3, y + 6)
      text_fit(lab, x + 6, y, 64, FAINT if dim else (PURPLE if n == 1 and catch_phase() else INK))
  else:
    items = fight_items()
    box(1, 84, W - 2, 36)
    rows = (len(items) + 1) // 2
    pitch = 11 if rows > 2 else 15
    for n, (lab, _) in enumerate(items):
      x = 5 + (n % 2) * 77
      y = 86 + (n // 2) * pitch
      sel = n == B.fcur
      if lab in ("MEGA!", "DYNAMAX!"):
        pen = PURPLE if lab[0] == "M" else RED
      else:
        pen = TYPE_COLOR[D.MOVES[lab][0]]
      if sel:
        screen.pen = HILITE
        screen.shape(shape.rounded_rectangle(x - 2, y, 75, pitch, 2))
      screen.pen = pen
      screen.rectangle(x, y + 3, 3, pitch - 6)
      text_fit(lab, x + 5, y + (0 if pitch == 11 else 1), 68, INK, SMALL if pitch == 11 else BODY)


# ---------------------------------------------------------------- other screens

def draw_title():
  screen.pen = color.rgb(255, 214, 70)
  screen.clear()
  screen.pen = color.rgb(255, 236, 140)
  screen.shape(shape.circle(80, 150, 80))
  screen.pen = RED
  screen.rectangle(0, 0, W, 3)
  text_center("POCKET MINI", 4, INK, TITLE)
  text_center("ADVENTURE", 19, RED, TITLE)
  bob = int(math.sin(badge.ticks / 300) * 2)
  draw_sprite("pikachu", 1, 8 + bob, 28)
  draw_sprite("pairi", W - 29, 8 - bob, 28)
  title_menu.draw_inline()


class TitleMenu:
  """One row per save slot: B plays it (or starts a new game), A erases it."""

  def __init__(self):
    self.cur = 0
    self.saves = [None] * SLOTS

  def refresh(self):
    self.saves = [load_slot(n) for n in range(1, SLOTS + 1)]

  def update(self):
    if repeat(BUTTON_DOWN):
      self.cur = (self.cur + 1) % SLOTS
    if repeat(BUTTON_UP):
      self.cur = (self.cur - 1) % SLOTS
    if ok():
      play_slot(self.cur + 1)
    elif back() and self.saves[self.cur]:
      n = self.cur + 1

      def yes():
        State.delete(slot_key(n))
        self.refresh()
      ask("Erase save %d? It's gone for good!" % n, yes)

  def draw_inline(self):
    for k in range(SLOTS):
      y = 37 + k * 14
      g = self.saves[k]
      sel = k == self.cur
      box(4, y, W - 8, 13, HILITE if sel else PANEL, INK if sel else FAINT)
      text("%d" % (k + 1), 8, y, RED if sel else MUTED)
      if g:
        lead = g["party"][0]
        text_fit("%s Lv.%d" % (D.SPECIES[lead["id"]][NAME], lead["lv"]), 19, y, 96)
        badge_icon(123, y + 6)
        text("%d" % len(g["badges"]), 129, y + 1, INK, SMALL)
        if g["bossCaught"]:
          ball_icon(146, y + 6, 3, True)
      else:
        text("New game", 19, y, FAINT)
    text_center("B = Play     A = Erase", 109, INK, TINY)


title_menu = TitleMenu()


def play_slot(n):
  global SLOT, G
  SLOT = n
  State.save(SAVE + "_meta", {"last": n})
  G = title_menu.saves[n - 1]
  if G:
    continue_game()
  else:
    run(intro_story())


def continue_game():
  s = step()
  go_town("Welcome back! %s is ready! %s" % (
    sp(active())[NAME], ("Story: " + goal_text()) if s else ""))


def intro_story():
  global scene, starter_cur
  yield from talk(ST.INTRO)
  starter_cur = 0
  scene = "starter"


starter_cur = 0


def starter_input():
  global starter_cur, G
  if repeat(BUTTON_DOWN) or badge.pressed(BUTTON_C):
    starter_cur = (starter_cur + 1) % 3
  if repeat(BUTTON_UP):
    starter_cur = (starter_cur - 1) % 3
  if back():
    go_title()
  elif ok():
    sid = STARTERS[starter_cur]
    G = {"party": [new_mon(sid, 5)], "box": [], "balls": 5, "dex": [sid], "badges": [],
         "masterBall": False, "bossCaught": False, "name": "", "cloud": None,
         "story": 0, "rival": ST.RIVAL_OF[sid]}
    save()
    go_town("Yay! %s is your buddy now! Let's go!" % D.SPECIES[sid][NAME])


def draw_starter():
  screen.pen = PAPER
  screen.clear()
  screen.pen = INK
  screen.rectangle(0, 0, W, 14)
  text_center("Pick your buddy!", 0, WHITE)
  for n, sid in enumerate(STARTERS):
    x = 4 + n * 52
    sel = n == starter_cur
    if sel:
      box(x - 2, 18, 54, 74, HILITE)
    bob = int(math.sin(badge.ticks / 200) * 2) if sel else 0
    draw_sprite(sid, x + 1, 22 + bob)
    s = D.SPECIES[sid]
    text_center(s[NAME], 72, INK, SMALL, cx=x + 25, maxw=50)
    tw = width_of(s[TYPE], TINY) + 4
    type_tag(s[TYPE], x + 25 - tw // 2, 83)
  text_center("Up/Down to look, B to pick!", 100, MUTED, SMALL)


def draw_heal():
  screen.pen = color.rgb(255, 230, 240)
  screen.clear()
  text_center("Pokemon Center", 4, RED, TITLE)
  text_center('"One moment please!"', 26, INK, SMALL)
  n = len(G["party"])
  for k, m in enumerate(G["party"]):
    x = W / 2 - n * 13 + k * 26
    draw_sprite(m["id"], x, 50 + int(math.sin(badge.ticks / 150 + k) * 2), 24)
  t = badge.ticks / 1000
  screen.pen = color.rgb(240, 90, 140)
  for k in range(6):
    y = 100 - ((t * 30 + k * 17) % 60)
    screen.shape(shape.circle(20 + k * 24, y, 3))


def draw_evolve():
  m, frm, to = evo
  t = badge.ticks - evo_at
  screen.pen = color.rgb(30, 30, 60)
  screen.clear()
  if t < 1700 * PACE:
    text_center("Huh...?", 2, WHITE, SMALL)
    text_center("%s looks funny...!" % D.SPECIES[frm][NAME], 13, WHITE, SMALL, maxw=W - 4)
    glow = (t // 160) % 2 == 0
    if glow:
      screen.pen = WHITE
      screen.shape(shape.circle(80, 56, 30 + (t // 100) % 4))
    draw_sprite(frm, 56, 32)
    text_center("It's glowing!", 96, YELLOW, SMALL)
  else:
    if m["id"] != to:
      m["id"] = to
      m["hp"] = max_hp(m)
      if to not in G["dex"]:
        G["dex"].append(to)
      save()
    screen.pen = color.rgb(255, 230, 120)
    for k in range(12):
      a = k * math.pi / 6 + t / 600
      screen.shape(shape.circle(80 + math.cos(a) * 40, 56 + math.sin(a) * 34, 2))
    draw_sprite(to, 56, 32 + int(math.sin(t / 200) * 2))
    text_center("WOW! %s became" % D.SPECIES[frm][NAME], 4, WHITE, SMALL, maxw=W - 4)
    text_center("%s!" % D.SPECIES[to][NAME], 16, YELLOW, BODY, maxw=W - 4)
    text_center("B = Yay!", 104, WHITE, SMALL)


def evolve_input():
  if badge.ticks - evo_at >= 1700 * PACE and evo[0]["id"] == evo[2] and ok():
    finish_battle(evo_next or "%s is super strong now!" % D.SPECIES[evo[2]][NAME])


def draw_win():
  screen.pen = color.rgb(40, 20, 70)
  screen.clear()
  t = badge.ticks
  for k, (x, y0) in enumerate(CONFETTI):
    y = (y0 + t // (12 + k)) % (H + 10) - 5
    screen.pen = (GOLD, PURPLE, RED, WHITE)[k % 4]
    screen.rectangle(x, y, 3, 3)
  draw_sprite("mewtwoX", 4, 20 + int(math.sin(t / 250) * 2))
  text("YOU WIN!", 56, 6, GOLD, TITLE)
  text("You beat the", 58, 30, WHITE, SMALL)
  text("Champion and", 58, 41, WHITE, SMALL)
  text("caught Mewtwo X!", 58, 52, WHITE, SMALL)
  text("Badges %d/5  Dex %d/%d" % (badge_count(), len(G["dex"]), len(D.ORDER)), 6, 76, WHITE, SMALL)
  text("Best level %d" % max(m["lv"] for m in G["party"]), 6, 88, WHITE, SMALL)
  text_center("B = Keep exploring", 106, YELLOW, SMALL)


CONFETTI = [(rand(W), rand(H)) for _ in range(14)]


def go_title():
  global scene
  stack.clear()
  scene = "title"
  title_menu.refresh()
  title_menu.cur = SLOT - 1


# ---------------------------------------------------------------- story

story_after = None      # (step, won) once a story battle is over
talk_state = None       # (who, lines on this page)


def step():
  i = G["story"]
  return ST.STEPS[i] if i < len(ST.STEPS) else None


def goal_text():
  s = step()
  if not s:
    return "Story complete! Keep catching them all!"
  return s[3] if s[0] == "battle" else s[2]


def cond_met(c):
  if c[0] == "dex":
    return len(G["dex"]) >= c[1]
  if c[0] == "badges":
    return badge_count() >= c[1]
  if c[0] == "boss":
    return G["bossCaught"]
  if c[0] == "legends":
    return len([i for i in G["dex"] if i in D.LEGENDS]) >= c[1]
  return False


def story_ready():
  """The current step is a battle you can go and fight right now."""
  s = step()
  return bool(s) and s[0] == "battle" and (s[2] is None or badge_count() >= D.AREAS[s[2]][3])


def story_label():
  if not step():
    return "DONE"
  return "GO!" if story_ready() else "%d/%d" % (G["story"] + 1, len(ST.STEPS))


def story_first():
  say_notice("Story first! " + goal_text())


def rival_at(lv):
  """Jay's starter, evolved as far as level lv allows."""
  sid = G["rival"]
  s = D.SPECIES[sid]
  while s[EVLV] and lv >= s[EVLV] and isinstance(s[EVTO], str):
    sid = s[EVTO]
    s = D.SPECIES[sid]
  return sid


def fill(s):
  if not G:
    return s
  return s.replace("{rival}", D.SPECIES[G["rival"]][NAME]).replace("{mon}", sp(active())[NAME])


def talk(lines):
  """Show lines of dialogue, a page at a time; B turns the page."""
  global scene, talk_state
  back_to = scene
  scene = "talk"
  for who, s in lines:
    page = wrap(fill(s), SMALL, W - 12)
    for k in range(0, len(page), 3):
      talk_state = (who, page[k:k + 3])
      shown = badge.ticks
      yield
      while not (ok() and badge.ticks - shown > 250):
        yield
  talk_state = None
  scene = back_to


def story_check():
  """In town: wrap up a story battle, a goal just reached, or start a battle
  that happens right where you are. True when a story scene started."""
  global story_after
  if not G:
    return False
  if story_after is not None:
    i, won = story_after
    story_after = None
    if i == G["story"]:
      run(finish_step(i, won))
      return True
  s = step()
  if not s:
    return False
  if s[0] == "goal" and cond_met(s[1]):
    run(finish_step(G["story"], True))
    return True
  if s[0] == "battle" and s[2] is None:
    run(story_battle_task(G["story"]))
    return True
  return False


def give(reward):
  got = []
  if reward.get("balls"):
    G["balls"] += reward["balls"]
    got.append("Got %d Poke Balls!" % reward["balls"])
  if reward.get("gift"):
    sid, lv = reward["gift"]
    m = new_mon(sid, lv)
    if len(G["party"]) < 6:
      G["party"].append(m)
      got.append("%s joined your team!" % D.SPECIES[sid][NAME])
    else:
      G["box"].append(m)
      got.append("%s is waiting in the Box!" % D.SPECIES[sid][NAME])
    if sid not in G["dex"]:
      G["dex"].append(sid)
  return " ".join(got)


def finish_step(i, won):
  s = ST.STEPS[i]
  if s[0] == "goal":
    lines, reward = s[4], s[5]
  else:
    lines, reward = (s[8] if won else s[9]), s[10]
  yield from talk(lines)
  G["story"] = i + 1
  got = give(reward)
  save()
  go_town(None, check=False)
  if not story_check():
    say_notice((got + " " if got else "") + ("New goal: " + goal_text() if step() else goal_text()))


def story_battle_task(i):
  s = ST.STEPS[i]
  yield from talk(s[7])
  team = [make_trainer_mon(rival_at(lv) if sid == "RIVAL" else sid, lv) for sid, lv in s[6]]
  b = Battle(team.pop(0), trainer=s[5], queue=team, bg=AREA_BG[s[2]] if s[2] is not None else PLAZA_BG)
  b.story = i
  start_battle(b, '%s wants to battle! "Go, %s!"' % (s[5], sp(b.enemy)[NAME]))


def open_story():
  global scene
  scene = "story"


def story_input():
  global scene
  if back():
    scene = "menu"
  elif ok():
    scene = "menu"
    if story_ready():
      if all_tired():
        say_notice("Your Pokemon are all tired! Heal them at the Center first.")
      else:
        run(story_battle_task(G["story"]))


def draw_story():
  s = step()
  screen.pen = PAPER
  screen.clear()
  screen.pen = INK
  screen.rectangle(0, 0, W, 14)
  text("Story", 4, 0, WHITE)
  text_right("%d/%d" % (min(G["story"] + 1, len(ST.STEPS)), len(ST.STEPS)), W - 4, 2, WHITE, SMALL)
  # progress along the whole story
  screen.pen = SHADE
  screen.rectangle(4, 17, W - 8, 3)
  screen.pen = GOLD
  screen.rectangle(4, 17, int((W - 8) * min(1, G["story"] / len(ST.STEPS))), 3)
  y = 24
  for line in wrap(goal_text(), BODY, W - 10):
    text(line, 5, y, INK)
    y += 13
  if s:
    y += 3
    hint = s[4] if s[0] == "battle" else s[3]
    for line in wrap(hint, SMALL, W - 10):
      text(line, 5, y, MUTED, SMALL)
      y += 11
  screen.pen = SHADE
  screen.rectangle(0, H - 13, W, 13)
  if story_ready():
    text("B = Go!", 5, H - 12, RED)
  text_right("A = Back", W - 5, H - 11, MUTED, SMALL)


def draw_person(cx, top, shirt, hair):
  screen.pen = color.rgb(*shirt)
  screen.shape(shape.rounded_rectangle(cx - 13, top + 21, 26, 26, 7))
  screen.pen = color.rgb(250, 214, 178)
  screen.shape(shape.circle(cx, top + 12, 10))
  was = screen.clip
  screen.clip = rect(cx - 12, top, 24, 9)
  screen.pen = color.rgb(*hair)
  screen.shape(shape.circle(cx, top + 12, 11))
  screen.clip = was
  screen.pen = INK
  screen.rectangle(cx - 4, top + 12, 2, 3)
  screen.rectangle(cx + 3, top + 12, 2, 3)


def draw_talk():
  screen.pen = color.rgb(200, 226, 248)
  screen.clear()
  screen.pen = color.rgb(150, 205, 120)
  screen.rectangle(0, 56, W, 20)
  if not talk_state:
    return
  who, lines = talk_state
  name, shirt, hair, partner = ST.PEOPLE[who]
  bob = int(math.sin(badge.ticks / 250) * 1.5)
  draw_person(42, 14 + bob, shirt, hair)
  if partner == "RIVAL":
    partner = rival_at(max(m["lv"] for m in G["party"])) if G else None
  if partner:
    draw_sprite(partner, 82, 18 - bob)
  box(1, 72, W - 2, 48)
  wd = width_of(name, SMALL) + 8
  screen.pen = color.rgb(*shirt)
  screen.shape(shape.rounded_rectangle(5, 66, wd, 12, 3))
  text(name, 9, 66, WHITE, SMALL)
  for n, line in enumerate(lines):
    text(line, 6, 80 + n * 11, INK, SMALL)
  if (badge.ticks // 400) % 2:
    screen.pen = RED
    screen.triangle(W - 12, 113, W - 6, 113, W - 9, 116)


# ---------------------------------------------------------------- overlays

def draw_notice():
  lines = wrap(notice, SMALL, W - 14)
  h = 10 + len(lines) * 11
  y = H - h - 2
  box(3, y, W - 6, h, PANEL)
  for n, line in enumerate(lines):
    text(line, 8, y + 2 + n * 11, INK, SMALL)
  if (badge.ticks // 400) % 2:
    screen.pen = RED
    screen.triangle(W - 12, y + h - 7, W - 6, y + h - 7, W - 9, y + h - 4)


def draw_confirm():
  q = confirm[0]
  lines = wrap(q, SMALL, W - 24)
  h = 24 + len(lines) * 11
  y = (H - h) // 2
  screen.pen = color.rgb(0, 0, 0, 120)
  screen.rectangle(0, 0, W, H)
  box(8, y, W - 16, h, PANEL)
  for n, line in enumerate(lines):
    text(line, 13, y + 3 + n * 11, INK, SMALL)
  text("B = Yes", 16, y + h - 14, RED)
  text_right("A = No", W - 16, y + h - 14, MUTED)


# ---------------------------------------------------------------- main loop

G = None
title_menu.refresh()
SLOT = last_slot()
title_menu.cur = SLOT - 1
exit_to = None
exit_hold_at = None

while exit_to is None:
  # both vertical buttons held together save and leave
  if badge.held(BUTTON_UP) and badge.held(BUTTON_DOWN):
    if exit_hold_at is None:
      exit_hold_at = badge.ticks
    elif badge.ticks - exit_hold_at > 700:
      if G:
        if B and not B.over:
          clear_battle_flags()
        save()
      exit_to = MENU
      break
  else:
    exit_hold_at = None

  if task:
    cur = task
    try:
      next(cur)
    except StopIteration:
      # it may have started the next task on its way out
      if task is cur:
        task = None
  elif confirm:
    if ok():
      fn = confirm[1]
      confirm = None
      fn()
    elif back():
      confirm = None
  elif notice:
    if ok() or back():
      notice = None
  elif scene == "title":
    title_menu.update()
  elif scene == "starter":
    starter_input()
  elif scene == "menu":
    stack[-1].update()
  elif scene == "battle":
    battle_input()
  elif scene == "info":
    if ok() or back():
      scene = "menu"
  elif scene == "story":
    story_input()
  elif scene == "evolve":
    evolve_input()
  elif scene == "win":
    if ok():
      go_town("Can you fill the whole Pokedex? Trainers love rematches!")

  if scene == "title":
    draw_title()
  elif scene == "starter":
    draw_starter()
  elif scene == "menu" and stack:
    top = stack[-1]
    top.draw()
    if getattr(top, "town", False):
      draw_town_header()
  elif scene == "battle":
    draw_battle()
  elif scene == "info":
    draw_info()
  elif scene == "heal":
    draw_heal()
  elif scene == "talk":
    draw_talk()
  elif scene == "story":
    draw_story()
  elif scene == "evolve":
    draw_evolve()
  elif scene == "win":
    draw_win()

  if notice and not task:
    draw_notice()
  if confirm:
    draw_confirm()

  badge.update()

on_exit = exit_to
