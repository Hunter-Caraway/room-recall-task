"""Download the CC0 models listed in assets_manifest.py from Poly Haven (glTF, 1k)."""
import concurrent.futures as cf
import json
import pathlib
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from assets_manifest import ALL_MODELS, HDRIS, TEXTURES

OUT = pathlib.Path(__file__).parent / "_downloads"
UA = {"User-Agent": "victoria-project-asset-fetcher"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def fetch_model(name):
    target = OUT / "models" / name
    marker = target / ".complete"
    if marker.exists():
        return name, "cached"
    info = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
    if "gltf" not in info:
        raise ValueError(f"{name} has no glTF download")
    entry = info["gltf"]["1k"]["gltf"]
    target.mkdir(parents=True, exist_ok=True)
    (target / f"{name}.gltf").write_bytes(get(entry["url"]))
    for rel, inc in entry["include"].items():
        path = (target / rel).resolve()
        if target.resolve() not in path.parents:
            raise ValueError(f"unsafe path in {name}: {rel}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(get(inc["url"]))
    marker.touch()
    return name, "ok"


def fetch_texture(name):
    target = OUT / "textures" / name
    marker = target / ".complete"
    if marker.exists():
        return name, "cached"
    info = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
    target.mkdir(parents=True, exist_ok=True)
    # Some fabric textures name their color map col_1 instead of Diffuse.
    color = "Diffuse" if "Diffuse" in info else "col_1"
    for key, saved in ((color, "Diffuse"), ("nor_gl", "nor_gl"), ("Rough", "Rough")):
        (target / f"{saved}.jpg").write_bytes(get(info[key]["2k"]["jpg"]["url"]))
    marker.touch()
    return name, "ok"


def fetch_hdri(name):
    target = OUT / "hdri" / f"{name}.hdr"
    if target.exists():
        return name, "cached"
    info = json.loads(get(f"https://api.polyhaven.com/files/{name}"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(get(info["hdri"]["2k"]["hdr"]["url"]))
    return name, "ok"


def main(textures):
    fails = []
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(fetch_model, n): n for n in ALL_MODELS}
        futs |= {ex.submit(fetch_texture, n): n for n in textures}
        futs |= {ex.submit(fetch_hdri, n): n for n in HDRIS}
        for f in cf.as_completed(futs):
            try:
                f.result()
            except Exception as e:  # report every failure, then exit non-zero
                fails.append((futs[f], repr(e)))
    print("assets:", len(ALL_MODELS) + len(textures), "failed:", fails)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main(sorted(set(TEXTURES + sys.argv[1:])))
