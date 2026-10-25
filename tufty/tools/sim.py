# Runs the badge app under CPython with a fake badge API, driven by a bot.
# Drawing is a no-op; the point is to walk every game path and catch crashes.
# See bots.py for the bots that drive it.
import builtins, sys, types, random, json, os, traceback

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pocket_mini_adventure")
sys.path.insert(0, APP)

BUTTONS = ["A", "B", "C", "UP", "DOWN", "HOME"]
for b in BUTTONS:
  setattr(builtins, "BUTTON_" + b, b)
builtins.LORES, builtins.HIRES, builtins.VSYNC = 1, 2, 4


class Stop(Exception):
  pass


class Badge:
  def __init__(self):
    self.ticks = 0
    self.ticks_delta = 16
    self.down = set()
    self.prev = set()
    self.bot = None
    self.frames = 0
    self.limit = 10 ** 9

  def mode(self, m):
    pass

  def pressed(self, b):
    return b in self.down and b not in self.prev

  def held(self, b):
    return b in self.down

  def released(self, b):
    return b in self.prev and b not in self.down

  def poll(self):
    pass

  def update(self):
    self.frames += 1
    if self.frames > self.limit:
      raise Stop()
    self.ticks += 16
    self.prev = self.down
    self.down = set(self.bot(self) if self.bot else ())


class Shape:
  def __getattr__(self, n):
    return lambda *a, **k: ("shape", n, a)


class Img:
  width = 48
  height = 48


class Screen:
  def __init__(self):
    self.font = None
    self.pen = None
    self.alpha = 255
    self.clip = (0, 0, 160, 120)
    self.antialias = 0

  def measure_text(self, s, *a, **k):
    h = getattr(self.font, "h", 12)
    return (len(s) * getattr(self.font, "cw", 6), h)

  def __getattr__(self, n):
    return lambda *a, **k: None


class Font:
  def __init__(self, cw, h):
    self.cw, self.h = cw, h


class Fonts:
  nope = Font(7, 13)
  yolk = Font(6, 11)
  desert = Font(5, 10)
  smart = Font(8, 16)


store = {}


class State:
  @staticmethod
  def load(name, d):
    if name in store:
      d.update(json.loads(store[name]))

  @staticmethod
  def save(name, d):
    store[name] = json.dumps(d)

  @staticmethod
  def delete(name):
    store.pop(name, None)


badge = Badge()
builtins.badge = badge
builtins.screen = Screen()
builtins.shape = Shape()
builtins.font = Fonts()
class Image(Screen):
  width = 48
  height = 48
  BILINEAR = 1

  def __init__(self, w=48, h=48):
    Screen.__init__(self)

  @staticmethod
  def load(p):
    if not os.path.exists(p.replace("/system/apps/pocket_mini_adventure", APP)):
      raise OSError(p)
    return Image()


builtins.image = Image
builtins.color = types.SimpleNamespace(rgb=lambda *a: a)
builtins.rect = lambda *a: a
bw = types.ModuleType("badgeware")
bw.State = State
sys.modules["badgeware"] = bw

SRC = open(os.path.join(APP, "__init__.py")).read()


def play(bot, frames, seed, ns_hook=None):
  random.seed(seed)
  badge.ticks = 0
  badge.frames = 0
  badge.limit = frames
  badge.down = set()
  badge.prev = set()
  ns = {"__name__": "pm"}
  badge.bot = lambda b: bot(ns, b)
  code = compile(SRC, "app/__init__.py", "exec")
  ns["exits"] = 0
  try:
    while True:          # quitting to the launcher just starts the app again
      fresh = {"__name__": "pm"}
      badge.bot = lambda b: bot(fresh, b)
      exec(code, fresh)
      ns.clear(); ns.update(fresh)
      play.exits = getattr(play, "exits", 0) + 1
  except Stop:
    ns.clear(); ns.update(fresh)
  return ns
