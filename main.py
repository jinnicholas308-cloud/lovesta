"""
Lovesta - 커플 추억 공유 앱
Entry point: python main.py
"""
from flask import render_template, make_response, request
from app import create_app

app = create_app()


@app.route('/health')
def health():
    """Railway 헬스체크 엔드포인트"""
    return 'OK', 200


@app.route('/sitemap')
def sitemap_visual():
    """사이트 구조 시각화 페이지"""
    return render_template('sitemap.html')


@app.route('/sitemap.xml')
def sitemap_xml():
    """SEO용 사이트맵 XML"""
    from datetime import datetime
    today = datetime.utcnow().strftime('%Y-%m-%d')
    base  = request.url_root.rstrip('/')

    # 비로그인 공개 페이지만 수록
    pages = [
        ('/', '1.0', 'daily'),
        ('/auth/login', '0.9', 'monthly'),
        ('/auth/register', '0.8', 'monthly'),
        ('/sitemap', '0.3', 'monthly'),
    ]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority, freq in pages:
        lines.append(
            f'  <url><loc>{base}{path}</loc>'
            f'<lastmod>{today}</lastmod>'
            f'<changefreq>{freq}</changefreq>'
            f'<priority>{priority}</priority></url>'
        )
    lines.append('</urlset>')

    resp = make_response('\n'.join(lines))
    resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return resp


if __name__ == '__main__':
    app.run(debug=True, port=5000)
