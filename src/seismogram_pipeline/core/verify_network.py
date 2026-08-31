# src/seismogram_pipeline/core/verify_network.py

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Union, Optional
import sys

load_dotenv()
SMB_SERVER = os.getenv("SMB_SERVER")
SMB_SHARE = os.getenv("SMB_SHARE")

def get_mount_path() -> Path:
    """
    Returns constructed network mount Path based on user platform
    """

    if not SMB_SERVER or not SMB_SHARE:
        raise ValueError("[ERROR] SMB_SEVER or SMB_SHARE is missing from .env")

    if sys.platform.startswith("linux"):
        uid = os.getuid()

        # GVfs normalize file path to be lowercase
        return Path(f"/run/user/{uid}/gvfs/smb-share:server={SMB_SERVER},share={SMB_SHARE.lower()}")

    elif sys.platform == "darwin":
        # macOS network mounts typically appear in /Volumes
        return Path(f"/Volumes/{SMB_SHARE}")
    
    elif sys.platform == 'win32':
        # Windows UNC path
        return Path(f"\\\\{SMB_SERVER}\\{SMB_SHARE}")

    else:
        raise NotImplementedError(f"Unsupported operating system: {sys.platform}")

def verify_and_access_share(
    view_contents: bool = False
) -> Optional[Path]:
    try:
        share_path = get_mount_path()
        data_folder = os.getenv("SMB_DATA")
        raw_data_path = share_path.joinpath(data_folder)

        # confirm data directory exists
        if raw_data_path.exists() and raw_data_path.is_dir():
            print(f"[SUCCESS] Network share found at: {share_path}")

            if view_contents:
                print("\nContents in data folder:")
                for item in raw_data_path.iterdir():
                    print(f" - {item.name}")
            return raw_data_path
        else:
            print("[NOTICE] Network share not found.")
            print("Please ensure you are connected to the VPN and the share is mounted.")
        return
            
    except PermissionError:
        print("[ERROR] Permission denied accessing the share. Please check your mount status.")
    except Exception as e:
        print(f"{e}")


if __name__ == "__main__":
    verify_and_access_share()


        
