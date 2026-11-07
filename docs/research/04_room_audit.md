# Room audit (kitchen, living room)

Tags: [R] seen in render; [C] from code. Line numbers are `art/build_rooms.py`. "Derived" means calculated from room.json and the camera in code. All 30 sprites were viewed on native-scale contact sheets, 14 zoomed 2x. Unplaced assets were checked by name and size only.

## A. What is wrong

**Both rooms**
- Same 4.6 m shell and near-identical camera: 1.85 m high, 22 mm (79° horizontal), 18-19° downward [C 26, 259, 356]. Verticals splay; it reads as a dollhouse [R].
- Same garden view with poles and a pavilion; no glass, curtains or reveal [R; C 190-204].
- No visible ceiling or fixture; hidden area lights give flat light; no sun patch despite daylight [R; C 222-229].
- No sockets, switches, radiators or cables [R].
- `stationery_supplies`: pens hover in stacked rows [R; C 348, 391].

**Kitchen**
- Sink and tap missing; also no dish rack, microwave or plates in use [R].
- `painted_wooden_cabinet` (291): oversized distressed dresser jammed against the counter end, drawer ajar, traps bananas and potato [R].
- `wooden_display_shelves_01` (292): unrelated beech unit; ends 13 cm short of the fridge front, obstructing the door [R; C].
- Fridge (283-286): blank box, slight emission, oversized handles [R; C].
- `metal_trash_can` (293): outdoor dustbin dominating the foreground, lid leaning, both cropped [R].
- `dining_table` (288): non-uniform scale; cloth bunched left, bare rust-coloured top exposed right [R; C].
- `wooden_bowl_01` (297): reads as a broken clay shard [R].
- `tea_set_01` (299): 1.3x teapot dwarfs the apple [R; C].
- `pot_enamel_01` (300): red pattern reads as burning coals on an unlit hob [R].
- `alarm_clock_01` (305): black, unreadable face [R].
- `ceramic_vase_01` (308): very large white vase, about 0.42 m (derived), on a dresser [R].
- `watering_can_metal_01` (310): on the floor behind a chair, no reason [R].
- Bleach and drain cleaner (337, 323) beside food; ceremonial goblets (344) on the counter [R].
- Brass pot (349) on the floor under the dresser; dustpan (336) half hidden [R].
- Shelves (277-280): no brackets [R; C].
- Splashback (270-271): stops either side of the window, bare wall under the sill, top misaligned with sill [R; C].
- Floor (257): checker tiles about chair-seat width. Counter (264) reads as seamed beige tile [R].
- Wasted: broom, `wicker_basket_02`, left-wall frame project off-frame (derived; 335, 350, 339). Kiwi (341) not visible; clipboard (342) a sliver [R].

**Living room**
- No TV; sofa faces empty foreground. `television_02` unused [R].
- Four timepieces: grandfather, wall, mantel, pocket watch (369, 403, 376, 411) [R].
- `vintage_grandfather_clock_01` (369): wedged between bookshelf and sofa; black dial [R].
- `ClassicConsole_01` (365): huge black carved table, cropped, clashes with the room [R].
- `mantel_clock_01` (376): plinth corner appears to overhang the console's curved edge [R].
- `desk_lamp_arm_01` (377): clamp lamp balanced on its tip, no base, no cord [R].
- `coffee_table_round_01` (367): about 1.07 m wide [C]; flea-market pile of nine things [R].
- Camera and binocular straps (378, 375): lie flat past the table edge, hovering [R].
- `horse_statue_01` (379) on a soft ottoman; garden `concrete_cat_statue` (380) on the rug [R].
- `vintage_suitcase` (383): in the walkway, no reason [R].
- `rubber_duck_toy` (385): bath toy centred on a shelf, larger than the goblets [R].
- `vintage_oil_lamp` (407): chimney pokes through the top board [R].
- `ceramic_vase_03` / goblets (395, 399): intersecting, 3 cm apart in x [R; C].
- `fancy_picture_frame_02` (398): empty gilt frame [R].
- Rug (359-360): zero-thickness tiled gingham, reads as a picnic cloth, stops short of sofa [R; C].
- `ArmChair_01` (366) hides the bookshelf base and faces nothing. Calathea (371) and basket (394) are cropped scraps [R].

**Transition:** frames 1, 36, 72 show `Sofa_01` from behind in a bare room matching neither study room; frame 72 ends on blank wall and a sliced sofa top [R; C 445].

## B. Cue leakage

Sprites are drawn at render size [C app.py 314, 325]. The tray only shrinks those over 104 px wide or 140 px tall [C app.py 85]. Nothing normalises orientation or scale.

Format: id, px, view elevation below horizon, keystone lean, my leak rating (angles derived).

**Kitchen:** brass_pan_01 107x16 4° -5° HIGH; carved_wooden_plate 88x22 12° +10° HIGH; ceramic_vase_01 84x142 10° +12° HIGH; wooden_cutting_board 174x59 21° +2° HIGH; alarm_clock_01 42x47 3° +9° MED; jug_01 65x53 3° -4° MED; tea_set_01 114x103 24° +5° MED; watering_can_metal_01 92x63 26° -8° MED; wooden_bowl_01 136x79 25° -3° MED; bananas 58x57 10° +9° LOW; multi_cleaner_bottle 29x62 10° -6° LOW; plastic_thermos 34x79 10° +7° LOW; pot_enamel_01 62x44 13° -1° LOW; vintage_electric_kettle 74x78 11° +2° LOW; wicker_basket_01 103x42 12° -4° LOW.

**Living room:** binoculars 110x52 26° +0° HIGH; boombox 99x82 11° +10° HIGH; Camera_01 91x80 27° +5° HIGH; horse_statue_01 51x62 31° -7° HIGH; mantel_clock_01 126x77 15° +14° HIGH; potted_plant_04 80x98 11° +12° HIGH; vintage_suitcase 193x155 31° +11° HIGH; antique_ceramic_vase_01 46x81 6° -5° MED; brass_candleholders 54x82 5° -9° MED; carved_wooden_elephant 55x43 1° -7° MED; concrete_cat_statue 79x120 26° -6° MED; desk_lamp_arm_01 97x159 12° +8° MED; magnifying_glass_01 96x41 24° +3° MED; Ukulele_01 126x27 19° +3° MED; rubber_duck_toy 34x44 10° -7° LOW.

Mechanisms:
1. Elevation encodes surface: shelves 1-6°, counter/console 10-15°, table 21-27°, floor/ottoman 26-31° (derived).
2. Lean encodes x position: up to 14° toward the frame edge (derived). Plant and mantel clock visibly lean right [R].
3. Pixel scale encodes depth: 233-442 px/m kitchen, 232-406 px/m living room (derived).
4. Yaw encodes wall: boombox and mantel clock face left, fitting only the right-wall console [R; C 374, 376].

Worst: `vintage_suitcase` (largest, top-down, floor only), `mantel_clock_01` (diagonal plinth), `boombox`, `potted_plant_04`, `Camera_01` and `binoculars` (flat straps imply a tabletop), `brass_pan_01` (edge-on, shelf only), `ceramic_vase_01`.

**Cut-off edges:** none meaningful. Cropping loses at most 39 faint pixels per sprite (measured); no sprite is cut by an occluder [C 533-538]. `wooden_cutting_board` has black wedges on its lower edge at the cloth ripples [R], weakly identifying the table.

**Baked lighting:** sprites keep room lighting [C 526-538], but I could not confirm a surface-specific cast shadow on any sprite. It is weak next to geometry. Sprites have no contact shadow, so all look equally unattached when placed [C].

**Empty room: no marks, strong leak from gaps.**
- No ghost marks. Pixels differing by over 8 levels: kitchen 89,416, living room 121,630. Those outside sprites are halos by the objects, meaning shadows in `full.jpg` correctly absent from `empty.jpg` [R, measured]. A kitchen floor patch (x 760-900, y 840-900) differs by about 4 levels; cause unknown, not visible by eye.
- Cleared surfaces [R]. Kitchen: left lower shelf, dresser top, stove. Living room: second bookshelf shelf, whole console top, ottoman, right sofa cushion.
- Clutter gaps [R]: counter between cans and avocado, under the window, between goblets and potato; side table between frame and candlestick.
- Targets are the big focal objects and clutter is small, so size partly marks targets [R].

**Spacing:** closest pairs 85 px (bananas/plate) and 86 px (boombox/plant) against the 80 px limit; they pass narrowly [C postprocess.py 52; measured].

## C. Available assets

Unused in these rooms, not inspected visually (sizes from `probe.json` or glTF bounds):
- Kitchen: `vintage_microwave` (1.07 m, scale down), `wooden_spoon`, `plastic_container`, `drawer_cabinet` (1.14x0.49x1.88), `painted_wooden_shelves` (0.51x0.37x1.13), `steel_frame_shelves_01` (probe says 10.97x5.02x21.41, scale carefully), `strawberry_chocolate_cake`.
- Living room: `television_02` (about 0.4x0.41x0.35), `gaming_console`, `gamepad`, `cassette_player`, `brass_vase_01`, `potted_plant_01`, `fancy_picture_frame_01`, `hanging_picture_frame_01`, `hanging_picture_frame_02`, `standing_picture_frame_01`, `binder_notebook`, `postcard_set_01`, `bronze_whale_statue`, `dartboard`.
- Textures: `painted_plaster_wall`, `white_plaster_02`.

Missing (name search): sink, tap, curtains, rug, ceiling light, floor lamp, sockets. Sink, tap, rod and sockets can be built with `box()`. Blender 5.2.3 is at `~/.local/opt/blender-5.2.3-linux-x64`.

## D. Proposed layouts

Not rendered. Coordinates were projected with the proposed camera; re-measure after rendering. Minimum projected spacing: kitchen 107 px, living room 89 px.

Camera: (0, -2.5, 1.55) aimed at (0, 1, 0.8), 24 mm, about 12° pitch. This reduces lean and elevation spread but does not remove them; sprite perspective needs its own decision.

Rule: every surface with a target keeps non-target clutter, so none goes bare.

**Kitchen.** Anchors: counter with stove, new sink under the window; counter ends at x 1.6; dresser in back-right corner (1.96, 1.25); fridge back-left; shelving on left wall, y about 0.3; table and two chairs; small bin by dresser. Groups: wash (sink, cleaners), cook (stove, hood), prep (left counter), breakfast (table). Move goblets, floor pot and bleach.

Targets (x, y):
- Table: jug (-0.3, -0.15); carved plate (0.35, -0.05).
- Counter: bananas (-1.25, 1.5); teapot at scale 1.0 (-0.8, 1.55); watering can (0.2, 1.55); wooden bowl (0.8, 1.5); kettle (1.35, 1.55).
- Stove: brass pan (-0.22, 1.45).
- Shelves: enamel pot (-1.1, 1.75); smaller ceramic vase (1.7, 1.75); wicker basket (2.1, 1.75).
- Sill: alarm clock (1.1, 1.9).
- Dresser: cutting board (1.95, 1.25).
- Shelving cube: thermos (-2.1, 0.5).
- Floor by bin: spray bottle (1.45, 0.45).

**Living room.** Anchors: sofa on right wall (1.95, 0.35) facing left; console on left wall (-2.0, 0.7) with TV; bookshelf back-left; armchair under window (0.3, 1.35); ottoman (0.55, 0.45); coffee table at scale 0.6 (0, -0.1) centred on the rug; side table back-right (1.75, 1.55). Remove grandfather clock; fill the empty frame. Groups: TV seating, reading (bookshelf, armchair), window corner.

Targets (x, y):
- Bookshelf (y 1.6): boombox z 1.05 (x -1.75); mantel clock z 1.4 (x -1.2); elephant z 0.72 (x -1.2); smaller suitcase on bottom shelf (x -1.5).
- Console: horse (-1.95, 0.5); antique vase (-2.0, 1.3).
- Coffee table: candleholder (-0.35, -0.2); magnifying glass (0.3, -0.15).
- Ottoman: camera (0.55, 0.45).
- Armchair: ukulele (0.3, 1.35).
- Floor: `brass_vase_01`, replacing the base-less lamp (-0.55, 1.55); cat statue by window (1.2, 1.6).
- Sill: rubber duck (1.05, 1.9).
- Side table: small plant (1.75, 1.55).
- Sofa: binoculars (1.9, 0.2).
