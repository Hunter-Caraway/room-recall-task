"""Choose which Poly Haven models become decoys, practice objects and room filler.

Writes art/made_objects.csv (one row per made object, editable) from the Poly Haven
catalogue. Run once; edit the CSV by hand after that. Rules:

  - Models built into the basements in 3D (ROOM_MODELS) are never decoys, so a
    decoy has never been in any room. The same goes for FILLER, which is placed in
    the rooms as cutouts.
  - Excluded: weapons, ceiling and street lights, scenery, and anything over 1.7 m.
  - Practice objects come from the rest; the remainder are decoys.

Usage: python art/choose_models.py
"""
import csv
import json
import pathlib
import random
import urllib.request

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "made_objects.csv"
UA = {"User-Agent": "asset-fetcher"}

ROOM_MODELS = [
    "steel_frame_shelves_01", "steel_frame_shelves_02", "steel_frame_shelves_03", "worn_metal_rack",
    "WoodenTable_03", "wooden_table_02", "tool_cart", "painted_wooden_shelves", "drawer_cabinet",
    "wooden_crate_01", "wooden_crate_02", "plastic_crate_01", "plastic_crate_02", "plastic_crate_03",
    "cardboard_box_01", "Barrel_02", "old_tyre", "wooden_military_crate", "old_military_crate",
    "wooden_ladder", "ladder_sectioned_01", "mounted_fluorescent_lights", "hanging_industrial_lamp",
    "wooden_bookshelf_worn", "Shelf_01", "wooden_display_shelves_01", "painted_wooden_cabinet",
    "small_wooden_table_01", "industrial_storage_cart", "metal_office_desk", "plastic_monobloc_chair_01",
    "folding_wooden_stool", "metal_trash_can", "pull_chain_light_socket",
]
FILLER = [
    "can_rusted", "cleaner_tin_01", "lubricant_spray", "spray_paint_bottles", "spray_paint_bottles_02",
    "multi_cleaner_5_litre", "multi_cleaner_bottle", "all_purpose_cleaner", "bleach_bottle", "drain_cleaner",
    "leather_cleaner_can", "oil_tin", "small_oil_can_01", "plastic_bottle_gallon", "plastic_jerrycan",
    "metal_jerrycan", "metal_jerrycan_green", "propane_tank", "small_lpg_tank", "cement_bag", "compost_bag_02",
    "trashbag", "seeding_tray_01", "planter_pot_clay", "russian_food_cans_01", "long_life_food",
    "wooden_bucket_01", "plastic_container", "industrial_pastic_container", "binder_notebook", "dustpan",
    "plastic_broom", "wooden_broom", "garden_gloves_01", "medical_tape",
]
EXCLUDE = {
    # weapons
    "bolt_action_rifle_7_62", "service_pistol", "stick_grenade", "antique_katana_01", "antique_estoc",
    "ornate_medieval_dagger", "ornate_medieval_mace", "ornate_war_hammer", "machete", "wooden_handle_saber",
    "katana_stand_01", "kite_shield", "ammo_box",
    # fixed to a building, or not an object
    "Chandelier_01", "Chandelier_02", "Chandelier_03", "chinese_chandelier", "lantern_chandelier_01",
    "ceiling_fan", "modern_ceiling_lamp_01", "caged_hanging_light", "industrial_caged_sconce",
    "industrial_wall_sconce", "industrial_wall_lamp", "security_light", "fire_alarm", "street_lamp_01",
    "street_lamp_02", "korean_public_payphone_01", "exterior_aircon_unit", "lateral_sea_marker", "ocean_buoy",
    "modular_airduct_rectangular_01", "modular_electric_cables", "overhead_crane", "covered_car",
    "scandinavian_masonry_heater", "wooden_barrels_01", "decorative_book_set_01", "office_notepads",
    "postcard_set_01", "throw_pillows_01", "tea_set_01", "brass_candleholders",
    # several separate items in one model: the dataset photos each show one object
    "brass_goblets", "cigarette_case", "football", "hamburger_buns", "screwdrivers_02", "stationery_supplies",
    "vintage_suitcase", "wine_bottles_01", "vintage_crutches_01",
}
SCENERY = {"nature", "rocks", "trees", "ground cover", "buildings", "structures", "grass", "ships", "moon",
           "plants", "flowers", "rigged"}
MAX_SIZE_M = 1.7
PRACTICE = 24


def main():
    request = urllib.request.Request("https://api.polyhaven.com/assets?t=models", headers=UA)
    catalogue = json.load(urllib.request.urlopen(request, timeout=60))
    taken = set(ROOM_MODELS) | set(FILLER) | EXCLUDE
    rest = []
    for name, info in sorted(catalogue.items()):
        cats = set(info["categories"])
        size = max(info.get("dimensions") or [0]) / 1000
        if name in taken or (cats & SCENERY and "potted plants" not in cats) or size > MAX_SIZE_M:
            continue
        rest.append(name)
    # Real sizes, so place() can catch models whose files use the wrong unit.
    dims = {k: [round(x / 1000, 4) for x in v["dimensions"]] for k, v in catalogue.items() if v.get("dimensions")}
    (ROOT / "model_dims.json").write_text(json.dumps(dims, indent=0, sort_keys=True))
    rng = random.Random("practice-pool")
    practice = set(rng.sample(rest, PRACTICE))

    def row(name, pool):
        info = catalogue[name]
        category = (info.get("category") or "").split("/")[-1] or info["categories"][0]
        return {"name": name, "model": name, "pick": "", "label": info["name"].lower(),
                "category": category.lower(), "pool": pool, "surfaces": "", "rotate_deg": 0}

    rows = ([row(n, "filler") for n in FILLER] + [row(n, "practice") for n in sorted(practice)] +
            [row(n, "decoy") for n in rest if n not in practice])
    with open(OUT, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = {p: sum(1 for r in rows if r["pool"] == p) for p in ("filler", "practice", "decoy")}
    print(f"wrote {OUT.name}: {counts}")


if __name__ == "__main__":
    main()
