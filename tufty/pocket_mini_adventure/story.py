"""The story for the Tufty edition: who you meet, what they say, and the goal
each step sets. Hand-written, so edit freely; __init__.py only reads it.

Each step is one of:
  ("goal", condition, goal text, hint, lines when done, reward)
  ("battle", key, area or None, goal text, hint, trainer, team, before, after win, after loss, reward)

A condition is ("dex", n), ("badges", n), ("boss",) or ("legends", n).
An area is an index into pkdata.AREAS; the battle starts when you explore
there (or pick Story in town). area None starts it straight away.
A team entry ("RIVAL", lv) is Jay's starter, evolved as far as lv allows.
"after loss" is None when you must win; otherwise the story carries on.
A reward is a dict: {"balls": n, "gift": (species, level)}.
In lines, {rival} is Jay's starter's name and {mon} is your lead Pokemon's.
"""

# who talks: name, shirt colour, hair colour, the Pokemon at their side
PEOPLE = {
  "prof": ("Prof. Pine", (110, 160, 90), (190, 190, 200), "eevee"),
  "jay": ("Rival Jay", (70, 120, 230), (90, 60, 40), "RIVAL"),
  "grunt": ("Grumble Grunt", (110, 70, 150), (60, 50, 70), "koffing"),
  "admin": ("Admin Sludge", (130, 60, 120), (200, 80, 160), "arbok"),
  "boss": ("Boss Grumbleton", (60, 40, 90), (30, 30, 30), "gengar"),
  "champ": ("The Champion", (230, 180, 40), (250, 250, 250), "raichu"),
}

# your starter -> the one Jay picks, so he always has the edge
RIVAL_OF = {"pairi": "kkobugi", "kkobugi": "isanghae", "isanghae": "pairi"}

INTRO = (
  ("prof", "Hello! I'm Professor Pine. Welcome to the world of Pokemon!"),
  ("prof", "Lately a gang called Team Grumble has been scaring Pokemon all over town."),
  ("prof", "I need a brave helper. First, pick a Pokemon to be your buddy!"),
)

STEPS = (
  # 0
  ("battle", "jay1", None, "Battle your rival Jay!", "Jay is waiting right here in town.",
   "Rival Jay", (("RIVAL", 4),),
   (("jay", "Hey! I'm Jay. I picked {rival} because it's strong against yours!"),
    ("jay", "Let's see who's the better trainer. Battle!")),
   (("jay", "What?! You won? Okay... that was just a warm-up!"),
    ("prof", "Well done! Now catch some friends in the Grass. Here are 5 Poke Balls!")),
   (("jay", "Yes! I win! But you were pretty good. Let's both get stronger!"),
    ("prof", "Don't worry! Catch some friends in the Grass. Here are 5 Poke Balls!")),
   {"balls": 5}),
  # 1
  ("goal", ("dex", 3), "Catch 2 new Pokemon in the Grass", "Make them tired first, then throw a ball!",
   (("prof", "Great catching! A strong team wins badges."),
    ("prof", "Hiker Rocky waits in the Rock Cave. Beat him to win your first badge!")),
   {"balls": 3}),
  # 2 - opens the Rock Cave
  ("goal", ("badges", 1), "Win the Rock Cave badge", "Train in the Grass until your team is about Lv.10.",
   (("prof", "Your first badge! Oh no... I just heard Team Grumble is in the Flower Woods!"),
    ("prof", "Please go and see what they are up to!")),
   {}),
  # 3
  ("battle", "grunt1", 1, "Stop Team Grumble in the Flower Woods", "Explore the Flower Woods.",
   "Grumble Grunt", (("zubat", 9), ("ekans", 10)),
   (("grunt", "Grr! We're Team Grumble! We grumble at Pokemon until they run away!"),
    ("grunt", "You want us to stop? Make us!")),
   (("grunt", "Grumble grumble... The Boss won't like this! I'm out of here!"),
    ("prof", "You chased them off! I heard Jay is training at the Beach...")),
   None, {"balls": 3}),
  # 4
  ("battle", "jay2", 2, "Jay wants a rematch at the Beach", "Explore the Beach.",
   "Rival Jay", (("pijyon", 11), ("RIVAL", 12)),
   (("jay", "There you are! {rival} and I trained super hard. Rematch!"),),
   (("jay", "Argh, you beat me again! Oh, Prof. Pine is looking for you, by the way."),
    ("prof", "Could you help my research? Catch lots of different Pokemon and show me!")),
   None, {"balls": 3}),
  # 5
  ("goal", ("dex", 10), "Show Prof. Pine 10 kinds of Pokemon", "Explore different lands - each one has its own Pokemon!",
   (("prof", "10 kinds! My research is going great."),
    ("prof", "Now go see Swimmer Marina in the Ice Cave!")),
   {"balls": 5}),
  # 6 - opens the Ice Cave
  ("goal", ("badges", 2), "Win the Ice Cave badge", "Swimmer Marina loves Water Pokemon. Grass and Electric work well!",
   (("prof", "Two badges! But Team Grumble is back. They are in the Dark Forest now!"),),
   {}),
  # 7
  ("battle", "grunt2", 3, "Clear Team Grumble out of the Dark Forest", "Explore the Dark Forest.",
   "Grumble Grunt", (("koffing", 15), ("zubat", 15), ("ekans", 16)),
   (("grunt", "Hey! This forest is Grumble territory now. Scram!"),),
   (("grunt", "Ugh! My buddy deeper in the forest will stop you!"),),
   None, {"balls": 3}),
  # 8
  ("battle", "grunt3", 3, "Find the other Grunt in the Dark Forest", "Explore the Dark Forest again.",
   "Grumble Grunt", (("grimer", 16), ("gastly", 17)),
   (("grunt", "You beat my buddy? Grumble! Then I'll grumble at you twice as hard!"),),
   (("grunt", "No fair! ...The Boss wants to catch the Legend in the Legend Cave, you know!"),
    ("prof", "So that's their plan! Oh, look - a little Eevee they scared wants to come with you!"),
    ("prof", "Let's keep the research going while Team Grumble hides.")),
   None, {"balls": 3, "gift": ("eevee", 15)}),
  # 9
  ("goal", ("dex", 18), "Show Prof. Pine 18 kinds of Pokemon", "Explore different lands - each one has its own Pokemon!",
   (("prof", "18 kinds! You're a real Pokemon expert."),
    ("prof", "Fire Chief Blaze waits in the Fire Cave. Good luck!")),
   {"balls": 5}),
  # 10 - opens the Fire Cave
  ("goal", ("badges", 3), "Win the Fire Cave badge", "Fire Chief Blaze is tough. Water and Rock moves help!",
   (("prof", "Three badges, and a Mega Bracelet! Team Grumble's Admin is in the Swamp. Be careful!"),),
   {}),
  # 11
  ("battle", "admin", 4, "Beat Admin Sludge in the Swamp", "Explore the Swamp.",
   "Admin Sludge", (("golbat", 25), ("vileplume", 25), ("arbok", 26), ("haunter", 27)),
   (("admin", "So you're the kid who keeps beating my Grunts. How annoying!"),
    ("admin", "I'm Admin Sludge. Let's see you handle a real Grumble!")),
   (("admin", "Impossible! Boss Grumbleton will hear about this!"),
    ("prof", "Amazing! Now, more research: there are still so many Pokemon to meet!")),
   None, {"balls": 5}),
  # 12
  ("goal", ("dex", 25), "Show Prof. Pine 25 kinds of Pokemon", "Explore different lands - each one has its own Pokemon!",
   (("prof", "25 kinds! My notebook is almost full!"),
    ("prof", "Witch Luna is waiting in the Ghost Cave. Spooky!")),
   {"balls": 5}),
  # 13 - opens the Ghost Cave
  ("goal", ("badges", 4), "Win the Ghost Cave badge", "Ghosts are weak to Ghost moves. Normal moves barely touch them!",
   (("prof", "Four badges! Jay asked me where you are. He's on the Mountain!"),),
   {}),
  # 14
  ("battle", "jay3", 5, "Jay is waiting on the Mountain", "Explore the Mountain.",
   "Rival Jay", (("pidgeot", 30), ("arcanine", 31), ("RIVAL", 32)),
   (("jay", "I heard you beat Team Grumble's Admin. Cool. But I'm stronger now!"),),
   (("jay", "You're really good... Let's stop Team Grumble together!"),
    ("prof", "Before the last cave, one more round of research. You can do it!")),
   None, {"balls": 5}),
  # 15
  ("goal", ("dex", 32), "Show Prof. Pine 32 kinds of Pokemon", "Explore different lands - each one has its own Pokemon!",
   (("prof", "32 kinds! That's amazing research!"),
    ("prof", "The last badge is in the Dragon Cave. Dragon Master Kai is very strong!")),
   {"balls": 5}),
  # 16 - opens the Dragon Cave
  ("goal", ("badges", 5), "Win the Dragon Cave badge", "Dragon Master Kai's Dragons are weak to Dragon moves.",
   (("prof", "All five badges! Boss Grumbleton is at the Volcano. This is it!"),),
   {}),
  # 17
  ("battle", "boss", 7, "Stop Boss Grumbleton at the Volcano", "Explore the Volcano.",
   "Boss Grumbleton", (("arbok", 36), ("weezing", 37), ("muk", 38), ("gengar", 39)),
   (("boss", "So YOU are the kid who ruined everything. Grumble!"),
    ("boss", "Once I catch the Legend, everyone will grumble with me forever!")),
   (("boss", "NOOO! My grumbly plan! ...Fine. Team Grumble is done grumbling."),
    ("prof", "You did it! The Legend Cave is open. The Champion guards Mega Mewtwo X inside.")),
   None, {"balls": 10}),
  # 18 - opens the Legend Cave
  ("goal", ("boss",), "Beat the Champion and catch Mega Mewtwo X", "Go to Caves, then the Legend Cave. Bring a Lv.45 team!",
   (("champ", "I kept Mewtwo safe from Team Grumble. Now it has chosen you."),
    ("prof", "You're a hero! But Jay says he has one last challenge for you..."),
    ("prof", "He's waiting at the Snowy Peak.")),
   {"balls": 10}),
  # 19
  ("battle", "jay4", 6, "Jay's final battle at the Snowy Peak", "Explore the Snowy Peak.",
   "Rival Jay", (("pidgeot", 48), ("alakazam", 49), ("exeggutor", 49), ("arcanine", 50), ("garados", 50), ("RIVAL", 52)),
   (("jay", "Champion of the whole town, huh? Then beat my best team ever!"),),
   (("jay", "You're the best, for real. Thanks for being my rival!"),
    ("prof", "Now a real Pokemon Master's quest: legendary Pokemon hide in every land!")),
   None, {"balls": 10}),
  # 20
  ("goal", ("legends", 3), "Catch 3 legendary Pokemon", "Each land has a rare legend. Keep exploring!",
   (("prof", "Three legends! Incredible. One last thing: can you meet 100 kinds of Pokemon?"),),
   {"balls": 20}),
  # 21
  ("goal", ("dex", 100), "Catch 100 kinds of Pokemon", "Check your Pokedex to see who is missing.",
   (("prof", "100 kinds! You are a true Pokemon Master. Thank you for everything!"),
    ("jay", "Pokemon Master... I'll catch up someday!")),
   {"balls": 20}),
)

# the step from which each cave opens; the Legend Cave is index 5
CAVE_OPENS_AT = (2, 6, 10, 13, 16, 18)

# where an older save picks the story back up: by badges won, then the end
RESUME_AT_BADGES = (0, 3, 7, 11, 14, 17)
RESUME_AFTER_BOSS = 19
