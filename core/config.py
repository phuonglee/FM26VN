import os
import sys
from pathlib import Path

# Thư mục gốc của project (cha của thư mục core/)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Đảm bảo có thể import các module từ thư mục con thông qua root (nếu cần)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Đường dẫn DB mặc định
DATA_DIR = PROJECT_ROOT / "data" / "database.sqlite"
ROOT_DB = PROJECT_ROOT / "database.sqlite"

# Fallback: Nếu không tìm thấy file trong data/ nhưng lại thấy ở root thì dùng root
if not DATA_DIR.exists() and ROOT_DB.exists():
    DEFAULT_DB_PATH = ROOT_DB
else:
    DEFAULT_DB_PATH = DATA_DIR

# Có thể nạp từ biến môi trường
DB_PATH = os.environ.get("DATABASE_PATH", str(DEFAULT_DB_PATH))
