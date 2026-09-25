from pathlib import Path
import base64

root = Path(__file__).resolve().parent
parts = sorted(root.glob("HD2_Better_Tanks_v1.0.0_Source.tar.xz.b64.part*"))
if not parts:
    raise SystemExit("No source archive parts found")

data = "".join(p.read_text(encoding="ascii").strip() for p in parts)
out = root / "HD2_Better_Tanks_v1.0.0_Source.tar.xz"
out.write_bytes(base64.b64decode(data))
print(out)
