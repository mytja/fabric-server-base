import os.path

import requests
import json


def download_file(url, filename):
    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        with open(filename, "wb") as file:
            for chunk in req.iter_content(chunk_size=8192):
                file.write(chunk)


# First download the latest Fabric version
r = requests.get("https://meta.fabricmc.net/v2/versions/")
res = r.json()
game_ver = res["game"][0]["version"]
loader = res["loader"][0]["version"]
installer = res["installer"][0]["version"]

print(f"Downloading Fabric server for {game_ver}, loader {loader}, installer {installer}")

download_file(f"https://meta.fabricmc.net/v2/versions/loader/{game_ver}/{loader}/{installer}/server/jar", "minecraft.jar")

print("Fabric server download was successful. Located in minecraft.jar.")

downloaded_mods = []

with open("mods.json", "r") as f:
    mods = json.loads(f.read())

for mod in mods:
    if mod["id"] in downloaded_mods:
        print(f"[WARNING] Skipping already downloaded mod {mod['id']}/{mod['filename']}.")
        continue

    if mod.get("version") is None:
        mod["version"] = ""

    if not os.path.exists(f"mods/{mod['filename']}"):
        mod["version"] = ""

    if mod["source"] == "modrinth":
        r = requests.get(f'https://api.modrinth.com/v2/project/{mod["id"]}/version?loaders=["fabric"]&game_versions=["{game_ver}"]')
        if r.status_code == 404:
            print(f"[ERROR] 404 returned from Modrinth API for mod {mod['id']}/{mod['filename']}.")
            continue

        res = r.json()

        if len(res) == 0:
            print(f"[ERROR] Mod ({mod['id']}/{mod['filename']}) doesn't exist for Fabric {game_ver}! Skipping.")
            continue

        if mod["version"] == res[0]['version_number']:
            print(f"[INFO] Mod ({mod['id']}/{mod['filename']}) is already updated to the latest version ({mod['version']}). Skipping update!")
            continue

        print(f"Downloading mod {res[0]['name']} for {res[0]['game_versions']}")

        download_file(res[0]["files"][0]["url"], f'mods/{mod["filename"]}')
        downloaded_mods.append(mod['id'])
        mod["version"] = res[0]['version_number']

        print(f"Download for {res[0]['name']} executed successfully!")
    else:
        print(f"[ERROR] Mod source {mod['source']} for mod {mod['id']}/{mod['filename']} not recognized!")

print("Updating mods.json!")
with open("mods.json", "w+") as f:
    f.write(json.dumps(mods, indent=4))

print("Done!")
