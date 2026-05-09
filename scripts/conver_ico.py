from pathlib import Path
from PIL import Image

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent

# Open the source image from the assets directory
img = Image.open(str(project_root / "assets" / "data-analytics.png"))

# Save as ICO file (it is recommended to include standard icon sizes)
img.save(str(project_root / "assets" / "data-analytics.ico"), format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])