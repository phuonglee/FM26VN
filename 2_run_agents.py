import argparse
import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).parent.absolute()

def main():
    parser = argparse.ArgumentParser(description="Run FM26 Translation Agents")
    parser.add_argument(
        "--model", 
        type=str, 
        default="default",
        choices=["default", "deepseek", "free_tier", "gpt_mini", "local", "moonshot"],
        help="Chọn mô hình agent runner để chạy."
    )
    parser.add_argument(
        "--use-sot",
        action="store_true",
        help="Sử dụng SOT Engine để bổ sung tri thức và hướng dẫn vào Prompt."
    )
    
    args = parser.parse_args()
    
    # Chuyển đổi tên script sang module path (VD: run_deepseek.py -> runners.run_deepseek)
    module_name = f"runners.{args.model if args.model != 'default' else 'run_default'}"
    if args.model != 'default':
        module_name = f"runners.run_{args.model}"
    else:
        module_name = "runners.run_default"

    if args.use_sot:
        import os
        os.environ["USE_SOT"] = "1"
        print("[*] Đang kích hoạt SOT Engine để chuẩn bị tri thức...")

    print(f"[*] Bắt đầu chạy agent với tùy chọn model: {args.model}")
    try:
        # Chạy dưới dạng module để Python tự xử lý sys.path từ thư mục gốc
        subprocess.run([sys.executable, "-m", module_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Tác vụ agents thất bại với mã lỗi: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n[*] Tác vụ đã bị hủy bởi người dùng.")
        sys.exit(0)

if __name__ == "__main__":
    main()
