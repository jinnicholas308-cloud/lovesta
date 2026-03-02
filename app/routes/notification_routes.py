"""
Notification routes: list, mark read, unread count API, push subscription.
"""
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.notification import Notification
from app.models.push_subscription import PushSubscription

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')


@notification_bp.route('/')
@login_required
def list_notifications():
    """알림 목록 (최근 50개)."""
    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                      .order_by(Notification.created_at.desc())\
                                      .limit(50).all()
    # 페이지 진입 시 모두 읽음 처리
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
                      .update({'is_read': True})
    db.session.commit()
    return render_template('notifications/list.html', notifications=notifications)


@notification_bp.route('/unread-count')
@login_required
def unread_count():
    """읽지 않은 알림 수 (네비 뱃지용 API)."""
    count = Notification.unread_count(current_user.id)
    return jsonify({'count': count})


@notification_bp.route('/<int:nid>/read', methods=['POST'])
@login_required
def mark_read(nid):
    """개별 알림 읽음 처리 후 해당 URL로 이동."""
    n = Notification.query.get_or_404(nid)
    if n.user_id != current_user.id:
        return jsonify({'error': '권한 없음'}), 403
    n.is_read = True
    db.session.commit()
    return redirect(n.url or url_for('notification.list_notifications'))


@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """모든 알림 읽음 처리."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
                      .update({'is_read': True})
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('notification.list_notifications'))


# ──────────────────── Web Push API ────────────────────

@notification_bp.route('/push/vapid-public-key')
@login_required
def vapid_public_key():
    """클라이언트 푸시 구독용 VAPID 공개키 반환."""
    key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    return jsonify({'publicKey': key})


@notification_bp.route('/push/subscribe', methods=['POST'])
@login_required
def push_subscribe():
    """브라우저 푸시 구독 등록."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    endpoint = data.get('endpoint', '')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh', '')
    auth = keys.get('auth', '')

    if not endpoint or not p256dh or not auth:
        return jsonify({'error': 'Missing subscription data'}), 400

    # 동일 endpoint 중복 방지
    existing = PushSubscription.query.filter_by(
        user_id=current_user.id, endpoint=endpoint
    ).first()

    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
    else:
        sub = PushSubscription(
            user_id=current_user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
        )
        db.session.add(sub)

    db.session.commit()
    return jsonify({'success': True})


@notification_bp.route('/push/unsubscribe', methods=['POST'])
@login_required
def push_unsubscribe():
    """브라우저 푸시 구독 해제."""
    data = request.get_json(silent=True)
    endpoint = data.get('endpoint', '') if data else ''

    if endpoint:
        PushSubscription.query.filter_by(
            user_id=current_user.id, endpoint=endpoint
        ).delete()
        db.session.commit()

    return jsonify({'success': True})
