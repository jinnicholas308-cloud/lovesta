"""
Email sending utility with professional HTML templates.
Uses smtplib (no extra packages needed).
Gracefully degrades: logs warning if SMTP not configured.

Env vars:
  MAIL_SERVER, MAIL_PORT (587), MAIL_USERNAME, MAIL_PASSWORD,
  MAIL_FROM (defaults to MAIL_USERNAME), MAIL_USE_TLS (True)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def _get_smtp_config():
    server = os.getenv('MAIL_SERVER')
    if not server:
        return None
    return {
        'server':   server,
        'port':     int(os.getenv('MAIL_PORT', '587')),
        'username': os.getenv('MAIL_USERNAME', ''),
        'password': os.getenv('MAIL_PASSWORD', ''),
        'from':     os.getenv('MAIL_FROM') or os.getenv('MAIL_USERNAME', ''),
        'use_tls':  os.getenv('MAIL_USE_TLS', 'true').lower() in ('true', '1', 'yes'),
    }


def _send_raw(to_email, subject, html_body):
    """Raw SMTP 전송."""
    cfg = _get_smtp_config()
    if not cfg:
        try:
            current_app.logger.warning(f'[Email] SMTP 미설정 — 메일 전송 스킵: {subject}')
        except RuntimeError:
            print(f'[Email] SMTP 미설정 — 메일 전송 스킵: {subject}')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f'Lovesta <{cfg["from"]}>'
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        if cfg['use_tls']:
            server = smtplib.SMTP(cfg['server'], cfg['port'], timeout=10)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP(cfg['server'], cfg['port'], timeout=10)
            server.ehlo()

        if cfg['username']:
            server.login(cfg['username'], cfg['password'])
        server.sendmail(cfg['from'], to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        try:
            current_app.logger.error(f'[Email] 전송 실패: {e}')
        except RuntimeError:
            print(f'[Email] 전송 실패: {e}')
        return False


# ── 등급별 테마 색상 ──
RARITY_COLORS = {
    'common':    {'bg': '#f3f4f6', 'accent': '#9ca3af', 'text': '#374151'},
    'uncommon':  {'bg': '#f0fdf4', 'accent': '#22c55e', 'text': '#166534'},
    'rare':      {'bg': '#eff6ff', 'accent': '#3b82f6', 'text': '#1e40af'},
    'epic':      {'bg': '#faf5ff', 'accent': '#a855f7', 'text': '#6b21a8'},
    'legendary': {'bg': '#fffbeb', 'accent': '#f59e0b', 'text': '#92400e'},
    'mythic':    {'bg': '#fff1f2', 'accent': '#f43f5e', 'text': '#9f1239'},
}


def _html_template(title, body_html, accent_color='#f43f5e'):
    """통일된 HTML 이메일 래퍼."""
    return f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;font-family:'Apple SD Gothic Neo','Noto Sans KR',sans-serif;background:#fdf2f8;">
<div style="max-width:520px;margin:24px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(244,63,94,.12);">
  <div style="background:linear-gradient(135deg,{accent_color},#ec4899);padding:28px 24px;text-align:center;">
    <h1 style="color:#fff;font-size:20px;margin:0;">Lovesta</h1>
    <p style="color:rgba(255,255,255,.85);font-size:13px;margin:6px 0 0;">{title}</p>
  </div>
  <div style="padding:28px 24px;">
    {body_html}
  </div>
  <div style="padding:16px 24px;background:#fdf2f8;text-align:center;">
    <p style="color:#9ca3af;font-size:11px;margin:0;">Lovesta — 우리의 추억을 함께 기록해요</p>
  </div>
</div>
</body></html>'''


def send_inquiry_notification(inquiry, admin_email=None):
    """새 문의 접수 시 어드민에게 알림 메일."""
    if not admin_email:
        admin_email = os.getenv('ADMIN_EMAIL', '')
    if not admin_email:
        return False

    body = f'''
    <p style="font-size:14px;color:#374151;line-height:1.7;">
      새로운 문의가 접수되었습니다.
    </p>
    <div style="background:#f9fafb;border-radius:12px;padding:16px;margin:16px 0;border:1px solid #e5e7eb;">
      <p style="margin:0 0 8px;font-size:12px;color:#9ca3af;">카테고리: <strong style="color:#f43f5e;">{inquiry.category_label}</strong></p>
      <p style="margin:0 0 4px;font-size:15px;font-weight:700;color:#111827;">{inquiry.subject}</p>
      <p style="margin:8px 0 0;font-size:13px;color:#4b5563;line-height:1.6;white-space:pre-line;">{inquiry.body}</p>
    </div>
    <p style="font-size:12px;color:#9ca3af;">
      작성자: {inquiry.author.username} ({inquiry.author.email})<br/>
      {f'커플 코드: {inquiry.author.couple.invite_code}' if inquiry.author.couple else '커플 미연결'}
    </p>
    '''
    return _send_raw(admin_email, f'[Lovesta 문의] {inquiry.subject}',
                     _html_template('새 문의가 접수되었습니다', body))


def send_inquiry_reply(inquiry, admin_reply):
    """문의 답변 시 유저에게 알림 메일."""
    user_email = inquiry.author.email
    if not user_email:
        return False

    body = f'''
    <p style="font-size:14px;color:#374151;line-height:1.7;">
      <strong>{inquiry.author.username}</strong>님, 문의에 대한 답변이 도착했어요!
    </p>
    <div style="background:#f0fdf4;border-radius:12px;padding:16px;margin:16px 0;border:1px solid #bbf7d0;">
      <p style="margin:0 0 8px;font-size:12px;color:#16a34a;font-weight:600;">관리자 답변</p>
      <p style="margin:0;font-size:14px;color:#166534;line-height:1.7;white-space:pre-line;">{admin_reply}</p>
    </div>
    <div style="background:#f9fafb;border-radius:12px;padding:12px;border:1px solid #e5e7eb;">
      <p style="margin:0;font-size:12px;color:#6b7280;">원본 문의: {inquiry.subject}</p>
    </div>
    '''
    return _send_raw(user_email, f'[Lovesta] 문의 답변: {inquiry.subject}',
                     _html_template('문의 답변이 도착했어요', body))


def send_limit_increase_notification(couple, new_limit):
    """커플 인원 증설 완료 알림 메일 (모든 멤버에게 발송)."""
    pet_info = couple.pet_info
    rarity = pet_info.get('rarity', 'common')
    colors = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])

    pet_emoji = pet_info.get('emoji', '🐾')
    pet_name = pet_info.get('name', '펫')

    body = f'''
    <div style="text-align:center;margin-bottom:20px;">
      <div style="display:inline-block;width:80px;height:80px;border-radius:50%;
                  background:{colors["bg"]};border:3px solid {colors["accent"]};
                  line-height:80px;font-size:40px;">
        {pet_emoji}
      </div>
      <p style="margin:8px 0 0;font-size:12px;color:{colors["accent"]};font-weight:700;">{pet_name}</p>
    </div>
    <div style="background:linear-gradient(135deg,{colors["bg"]},{colors["bg"]}cc);
                border-radius:12px;padding:20px;text-align:center;
                border:2px solid {colors["accent"]}40;">
      <p style="font-size:18px;font-weight:800;color:{colors["text"]};margin:0;">
        피드 정원이 확장되었습니다!
      </p>
      <p style="font-size:14px;color:{colors["text"]}cc;margin:8px 0 0;">
        <strong>{couple.invite_code}</strong>님의 피드가
        <span style="font-size:24px;font-weight:900;color:{colors["accent"]};">{new_limit}</span>명으로 확장되었습니다.
      </p>
    </div>
    <p style="text-align:center;font-size:12px;color:#9ca3af;margin-top:16px;">
      더 많은 추억을 함께 나눠보세요!
    </p>
    '''

    for member in couple.members.all():
        if member.email:
            _send_raw(member.email,
                      f'[Lovesta] 피드 정원 확장 완료 ({new_limit}명)',
                      _html_template('피드 정원 확장 완료!', body, accent_color=colors['accent']))
