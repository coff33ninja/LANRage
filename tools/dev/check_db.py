import asyncio
import sys
from pathlib import Path

# Ensure repo root is importable when this script is executed directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.control_plane.settings import get_settings_db


async def check_db():
    db = await get_settings_db()

    # Get all settings
    print("=== ALL SETTINGS ===")
    settings = await db.get_all_settings()
    for key, value in settings.items():
        print(f"{key}: {value}")

    print("\n=== ALL CONFIGS ===")
    configs = await db.get_all_server_configs()
    if not configs:
        print("No configurations saved")
    else:
        for config in configs:
            print(f'ID: {config["id"]}, Name: {config["name"]}, Mode: {config["mode"]}')
            print(f'  Config: {config["config"]}')
            print(f'  Enabled: {config["enabled"]}')


asyncio.run(check_db())
