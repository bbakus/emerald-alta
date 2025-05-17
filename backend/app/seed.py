from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Class_, Enemy, Move, Item
import os

# Create engine with absolute path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emerald_altar.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# ======= CLASSES =======

classes = [
    Class_(
        name="Revolutionary",
        hp=110, mp=30, armor_class=14,
        str=4, dex=3, speed=2,
        wisdom=0, intelligence=1, constitution=3,
        charisma=2, initiative=2,
        passive="Ricochet — gains bonus damage against multiple targets",
        description="Veteran fighters of the revolution who now turn their wrath against the supernatural. Agile and clever with improvised weapons."
    ),
    Class_(
        name="Bruja",
        hp=80, mp=120, armor_class=10,
        str=-1, dex=1, speed=0,
        wisdom=5, intelligence=3, constitution=0,
        charisma=4, initiative=0,
        passive="Blood Sigil — heals when status effects are inflicted",
        description="Occult spellcasters who channel blood and curses. Masters of hexes, healing, and ritual magic."
    ),
    Class_(
        name="Priest of the Black Flame",
        hp=100, mp=80, armor_class=13,
        str=1, dex=0, speed=-1,
        wisdom=4, intelligence=2, constitution=2,
        charisma=4, initiative=0,
        passive="Exorcist's Will — resistant to curse and fear",
        description="Devout exorcists wielding sacred fire to banish darkness. Resilient against curses and fear, they protect the living."
    ),
    Class_(
        name="Occult Archaeologist",
        hp=90, mp=100, armor_class=11,
        str=0, dex=2, speed=1,
        wisdom=3, intelligence=5, constitution=0,
        charisma=1, initiative=2,
        passive="Runesight — glyphs reveal hidden weaknesses",
        description="Scholars and explorers deciphering forbidden glyphs. Their knowledge exposes enemy weaknesses and unlocks ancient powers."
    ),
    Class_(
        name="Streetfighter",
        hp=130, mp=30, armor_class=16,
        str=5, dex=2, speed=2,
        wisdom=-1, intelligence=-1, constitution=4,
        charisma=0, initiative=3,
        passive="Adrenaline Rush — strength increases as HP drops",
        description="Tough survivors from the city's underbelly. Excel in brawling, improvisation, and thrive when wounded."
    )
]

session.add_all(classes)
session.commit()

# ======= CLASS MOVES =======
class_moves = [
    # Revolutionary moves
    Move(
        name="Molotov Toss",
        description="Hurl a flaming bottle that explodes on impact, dealing damage to all enemies in the area.",
        damage=15,
        mana_cost=10,
        status_effect="burning",
        condition="multiple targets",
        lore_description="A signature weapon of the revolution, now used to purge supernatural threats."
    ),
    Move(
        name="Guerrilla Strike",
        description="A swift, precise attack that deals bonus damage to isolated targets.",
        damage=20,
        mana_cost=5,
        condition="single target",
        lore_description="The art of striking when the enemy is most vulnerable."
    ),
    Move(
        name="Rally Cry",
        description="Inspire allies, increasing their damage for the next turn.",
        damage=0,
        mana_cost=15,
        status_effect="inspired",
        lore_description="The battle cry that once rallied revolutionaries now empowers the fight against darkness."
    ),

    # Bruja moves
    Move(
        name="Blood Curse",
        description="Inflict a curse that drains health over time.",
        damage=10,
        mana_cost=20,
        status_effect="cursed",
        lore_description="Ancient blood magic passed down through generations of witches."
    ),
    Move(
        name="Healing Ritual",
        description="Restore health to all allies.",
        damage=-20,
        mana_cost=25,
        lore_description="A sacred ritual that channels life force to mend wounds."
    ),
    Move(
        name="Hex Bolt",
        description="Launch a bolt of dark energy that can silence enemies.",
        damage=15,
        mana_cost=15,
        status_effect="silenced",
        lore_description="Dark energy shaped by the will of the bruja."
    ),

    # Priest of the Black Flame moves
    Move(
        name="Sacred Fire",
        description="Channel holy fire to burn enemies and cleanse allies.",
        damage=18,
        mana_cost=20,
        status_effect="purified",
        lore_description="The sacred flame that burns away corruption."
    ),
    Move(
        name="Exorcism",
        description="Attempt to banish a supernatural entity.",
        damage=25,
        mana_cost=30,
        condition="supernatural target",
        lore_description="The ultimate weapon against the forces of darkness."
    ),
    Move(
        name="Divine Shield",
        description="Create a protective barrier that reduces incoming damage.",
        damage=0,
        mana_cost=15,
        status_effect="protected",
        lore_description="A manifestation of divine protection."
    ),

    # Occult Archaeologist moves
    Move(
        name="Decipher Glyph",
        description="Study enemy patterns to reveal weaknesses.",
        damage=0,
        mana_cost=10,
        status_effect="exposed",
        lore_description="Ancient knowledge used to expose vulnerabilities."
    ),
    Move(
        name="Artifact Blast",
        description="Channel the power of a discovered artifact.",
        damage=20,
        mana_cost=25,
        lore_description="The power of forgotten relics unleashed."
    ),
    Move(
        name="Field Study",
        description="Analyze the battlefield to gain tactical advantage.",
        damage=0,
        mana_cost=15,
        status_effect="enlightened",
        lore_description="Scholarly observation turned to tactical advantage."
    ),

    # Streetfighter moves
    Move(
        name="Dirty Strike",
        description="A brutal attack that can stun enemies.",
        damage=18,
        mana_cost=5,
        status_effect="stunned",
        lore_description="The art of fighting dirty, perfected in the streets."
    ),
    Move(
        name="Adrenaline Surge",
        description="Temporarily increase strength and speed.",
        damage=0,
        mana_cost=15,
        status_effect="empowered",
        lore_description="The rush of combat that turns pain into power."
    ),
    Move(
        name="Street Smarts",
        description="Use the environment to gain an advantage.",
        damage=12,
        mana_cost=10,
        condition="environmental advantage",
        lore_description="The wisdom of the streets, where every object is a weapon."
    )
]

session.add_all(class_moves)
session.commit()

# Associate class moves with their respective classes
revolutionary = session.query(Class_).filter_by(name="Revolutionary").first()
bruja = session.query(Class_).filter_by(name="Bruja").first()
priest = session.query(Class_).filter_by(name="Priest of the Black Flame").first()
archaeologist = session.query(Class_).filter_by(name="Occult Archaeologist").first()
streetfighter = session.query(Class_).filter_by(name="Streetfighter").first()

revolutionary_moves = session.query(Move).filter(Move.name.in_(["Molotov Toss", "Guerrilla Strike", "Rally Cry"])).all()
bruja_moves = session.query(Move).filter(Move.name.in_(["Blood Curse", "Healing Ritual", "Hex Bolt"])).all()
priest_moves = session.query(Move).filter(Move.name.in_(["Sacred Fire", "Exorcism", "Divine Shield"])).all()
archaeologist_moves = session.query(Move).filter(Move.name.in_(["Decipher Glyph", "Artifact Blast", "Field Study"])).all()
streetfighter_moves = session.query(Move).filter(Move.name.in_(["Dirty Strike", "Adrenaline Surge", "Street Smarts"])).all()

revolutionary.moves.extend(revolutionary_moves)
bruja.moves.extend(bruja_moves)
priest.moves.extend(priest_moves)
archaeologist.moves.extend(archaeologist_moves)
streetfighter.moves.extend(streetfighter_moves)

session.commit()

# ======= ENEMY-SPECIFIC MOVES =======
enemy_moves = [
    # Basic enemy moves
    Move(
        name="Venomous Gaze",
        description="A hypnotic stare that can paralyze or confuse the target.",
        damage=0,
        mana_cost=15,
        status_effect="paralyze",
        condition="must maintain eye contact",
        lore_description="The gaze of a supernatural being that can freeze mortals in place."
    ),
    Move(
        name="Life Drain",
        description="Steals life force from the target, healing the user.",
        damage=15,
        mana_cost=20,
        status_effect="drain",
        condition="target must be within range",
        lore_description="A dark art that siphons the essence of life itself."
    ),
    Move(
        name="Tail Lash",
        description="A powerful strike from the hand at the end of the tail.",
        damage=20,
        mana_cost=10,
        status_effect="stun",
        condition="close range",
        lore_description="The hand at the end of the tail strikes with supernatural precision."
    ),
    # Add more enemy-specific moves here
]
session.add_all(enemy_moves)
session.commit()

# ======= ENEMIES =======
# First Wave
first_wave_enemies = [
    Enemy(name="Jaguar Hybrid", description="A tactical predator once human, now twisted into a sleek killing machine.",
          lore_description="A tactical predator once human, now twisted into a sleek killing machine.",
          hp=90, mp=10, armor_class=14, str=5, dex=5, speed=4, wisdom=1, intelligence=2,
          constitution=4, charisma=1, initiative=4),
    Enemy(name="Feathered Serpent", description="A winged serpent exuding hypnotic venom and corrupted charisma.",
          lore_description="A winged serpent exuding hypnotic venom and corrupted charisma.",
          hp=80, mp=50, armor_class=14, str=2, dex=5, speed=5, wisdom=3, intelligence=4,
          constitution=2, charisma=5, initiative=4),
    Enemy(name="Skull Harvester", description="A skeletal healer corrupted to collect life essence.",
          lore_description="A skeletal healer corrupted to collect life essence.",
          hp=90, mp=40, armor_class=14, str=4, dex=3, speed=3, wisdom=5, intelligence=3,
          constitution=3, charisma=1, initiative=2),
    Enemy(name="Market Phantom", description="A vendor's cursed spirit lures victims with illusory wealth.",
          lore_description="A vendor's cursed spirit lures victims with illusory wealth.",
          hp=80, mp=50, armor_class=12, str=3, dex=4, speed=4, wisdom=4, intelligence=4,
          constitution=2, charisma=5, initiative=3),
    Enemy(name="Codex Wraith", description="A floating scholar wreathed in glyphs, draining memory by touch.",
          lore_description="A floating scholar wreathed in glyphs, draining memory by touch.",
          hp=70, mp=60, armor_class=12, str=2, dex=3, speed=3, wisdom=5, intelligence=5,
          constitution=2, charisma=3, initiative=3),
    Enemy(name="Ahuizotl", description="A water beast with a hand at the end of its tail, hungering for eyes.",
          lore_description="A water beast with a hand at the end of its tail, hungering for eyes.",
          hp=90, mp=20, armor_class=14, str=4, dex=4, speed=4, wisdom=3, intelligence=2,
          constitution=5, charisma=2, initiative=4),
]
session.add_all(first_wave_enemies)
session.commit()

# Associate moves with first wave enemies
jaguar_hybrid = session.query(Enemy).filter_by(name="Jaguar Hybrid").first()
feathered_serpent = session.query(Enemy).filter_by(name="Feathered Serpent").first()
skull_harvester = session.query(Enemy).filter_by(name="Skull Harvester").first()
market_phantom = session.query(Enemy).filter_by(name="Market Phantom").first()
codex_wraith = session.query(Enemy).filter_by(name="Codex Wraith").first()
ahuizotl = session.query(Enemy).filter_by(name="Ahuizotl").first()

# Get moves for first wave enemies
jaguar_moves = session.query(Move).filter(Move.name.in_([
    "Jaguar Pounce",
    "Dirty Strike",
    "Guerrilla Strike"
])).all()

serpent_moves = session.query(Move).filter(Move.name.in_([
    "Venomous Gaze",
    "Hex Bolt",
    "Blood Curse"
])).all()

harvester_moves = session.query(Move).filter(Move.name.in_([
    "Life Drain",
    "Blood Curse",
    "Healing Ritual"
])).all()

phantom_moves = session.query(Move).filter(Move.name.in_([
    "Hex Bolt",
    "Venomous Gaze",
    "Blood Curse"
])).all()

wraith_moves = session.query(Move).filter(Move.name.in_([
    "Life Drain",
    "Decipher Glyph",
    "Artifact Blast"
])).all()

ahuizotl_moves = session.query(Move).filter(Move.name.in_([
    "Tail Lash",
    "Dirty Strike",
    "Jaguar Pounce"
])).all()

# Associate moves with first wave enemies
if jaguar_hybrid:
    jaguar_hybrid.moves.extend(jaguar_moves)
if feathered_serpent:
    feathered_serpent.moves.extend(serpent_moves)
if skull_harvester:
    skull_harvester.moves.extend(harvester_moves)
if market_phantom:
    market_phantom.moves.extend(phantom_moves)
if codex_wraith:
    codex_wraith.moves.extend(wraith_moves)
if ahuizotl:
    ahuizotl.moves.extend(ahuizotl_moves)

session.commit()

# ======= ITEMS =======

items = [
    Item(name="Rusty Machete", type="weapon", weight=3, effect_description="An old revolutionary blade. Still cuts.",
         lore_description="Carried by a dozen ghosts. You can still feel their grip on the handle.",
         image_url="https://storage.googleapis.com/pai-images/bccf32fc42e644fd864de16fdb069a37.jpeg",
         armor_class=0, str=2, dex=0, speed=0, wisdom=-1, intelligence=-1, constitution=0,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    Item(name="Bruja's Totem", type="trinket", weight=1, effect_description="Increases curse resistance and blood magic potency.",
         lore_description="A fetish carved from bone and obsidian, humming with power.",
         image_url="https://storage.googleapis.com/pai-images/6c4a6eaf54284a1e819478b8c9f0d352.jpeg",
         armor_class=0, str=-1, dex=0, speed=0, wisdom=3, intelligence=2, constitution=0,
         charisma=1, initiative=0, equippable=True, is_equipped=False),
    Item(name="Field Journal", type="accessory", weight=2, effect_description="Used by archaeologists to translate glyphs.",
         lore_description="Pages are filled with frantic notes, some written in a trembling hand.",
         image_url="https://storage.googleapis.com/pai-images/3e31cc5ec5394982a47c77f1fa5a6d00.jpeg",
         armor_class=0, str=0, dex=0, speed=0, wisdom=2, intelligence=3, constitution=-1,
         charisma=0, initiative=0, equippable=True, is_equipped=False),
    Item(name="Blessed Rosary", type="necklace", weight=1, effect_description="Grants temporary invulnerability to fear effects.",
         lore_description="Each bead is etched with prayers against the darkness.",
         image_url="https://storage.googleapis.com/pai-images/00bd93b1b8dc442a99e1f2ce2afbc7d5.jpeg",
         armor_class=0, str=0, dex=0, speed=-1, wisdom=3, intelligence=1, constitution=1,
         charisma=1, initiative=0, equippable=True, is_equipped=False),
    Item(name="Streetfighter's Gloves", type="armor", weight=4, effect_description="Boosts strength when below 50% HP.",
         lore_description="Bloodstained and cracked, they pulse with adrenaline.",
         armor_class=1, str=3, dex=1, speed=0, wisdom=-1, intelligence=-1, constitution=2,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    # Boss loot
    Item(name="Emerald Fracture Blade", type="weapon", weight=6, effect_description="Forged from Cizin's core, trembles with unholy power.",
         lore_description="A sword that hums with the agony of the dead.",
         armor_class=0, str=3, dex=0, speed=0, wisdom=-1, intelligence=-1, constitution=2,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    Item(name="Rainbow Veil", type="cloak", weight=2, effect_description="Once worn by Ixchel, distorts reality around the wearer.",
         lore_description="Shifts color in the corner of your eye. Sometimes you see faces.",
         armor_class=2, str=-1, dex=2, speed=2, wisdom=1, intelligence=0, constitution=-1,
         charisma=2, initiative=1, equippable=True, is_equipped=False),
    Item(name="Jaguar Mask of Xbalanque", type="helm", weight=3, effect_description="Allows stealth in darkness. Whispers in your dreams.",
         lore_description="The mask is warm and smells of blood and wet earth.",
         armor_class=1, str=1, dex=3, speed=1, wisdom=0, intelligence=0, constitution=1,
         charisma=-1, initiative=2, equippable=True, is_equipped=False),
    Item(name="Obsidian Heart", type="artifact", weight=1, effect_description="An unstable shard from Xibalba's core. Terrifying but powerful.",
         lore_description="It beats faintly in your palm, echoing the underworld.",
         armor_class=0, str=0, dex=-1, speed=-1, wisdom=3, intelligence=3, constitution=0,
         charisma=-1, initiative=0, equippable=True, is_equipped=False),
    Item(name="Tunic of the Wind", type="armor", weight=2, effect_description="Gifted by Kukulkan's Avatar. Increases movement and dodge chance.",
         lore_description="Threads shimmer like a distant storm. You feel lighter.",
         armor_class=1, str=-1, dex=3, speed=3, wisdom=0, intelligence=0, constitution=-1,
         charisma=1, initiative=2, equippable=True, is_equipped=False),
]

session.add_all(items)
session.commit()

# ======= SECOND WAVE ENEMIES =======
second_wave_enemies = [
    Enemy(name="Tzitzimitl", description="A star demon born from apocalyptic corruption, cloaked in solar death flame.",
          lore_description="A star demon born from apocalyptic corruption, cloaked in solar death flame.",
          hp=100, mp=80, armor_class=16, str=5, dex=3, speed=2, wisdom=5, intelligence=4,
          constitution=5, charisma=1, initiative=3),
    Enemy(name="Chaneque", description="A mischievous nature spirit born of lost children, steals shadows with a whisper.",
          lore_description="A mischievous nature spirit born of lost children, steals shadows with a whisper.",
          hp=60, mp=50, armor_class=14, str=1, dex=5, speed=5, wisdom=4, intelligence=3,
          constitution=1, charisma=3, initiative=5),
    Enemy(name="Cihuateteo", description="The restless dead of women lost in childbirth, screaming at crossroads.",
          lore_description="The restless dead of women lost in childbirth, screaming at crossroads.",
          hp=80, mp=60, armor_class=12, str=3, dex=4, speed=4, wisdom=5, intelligence=4,
          constitution=3, charisma=5, initiative=3),
    Enemy(name="Nagual", description="A cursed shaman capable of transforming into jaguar form and bending light.",
          lore_description="A cursed shaman capable of transforming into jaguar form and bending light.",
          hp=90, mp=80, armor_class=14, str=4, dex=5, speed=4, wisdom=5, intelligence=5,
          constitution=3, charisma=2, initiative=4),
    Enemy(name="Cipactli", description="A crocodilian horror with mouths at every joint, fueled by unending hunger.",
          lore_description="A crocodilian horror with mouths at every joint, fueled by unending hunger.",
          hp=110, mp=20, armor_class=16, str=5, dex=2, speed=2, wisdom=1, intelligence=1,
          constitution=5, charisma=0, initiative=1),
]
session.add_all(second_wave_enemies)
session.commit()

# ======= SECOND WAVE MOVES =======
second_wave_moves = [
    Move(name="Shadow Snatch", description="Steals part of the target's shadow, reducing their speed.", 
         lore_description="Chaneque steal shadows, leaving their victims weak and slow.", 
         damage=5, mana_cost=7, status_effect="slow", condition="usable by Chaneque"),
    Move(name="Crossroads Howl", description="A piercing scream that may paralyze all who hear it.", 
         lore_description="The Cihuateteo's wail chills the soul and stops the heart.", 
         damage=0, mana_cost=15, status_effect="paralyze", condition="usable by Cihuateteo"),
    Move(name="Starfire Flare", description="Summons falling stars to scorch the battlefield.", 
         lore_description="Tzitzimitl calls down stellar fire to burn all below.", 
         damage=20, mana_cost=25, status_effect="burn", condition="daylight"),
    Move(name="Devouring Maw", description="A mouth opens on the attacker's arm to consume target HP.", 
         lore_description="Cipactli's hunger is endless; it devours flesh and soul.", 
         damage=16, mana_cost=5, status_effect="drain", condition="if target is below 50% HP"),
    Move(name="Soul Echo", description="Repeats the last spell cast on the caster's next turn.", 
         lore_description="Naguals echo the world's magic, repeating what was done.", 
         damage=0, mana_cost=8, status_effect="repeat", condition="usable by Nagual"),
    Move(name="Quake Stomp", description="Creates a localized tremor that can knock targets prone.", 
         lore_description="Cipactli's step shakes the earth, toppling the weak.", 
         damage=10, mana_cost=10, status_effect="knockdown", condition="usable by Cipactli"),
]
session.add_all(second_wave_moves)
session.commit()

# Associate moves with second wave enemies
tzitzimitl = session.query(Enemy).filter_by(name="Tzitzimitl").first()
chaneque = session.query(Enemy).filter_by(name="Chaneque").first()
cihuateteo = session.query(Enemy).filter_by(name="Cihuateteo").first()
nagual = session.query(Enemy).filter_by(name="Nagual").first()
cipactli = session.query(Enemy).filter_by(name="Cipactli").first()

# Get moves for second wave enemies
tzitzimitl_moves = session.query(Move).filter(Move.name.in_([
    "Starfire Flare",
    "Mirror Fracture",
    "Lava Spit"
])).all()

chaneque_moves = session.query(Move).filter(Move.name.in_([
    "Shadow Snatch",
    "Mist Lure",
    "Venomous Gaze"
])).all()

cihuateteo_moves = session.query(Move).filter(Move.name.in_([
    "Crossroads Howl",
    "Bitter Whisper",
    "Blood Curse"
])).all()

nagual_moves = session.query(Move).filter(Move.name.in_([
    "Jaguar Pounce",
    "Soul Echo",
    "Hex Bolt"
])).all()

cipactli_moves = session.query(Move).filter(Move.name.in_([
    "Devouring Maw",
    "Quake Stomp",
    "Earthen Maw"
])).all()

# Associate moves with second wave enemies
if tzitzimitl:
    tzitzimitl.moves.extend(tzitzimitl_moves)
if chaneque:
    chaneque.moves.extend(chaneque_moves)
if cihuateteo:
    cihuateteo.moves.extend(cihuateteo_moves)
if nagual:
    nagual.moves.extend(nagual_moves)
if cipactli:
    cipactli.moves.extend(cipactli_moves)

session.commit()

# ======= SECOND WAVE ITEMS =======
second_wave_items = [
    Item(name="Tzitzimitl Fragment", type="artifact", weight=1, effect_description="A sliver of star-demon bone, crackling with raw power.",
         lore_description="It hums and burns against your skin, eager for battle.",
         armor_class=0, str=2, dex=-1, speed=-1, wisdom=3, intelligence=0, constitution=2,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    Item(name="Nagual Pelt Cloak", type="cloak", weight=2, effect_description="Allows limited transformation into spirit form.",
         lore_description="Strips of fur and hide, woven with spirit threads.",
         armor_class=1, str=0, dex=2, speed=2, wisdom=1, intelligence=1, constitution=-1,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    Item(name="Tooth of Cipactli", type="weapon", weight=5, effect_description="Massive jagged tooth used as a blade. Hungers with each swing.",
         lore_description="It vibrates in your hand, eager to bite.",
         armor_class=0, str=3, dex=-1, speed=-1, wisdom=0, intelligence=-1, constitution=2,
         charisma=0, initiative=0, equippable=True, is_equipped=False),
    Item(name="Grieving Veil", type="helm", weight=1, effect_description="Worn by mourning spirits. Protects from madness.",
         lore_description="The fabric is cold and damp with ghostly tears.",
         armor_class=1, str=-1, dex=0, speed=1, wisdom=2, intelligence=2, constitution=0,
         charisma=1, initiative=0, equippable=True, is_equipped=False),
    Item(name="Shadow Flute", type="accessory", weight=1, effect_description="Played by Chaneque to entrance or escape.", 
         lore_description="Carved from bone, its notes linger in the dark.",
         armor_class=0, str=-1, dex=1, speed=1, wisdom=0, intelligence=1, constitution=0,
         charisma=3, initiative=1, equippable=True, is_equipped=False),
]
session.add_all(second_wave_items)
session.commit()

print("Second wave of enemies, moves, and items seeded.")

# ======= THIRD WAVE ENEMIES =======
third_wave_enemies = [
    Enemy(name="Ehecatl Servant", description="A wind spirit with avian traits, spreading chaos with each step.",
          lore_description="A wind spirit with avian traits, spreading chaos with each step.",
          hp=80, mp=50, armor_class=12, str=2, dex=5, speed=5, wisdom=4, intelligence=3,
          constitution=2, charisma=3, initiative=5),
    Enemy(name="Xolotl Hound", description="A skeletal canine with backward feet that guards the dead.",
          lore_description="A skeletal canine with backward feet that guards the dead.",
          hp=90, mp=10, armor_class=14, str=5, dex=3, speed=3, wisdom=3, intelligence=2,
          constitution=4, charisma=1, initiative=2),
    Enemy(name="Mictlantecuhtli Acolyte", description="A spectral undertaker swathed in death banners.",
          lore_description="A spectral undertaker swathed in death banners.",
          hp=90, mp=60, armor_class=14, str=2, dex=2, speed=3, wisdom=5, intelligence=4,
          constitution=3, charisma=1, initiative=3),
    Enemy(name="Mixcoatl Archer", description="A ghostly hunter with star-speckled skin and bone arrows.",
          lore_description="A ghostly hunter with star-speckled skin and bone arrows.",
          hp=80, mp=40, armor_class=13, str=4, dex=5, speed=4, wisdom=3, intelligence=4,
          constitution=3, charisma=2, initiative=4),
    Enemy(name="Tlaltecuhtli Maw", description="An earth-devouring horror that opens its gullet beneath your feet.",
          lore_description="An earth-devouring horror that opens its gullet beneath your feet.",
          hp=110, mp=0, armor_class=16, str=5, dex=1, speed=1, wisdom=2, intelligence=1,
          constitution=5, charisma=0, initiative=1),
]
session.add_all(third_wave_enemies)
session.commit()

# ======= THIRD WAVE MOVES =======
third_wave_moves = [
    Move(name="Wind Lash", description="A slicing gust that knocks enemies back.", 
         lore_description="Ehecatl's servants whip up razor winds to scatter foes.", 
         damage=11, mana_cost=6, status_effect="push", condition=None),
    Move(name="Grave Bind", description="Spectral bands erupt from the floor, rooting targets in place.", 
         lore_description="The dead reach up to grasp the living, holding them fast.", 
         damage=0, mana_cost=10, status_effect="root", condition="on corpse terrain"),
    Move(name="Echoing Bark", description="A dissonant howl that saps enemy initiative.", 
         lore_description="Xolotl Hounds bark and the living hesitate.", 
         damage=5, mana_cost=3, status_effect="initiative down", condition=None),
    Move(name="Meteor Shot", description="A flaming bone arrow crashes like a comet.", 
         lore_description="Mixcoatl Archers fire arrows that blaze like falling stars.", 
         damage=22, mana_cost=15, status_effect="burn", condition="must be used outdoors"),
    Move(name="Earthen Maw", description="Opens a gaping pit to swallow a nearby foe whole.", 
         lore_description="Tlaltecuhtli's hunger is bottomless, swallowing all.", 
         damage=25, mana_cost=20, status_effect="disable", condition="close range"),
    Move(name="Luminous Veil", description="Wraps the caster in shimmering glyphs that reduce spell damage.", 
         lore_description="Glyphs shimmer and deflect incoming spells.", 
         damage=0, mana_cost=8, status_effect="spell resist", condition="usable if below 50% MP"),
    Move(name="Quetzal Rush", description="Blindingly fast charge that pierces armor.", 
         lore_description="A flash of feathers and wind, nothing withstands the charge.", 
         damage=14, mana_cost=7, status_effect="armor break", condition=None),
    Move(name="Bitter Whisper", description="Inflicts confusion by channeling voices of the dead.", 
         lore_description="Acolytes of Mictlantecuhtli murmur secrets that unravel sanity.", 
         damage=6, mana_cost=6, status_effect="confuse", condition="usable by Mictlantecuhtli Acolyte"),
]
session.add_all(third_wave_moves)
session.commit()

# Associate moves with third wave enemies
ehecatl = session.query(Enemy).filter_by(name="Ehecatl Servant").first()
xolotl = session.query(Enemy).filter_by(name="Xolotl Hound").first()
mictlantecuhtli = session.query(Enemy).filter_by(name="Mictlantecuhtli Acolyte").first()
mixcoatl = session.query(Enemy).filter_by(name="Mixcoatl Archer").first()
tlaltecuhtli = session.query(Enemy).filter_by(name="Tlaltecuhtli Maw").first()

# Get moves for third wave enemies
ehecatl_moves = session.query(Move).filter(Move.name.in_([
    "Wind Lash",
    "Quetzal Rush",
    "Luminous Veil"
])).all()

xolotl_moves = session.query(Move).filter(Move.name.in_([
    "Echoing Bark",
    "Grave Bind",
    "Bitter Whisper"
])).all()

mictlantecuhtli_moves = session.query(Move).filter(Move.name.in_([
    "Bitter Whisper",
    "Grave Bind",
    "Blood Curse"
])).all()

mixcoatl_moves = session.query(Move).filter(Move.name.in_([
    "Meteor Shot",
    "Quetzal Rush",
    "Luminous Veil"
])).all()

tlaltecuhtli_moves = session.query(Move).filter(Move.name.in_([
    "Earthen Maw",
    "Quake Stomp",
    "Devouring Maw"
])).all()

# Associate moves with third wave enemies
if ehecatl:
    ehecatl.moves.extend(ehecatl_moves)
if xolotl:
    xolotl.moves.extend(xolotl_moves)
if mictlantecuhtli:
    mictlantecuhtli.moves.extend(mictlantecuhtli_moves)
if mixcoatl:
    mixcoatl.moves.extend(mixcoatl_moves)
if tlaltecuhtli:
    tlaltecuhtli.moves.extend(tlaltecuhtli_moves)

session.commit()

# ======= THIRD WAVE ITEMS =======
third_wave_items = [
    Item(name="Glyph-Bound Ring", type="accessory", weight=1, effect_description="Magical runes engraved into obsidian. Boosts casting speed.",
         lore_description="The runes shift and flicker, never quite readable.",
         armor_class=0, str=-1, dex=0, speed=1, wisdom=2, intelligence=3, constitution=0,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    Item(name="Ehecatl Feather", type="trinket", weight=0, effect_description="A blessed wind-feather, enhances agility and reflex.",
         lore_description="Light as air, it always points toward the nearest storm.",
         armor_class=0, str=-1, dex=2, speed=3, wisdom=0, intelligence=1, constitution=-1,
         charisma=0, initiative=2, equippable=True, is_equipped=False),
    Item(name="Bone Quiver", type="back", weight=2, effect_description="Holds arrows that phase through armor.",
         lore_description="The bones rattle, even when empty.",
         armor_class=0, str=0, dex=2, speed=0, wisdom=0, intelligence=1, constitution=0,
         charisma=-1, initiative=2, equippable=True, is_equipped=False),
    Item(name="Obsidian Sun Pendant", type="necklace", weight=1, effect_description="Protects from death magic. Warm to the touch.",
         lore_description="A black sun glimmers at its center, warding off the grave.",
         armor_class=1, str=0, dex=0, speed=-1, wisdom=2, intelligence=1, constitution=2,
         charisma=1, initiative=0, equippable=True, is_equipped=False),
    Item(name="Burial Mask of Mixcoatl", type="helm", weight=3, effect_description="Worn by hunters of the void. Reveals hidden paths.",
         lore_description="Cold and heavy, it shows you more than you wish to see.",
         armor_class=1, str=1, dex=2, speed=1, wisdom=1, intelligence=1, constitution=0,
         charisma=-1, initiative=1, equippable=True, is_equipped=False),
]
session.add_all(third_wave_items)
session.commit()

print("Third wave of enemies, moves, and items seeded.")

# ======= FOURTH WAVE ENEMIES =======
fourth_wave_enemies = [
    Enemy(name="Tezcatlipoca's Shade", description="A spectral fragment of the smoking mirror god, wrapped in obsidian and shadow.",
          lore_description="A spectral fragment of the smoking mirror god, wrapped in obsidian and shadow.",
          hp=100, mp=80, armor_class=16, str=4, dex=4, speed=3, wisdom=5, intelligence=5,
          constitution=3, charisma=4, initiative=4),
    Enemy(name="Itzpapalotl", description="Obsidian butterfly queen with bone wings and talons sharp enough to slice souls.",
          lore_description="Obsidian butterfly queen with bone wings and talons sharp enough to slice souls.",
          hp=90, mp=70, armor_class=14, str=4, dex=5, speed=5, wisdom=5, intelligence=4,
          constitution=3, charisma=5, initiative=4),
    Enemy(name="Camazotz Spawn", description="A lesser blood bat created from ritual sacrifice, blind but relentless.",
          lore_description="A lesser blood bat created from ritual sacrifice, blind but relentless.",
          hp=80, mp=40, armor_class=12, str=4, dex=5, speed=4, wisdom=3, intelligence=2,
          constitution=3, charisma=1, initiative=3),
    Enemy(name="Obsidian Sentinel", description="A living statue placed at sacred sites, animated by ancient rites.",
          lore_description="A living statue placed at sacred sites, animated by ancient rites.",
          hp=120, mp=0, armor_class=16, str=5, dex=1, speed=1, wisdom=3, intelligence=1,
          constitution=5, charisma=0, initiative=0),
    Enemy(name="Xibalban Scribe", description="An undead record-keeper who writes curses into reality.",
          lore_description="An undead record-keeper who writes curses into reality.",
          hp=90, mp=80, armor_class=12, str=1, dex=3, speed=3, wisdom=5, intelligence=5,
          constitution=3, charisma=2, initiative=3),
]
session.add_all(fourth_wave_enemies)
session.commit()

# ======= FOURTH WAVE MOVES =======
fourth_wave_moves = [
    Move(name="Mirror Fracture", description="Shatters an illusionary mirror to deal psychic backlash.", 
         lore_description="Fragments of the mirror god's power drive foes mad.", 
         damage=17, mana_cost=12, status_effect="confuse", condition="usable by Tezcatlipoca's Shade"),
    Move(name="Soul Shred", description="Itzpapalotl's wing slice deals damage to HP and MP simultaneously.", 
         lore_description="Obsidian wings cut deeper than flesh, severing spirit.", 
         damage=14, mana_cost=15, status_effect="drain", condition="usable by Itzpapalotl"),
    Move(name="Blind Dive", description="A reckless plunge from above that deals heavy damage but stuns the user.", 
         lore_description="Camazotz Spawn crash down, heedless of pain.", 
         damage=18, mana_cost=5, status_effect="self-stun", condition="usable by Camazotz Spawn"),
    Move(name="Stone Fist", description="A slow but devastating strike that can fracture armor.", 
         lore_description="Sentinels move ponderously, but with crushing force.", 
         damage=20, mana_cost=0, status_effect="armor break", condition="melee only"),
    Move(name="Curse Glyph", description="Inscribes a symbol mid-battle that inflicts a random status.", 
         lore_description="A scribe's glyph twists fate with every stroke.", 
         damage=0, mana_cost=10, status_effect="random", condition="usable by Xibalban Scribe"),
    Move(name="Temporal Ripple", description="Slows the flow of time for enemies for one turn.", 
         lore_description="A ripple warps seconds into eternity.", 
         damage=0, mana_cost=12, status_effect="slow", condition="first turn only"),
    Move(name="Shriek of Ruin", description="A high-pitched screech that disrupts concentration.", 
         lore_description="The scream of lost souls disrupts all thought.", 
         damage=8, mana_cost=4, status_effect="silence", condition="interrupt spell"),
    Move(name="Bone Swarm", description="Summons a vortex of teeth and ribs to shred nearby foes.", 
         lore_description="The dead rise in a storm of gnashing bone.", 
         damage=16, mana_cost=8, status_effect="bleed", condition="close range"),
]
session.add_all(fourth_wave_moves)
session.commit()

# Associate moves with fourth wave enemies
tezcatlipoca = session.query(Enemy).filter_by(name="Tezcatlipoca's Shade").first()
itzpapalotl = session.query(Enemy).filter_by(name="Itzpapalotl").first()
camazotz = session.query(Enemy).filter_by(name="Camazotz Spawn").first()
sentinel = session.query(Enemy).filter_by(name="Obsidian Sentinel").first()
scribe = session.query(Enemy).filter_by(name="Xibalban Scribe").first()

# Get moves for fourth wave enemies
tezcatlipoca_moves = session.query(Move).filter(Move.name.in_([
    "Mirror Fracture",
    "Temporal Ripple",
    "Shriek of Ruin"
])).all()

itzpapalotl_moves = session.query(Move).filter(Move.name.in_([
    "Soul Shred",
    "Bone Swarm",
    "Luminous Veil"
])).all()

camazotz_moves = session.query(Move).filter(Move.name.in_([
    "Blind Dive",
    "Shriek of Ruin",
    "Blood Curse"
])).all()

sentinel_moves = session.query(Move).filter(Move.name.in_([
    "Stone Fist",
    "Quake Stomp",
    "Earthen Maw"
])).all()

scribe_moves = session.query(Move).filter(Move.name.in_([
    "Curse Glyph",
    "Temporal Ripple",
    "Bitter Whisper"
])).all()

# Associate moves with fourth wave enemies
if tezcatlipoca:
    tezcatlipoca.moves.extend(tezcatlipoca_moves)
if itzpapalotl:
    itzpapalotl.moves.extend(itzpapalotl_moves)
if camazotz:
    camazotz.moves.extend(camazotz_moves)
if sentinel:
    sentinel.moves.extend(sentinel_moves)
if scribe:
    scribe.moves.extend(scribe_moves)

session.commit()

# ======= FOURTH WAVE ITEMS =======
fourth_wave_items = [
    Item(name="Shard of the Mirror God", type="artifact", weight=1, effect_description="A sliver of Tezcatlipoca's mirror — reflects spells at random.",
         lore_description="It shimmers with illusions, showing you your worst self.",
         armor_class=1, str=-1, dex=0, speed=0, wisdom=3, intelligence=3, constitution=0,
         charisma=1, initiative=0, equippable=True, is_equipped=False),
    Item(name="Itzpapalotl's Talon", type="weapon", weight=3, effect_description="Razor-sharp claw with spiritual resonance.",
         lore_description="Hums with the agony of souls it has severed.",
         armor_class=0, str=2, dex=2, speed=1, wisdom=1, intelligence=0, constitution=0,
         charisma=1, initiative=1, equippable=True, is_equipped=False),
    Item(name="Camazotz Fang", type="necklace", weight=1, effect_description="Drips with eternal blood. Increases lifesteal.",
         lore_description="The blood never dries, and never stops dripping.",
         armor_class=0, str=2, dex=0, speed=0, wisdom=-1, intelligence=-1, constitution=1,
         charisma=0, initiative=1, equippable=True, is_equipped=False),
    Item(name="Sentinel Plate", type="armor", weight=6, effect_description="Worn by the Obsidian Guardians. Heavy but nearly impenetrable.",
         lore_description="Etched with ancient warnings, it weighs on your soul.",
         armor_class=3, str=1, dex=-2, speed=-2, wisdom=0, intelligence=0, constitution=3,
         charisma=0, initiative=-1, equippable=True, is_equipped=False),
    Item(name="Cursed Codex", type="book", weight=2, effect_description="Scribed in Xibalban ink. Spells cast from it may backfire.",
         lore_description="The pages writhe and squirm, eager to be read aloud.",
         armor_class=0, str=-2, dex=0, speed=0, wisdom=2, intelligence=3, constitution=-1,
         charisma=0, initiative=0, equippable=True, is_equipped=False),
]
session.add_all(fourth_wave_items)
session.commit()

print("Fourth wave of enemies, moves, and items seeded.")