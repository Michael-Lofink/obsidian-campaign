```statblock
columns: 2
forcecolumns: true
layout: Basic Pathfinder 2e Layout
source: "Bestiary"
name: "Crocodile"
level: "Creature 2"

alignment: "N"
size: "Large"
trait_01: "animal"
modifier: 7

perception:
  - name: "Perception"
    desc: "+7; low-light vision"

skills:
  - name: "Skills"
    desc: "Athletics: +8, Stealth: +7 (+11 in water)"

abilityMods: [4, 1, 3, -5, 1, -4]
speed: "20 feet, swim 25 feet"
sourcebook: "_Bestiary_, page 67"

ac: 18
armorclass:
  - name: "AC"
    desc: "18; __Fort__ +9, __Ref__ +7, __Will__ +5"

hp: 30
health:
  - name: ""
  - name: "HP"
    desc: "30"

abilities_top:
  - name: ""

abilities_mid:
  - name: ""

attacks:
  - name: ""

  - name: "**Melee** `pf2:1` Jaws"
    desc: "+10 (reach 5 feet)\n__Damage__ 1d10 + 4 piercing plus Grab"

  - name: "**Melee** `pf2:1` Tail"
    desc: "+10 (agile)\n__Damage__ 1d6 + 4 bludgeoning"

  - name: "Aquatic Ambush"
    desc: "`pf2:2` 35 feet\n**Requirements** The crocodile is hiding in water and a creature that hasn't detected it is within 35 feet.\n\n**Effect** The crocodile moves up to its swim Speed + 10 feet toward the triggering creature, traveling through water and on land. Once the creature is within reach, the crocodile makes a Strike against it. The creature is off-guard against this Strike."

  - name: "Death Roll"
    desc: "`pf2:1` **Requirements** The crocodile has a creature grabbed.\n\n**Effect** The crocodile tucks its legs and rolls rapidly, twisting its victim. It makes a jaws Strike with a +2 circumstance bonus to the attack roll against the grabbed creature. If it hits, it also knocks the creature prone. If it fails, it releases the creature."

  - name: "Deep Breath"
    desc: "The crocodile can hold its breath for about 2 hours."
```