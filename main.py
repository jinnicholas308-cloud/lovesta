"""
Lovesta - 커플 추억 공유 앱
Entry point: python main.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
