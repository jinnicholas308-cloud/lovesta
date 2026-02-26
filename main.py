"""
Lovesta - 커플 추억 공유 앱
Entry point: python main.py
"""
from app import create_app

app = create_app()


@app.route('/health')
def health():
    """Railway 헬스체크 엔드포인트"""
    return 'OK', 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
