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
    
    args = parser.parse_args()
    
    runner_script = f"run_{args.model}.py"
    runner_path = PROJECT_ROOT / "runners" / runner_script
    
    if not runner_path.exists():
        print(f"Lỗi: Không tìm thấy file {runner_path}.")
        sys.exit(1)
        
    print(f"[*] Bắt đầu chạy agent với tùy chọn model: {args.model}")
    try:
        subprocess.run([sys.executable, str(runner_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Tác vụ agents thất bại với mã lỗi: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n[*] Tác vụ đã bị hủy bởi người dùng.")
        sys.exit(0)

if __name__ == "__main__":
    main()
