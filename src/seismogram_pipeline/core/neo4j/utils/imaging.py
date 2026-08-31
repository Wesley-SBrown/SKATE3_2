# src/seismogram_pipeline/core/neo4j/utils/imaging.py

import io
from pathlib import Path

from PIL import Image
from PIL.TiffTags import TAGS
from PIL.ExifTags import TAGS as EXIF_TAGS


def inspect_tiff_metadata(file_path: Path):
    Image.MAX_IMAGE_PIXELS = None
    print(f"Inspecting: {file_path.name}\n")
    with Image.open(file_path) as img:
        # basic properties
        print(f"Format: {img.format}")
        print(f"Size (Dimensions): {img.size}")
        print(f"Mode (Color type): {img.mode}")
        print(f"File Size (Bytes): {file_path.stat().st_size}\n")
        
        # Check for embedded ICC profile description (color space like AdobeRGB)
        print("Color Profile / Space Info:")
        icc_profile = img.info.get('icc_profile')
        if icc_profile:
            try:
                from PIL import ImageCms
                io_stream = io.BytesIO(icc_profile)
                profile = ImageCms.ImageCmsProfile(io_stream)
                profile_desc = ImageCms.get_profile_name(profile) if hasattr(ImageCms, 'get_profile_name') else profile.profile.title
                print(f"  ICC Profile Name: {profile_desc.strip()}")
            except Exception as e:
                print(f"  ICC profile present, but failed to parse details: {e}")
        else:
            print("  No ICC profile found in img.info (might be untagged or standard sRGB default).")
        print()

        # Check for EXIF metadata (scanner settings, software, descreening, rendering intents if embedded)
        print("EXIF Metadata:")
        try:
            exif_data = img.getexif()
            if exif_data:
                found_exif = False
                for tag_id, value in exif_data.items():
                    tag_name = EXIF_TAGS.get(tag_id, tag_id)
                    print(f"  {tag_name} (ID: {tag_id}): {value}")
                    found_exif = True
                if not found_exif:
                    print("  EXIF container empty.")
            else:
                print("  No EXIF data found.")
        except Exception as e:
            print(f"  Could not retrieve EXIF data: {e}")
        print()

        print("Internal TIFF Tags:")
        # raw TIFF tags translated to human-readable names
        if hasattr(img, 'tag') and img.tag:
            for tag_id, value in img.tag.items():
                tag_name = TAGS.get(tag_id, tag_id)
                print(f"  {tag_name} (ID: {tag_id}): {value}")
        else:
            print("  No specialized TIFF tags found.")