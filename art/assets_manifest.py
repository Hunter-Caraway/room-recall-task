"""Poly Haven (CC0) assets used to build the rooms. Fetched by fetch_assets.py."""

FURNITURE = [
    "dining_table", "dining_chair_02", "electric_stove", "vintage_microwave",
    "drawer_cabinet", "painted_wooden_cabinet", "metal_trash_can", "wooden_display_shelves_01",
    "Sofa_01", "ArmChair_01", "coffee_table_round_01", "ClassicConsole_01",
    "wooden_bookshelf_worn", "side_table_01", "ornate_mirror_01", "Ottoman_01",
    "potted_plant_01", "throw_pillows_01", "vintage_grandfather_clock_01",
    "steel_frame_shelves_01", "painted_wooden_shelves",
]

KITCHEN_SCORED = [
    "jug_01", "pot_enamel_01", "brass_pan_01", "wooden_cutting_board",
    "vintage_electric_kettle", "wooden_bowl_01", "bananas", "tea_set_01",
    "wicker_basket_01", "plastic_thermos", "ceramic_vase_01", "alarm_clock_01",
    "multi_cleaner_bottle", "watering_can_metal_01", "carved_wooden_plate",
]
KITCHEN_CLUTTER = [
    "hamburger_buns", "croissant", "food_apple_01", "food_pears_asian_01", "yellow_onion",
    "lemon", "russian_food_cans_01", "long_life_food", "wooden_spoon", "all_purpose_cleaner",
    "plastic_container", "wooden_bucket_01", "plastic_broom", "dustpan", "brass_pot_01",
    "wine_bottles_01", "bleach_bottle", "carrot_cake",
]

LIVING_SCORED = [
    "horse_statue_01",
    "boombox", "binoculars", "mantel_clock_01", "desk_lamp_arm_01", "Camera_01",
    "concrete_cat_statue", "antique_ceramic_vase_01", "brass_candleholders",
    "vintage_suitcase", "magnifying_glass_01", "rubber_duck_toy", "carved_wooden_elephant",
    "potted_plant_04", "Ukulele_01",
]
LIVING_CLUTTER = [
    "book_encyclopedia_set_01", "postcard_set_01",
    "stationery_supplies", "office_notepads", "binder_notebook", "cassette_player",
    "wicker_basket_02", "ceramic_vase_03", "brass_vase_01",
    "standing_picture_frame_02", "fancy_picture_frame_01",
    "hanging_picture_frame_01", "hanging_picture_frame_02", "wall_clock", "tea_set_01",
]

EXTRA_CLUTTER = [
    "food_avocado_01", "food_kiwi_01", "food_lime_01", "sweet_potato", "wooden_bowl_02",
    "metal_jug", "plastic_bottle_gallon", "drain_cleaner",
    "ceramic_pot", "planter_pot_clay", "potted_plant_02", "clipboard", "brass_goblets",
    "chess_set", "round_spectacles", "vintage_oil_lamp", "lambis_shell", "wooden_candlestick",
    "hanging_picture_frame_03", "calathea_orbifolia_01", 
    "television_02", "pocket_watch", "fancy_picture_frame_02",
]

# Added for the rebuilt rooms (round 2) and the hallway practice room.
ROUND2 = [
    "CheeseBox_01", "Television_01", "modern_wooden_cabinet", "vintage_cabinet_01",
    "painted_wooden_bench", "fishermans_hat", "rubber_boots", "garden_gloves_01",
    "vintage_flashlight", "filmstrip_projector_8mm", "side_table_tall_01",
    "food_pomegranate_01", "food_ginger_01", "sofa_02", "modern_coffee_table_01",
    "CoffeeTable_01", "round_wooden_table_01", "small_wooden_table_01",
    "painted_wooden_cabinet_02", "vintage_wooden_drawer_01", "ClassicNightstand_01",
    "wooden_crate_01", "modern_ceiling_lamp_01", "brass_pot_02", "cardboard_box_01",
    "painted_wooden_nightstand", "seadogs_compass",
    "vintage_telephone_wall_clock", "Shelf_01", "vintage_pocket_watch",
    "WoodenTable_01", "WoodenTable_02", "wooden_table_02", "painted_wooden_table", "gallinera_table",
    "round_wooden_table_02", "painted_wooden_chair_01", "gallinera_chair", "wooden_stool_01",
    "food_lychee_01", "wooden_broom", "trashbag", "planter_box_01", "brass_diya_lantern",
]

# Round 3: bedroom and garage, a more crowded living room, three arrangements each.
ROUND3 = [
    # bedroom
    "GothicBed_01", "old_bed_frame", "vintage_day_bed", "GothicCommode_01", "chinese_commode",
    "GreenChair_01", "SchoolDesk_01", "painted_wooden_chair_02",
    "ceramic_vase_02", "ceramic_vase_04", "Lantern_01", "vintage_video_camera", "brass_vase_02",
    "portable_cassette_player", "digital_wrist_watch", "standing_picture_frame_01",
    "painted_wooden_stool", "folding_wooden_stool", "wooden_lantern_01",
    # living room
    "ArmChair_01", "sofa_03", "modern_coffee_table_02", "mid_century_lounge_chair", "brass_vase_03",
    "sungka_board", "gaming_console", "television_02", "vintage_oil_lamp", "anthurium_botany_01",
    "pachira_aquatica_01", "chinese_tea_table", "brass_vase_04",
    # garage
    "american_football", "garden_gnome", "tire_pump", "metal_toolbox", "Megaphone_01",
    "steel_frame_shelves_01", "steel_frame_shelves_02", "steel_frame_shelves_03", "worn_metal_rack",
    "metal_tool_chest", "WoodenTable_03", "tool_cart", "bench_vice_01", "ladder_sectioned_01",
    "Barrel_02", "plastic_crate_01", "plastic_crate_02", "plastic_crate_03", "compost_bags",
    "compost_bag_02", "garden_hose_wall_mounted_01", "old_tyre", "metal_jerrycan", "plastic_jerrycan",
    "spray_paint_bottles", "cleaner_tin_01", "cement_bag", "rusted_spade_01", "power_box_01",
    "mounted_fluorescent_lights", "hanging_industrial_lamp", "rollershutter_door",
    "multi_cleaner_5_litre", "can_rusted", "leather_cleaner_can", "lubricant_spray",
    "measuring_tape_01", "Drill_01", "wooden_hammer_01", "handsaw_wood", "seeding_tray_01",
    "planter_box_02", "garden_sprinkler_01", "trowel_01", "small_oil_can_01",
    "plastic_monobloc_chair_01", "wooden_crate_02", "old_military_crate", "dartboard", "oil_tin",
    "wooden_stool_02",
]

ALL_MODELS = sorted(set(
    FURNITURE + KITCHEN_SCORED + KITCHEN_CLUTTER + LIVING_SCORED + LIVING_CLUTTER + EXTRA_CLUTTER + ROUND2
    + ROUND3
))

TEXTURES = [
    "floor_tiles_06", "herringbone_parquet", "kitchen_wood", "laminate_floor_02",
    "long_white_tiles", "marble_01", "oak_veneer_01", "painted_plaster_wall", "white_plaster_02",
    "fabric_pattern_07", "poly_wool_herringbone", "caban", "plank_flooring_02",
    "patterned_terracotta_tiling",
    # round 3
    "garage_floor", "painted_concrete", "concrete_block_wall", "wood_floor", "wool_boucle",
    "quatrefoil_jacquard_fabric",
]
HDRIS = ["symmetrical_garden_02", "cloudy_vondelpark"]
