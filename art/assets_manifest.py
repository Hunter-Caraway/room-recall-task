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

ALL_MODELS = sorted(set(
    FURNITURE + KITCHEN_SCORED + KITCHEN_CLUTTER + LIVING_SCORED + LIVING_CLUTTER + EXTRA_CLUTTER
))
