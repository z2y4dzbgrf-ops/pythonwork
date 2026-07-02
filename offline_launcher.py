# offline_launcher.py —— 离线版游戏启动入口
"""
高中生涯 - 无悔青春 · 离线版
直接运行此文件即可在浏览器中打开游戏。
需要 Flask: pip install flask
"""
import sys, os, webbrowser, threading, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

def main():
    print("=" * 50)
    print("  高中生涯 - 无悔青春  离线版")
    print("  v2026.1.4")
    print("=" * 50)
    print()
    
    port = 5000
    url = f"http://127.0.0.1:{port}"
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"  游戏已启动！")
    print(f"  浏览器访问: {url}")
    print(f"  按 Ctrl+C 退出")
    print()
    
    app.run(host='127.0.0.1', port=port, debug=False)

if __name__ == '__main__':
    main()
