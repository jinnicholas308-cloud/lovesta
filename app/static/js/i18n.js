/**
 * Lovesta i18n — Korean ↔ English
 * 사용법:
 *   <span data-i18n="couple.day_unit">일</span>
 *   <input data-i18n-placeholder="upload.caption_ph" />
 */
(function () {
  var LANG_KEY = 'lovesta_lang';

  var TRANSLATIONS = {
    ko: {
      /* ── Navigation ── */
      'nav.upload':        '+ 추억 업로드',
      'nav.couple':        '💑 커플',
      'nav.admin':         '🛠️ 관리',
      'nav.logout':        '로그아웃',
      'nav.profile':       '프로필',
      'nav.feed':          '피드',

      /* ── Couple page ── */
      'couple.together_for': '함께한 지',
      'couple.day_unit':     '일',
      'couple.since':        '부터',
      'couple.invite_code':  '커플 초대 코드',
      'couple.copy':         '복사하기',
      'couple.members':      '멤버',
      'couple.me':           '나',
      'couple.back':         '← 피드로 돌아가기',

      /* ── Profile page ── */
      'profile.basic':       '기본 정보',
      'profile.username':    '사용자명',
      'profile.birthday':    '🎂 생일',
      'profile.food':        '🍜 좋아하는 음식',
      'profile.mbti':        '🧠 MBTI',
      'profile.bio':         '✏️ 한 줄 소개',
      'profile.no_select':   '선택 안 함',
      'profile.pet':         '우리 펫 🐾',
      'profile.pet_name':    '펫 이름 변경',
      'profile.save':        '저장하기 💾',
      'profile.partner':     '파트너 💑',
      'profile.account':     '계정',
      'profile.joined':      '가입일',
      'profile.login_type':  '로그인 방식',
      'profile.logout':      '로그아웃',
      'profile.together':    '함께한 지',
      'profile.days':        '일째 🌸',

      /* ── Pet widget ── */
      'pet.days':      '일째 🌸',
      'pet.hatching':  '곧 깨어나요 🥚',
      'pet.grown':     '다 컸어요! 🎉',
      'pet.caption':   '우리의 소중한 펫이에요 💕',

      /* ── Auth pages ── */
      'login.tagline':    '우리의 추억을 함께 기록해요',
      'login.google':     'Google로 로그인',
      'login.or_email':   '또는 이메일로',
      'login.email':      '이메일',
      'login.password':   '비밀번호',
      'login.remember':   '로그인 유지 (30일)',
      'login.forgot':     '아이디 / 비밀번호 찾기',
      'login.submit':     '로그인',
      'login.no_account': '계정이 없으신가요?',
      'login.register':   '회원가입',

      /* ── Feed page ── */
      'feed.days_label':    '일 ♥',
      'feed.together_for':  '함께한 지',
      'feed.add':           '+ 추억 추가',
      'feed.empty_title':   '아직 추억이 없네요',
      'feed.empty_sub':     '첫 번째 추억을 기록해보세요!',
      'feed.first_upload':  '첫 추억 업로드',
      'feed.prev':          '이전',
      'feed.next':          '다음',

      /* ── Upload page ── */
      'upload.title':      '📷 추억 기록하기',
      'upload.photo':      '사진',
      'upload.click_to':   '클릭해서 사진 선택',
      'upload.file_hint':  'PNG, JPG, GIF, WEBP (최대 16MB)',
      'upload.caption':    '캡션',
      'upload.location':   '장소',
      'upload.optional':   '(선택)',
      'upload.date':       '날짜',
      'upload.cancel':     '취소',
      'upload.submit':     '✨ 업로드',
      'upload.loading':    '업로드 중...',

      /* ── Detail page ── */
      'detail.back':       '← 뒤로가기',
      'detail.like':       '좋아요',
      'detail.comment':    '댓글',
      'detail.comment_ph': '따뜻한 댓글을 남겨보세요...',
      'detail.send':       '작성',
      'detail.delete':     '삭제',
    },

    en: {
      /* ── Navigation ── */
      'nav.upload':        '+ Upload Memory',
      'nav.couple':        '💑 Couple',
      'nav.admin':         '🛠️ Admin',
      'nav.logout':        'Logout',
      'nav.profile':       'Profile',
      'nav.feed':          'Feed',

      /* ── Couple page ── */
      'couple.together_for': 'Together for',
      'couple.day_unit':     'days',
      'couple.since':        'since',
      'couple.invite_code':  'Couple Invite Code',
      'couple.copy':         'Copy',
      'couple.members':      'Members',
      'couple.me':           'me',
      'couple.back':         '← Back to Feed',

      /* ── Profile page ── */
      'profile.basic':       'Basic Info',
      'profile.username':    'Username',
      'profile.birthday':    '🎂 Birthday',
      'profile.food':        '🍜 Favorite Food',
      'profile.mbti':        '🧠 MBTI',
      'profile.bio':         '✏️ Bio',
      'profile.no_select':   'Not selected',
      'profile.pet':         'Our Pet 🐾',
      'profile.pet_name':    'Change Pet Name',
      'profile.save':        'Save 💾',
      'profile.partner':     'Partner 💑',
      'profile.account':     'Account',
      'profile.joined':      'Joined',
      'profile.login_type':  'Login',
      'profile.logout':      'Logout',
      'profile.together':    'Together for',
      'profile.days':        'days 🌸',

      /* ── Pet widget ── */
      'pet.days':      'days 🌸',
      'pet.hatching':  'Hatching soon 🥚',
      'pet.grown':     'Fully grown! 🎉',
      'pet.caption':   'Our little companion 💕',

      /* ── Auth pages ── */
      'login.tagline':    'Record our memories together',
      'login.google':     'Sign in with Google',
      'login.or_email':   'or with email',
      'login.email':      'Email',
      'login.password':   'Password',
      'login.remember':   'Remember me (30 days)',
      'login.forgot':     'Forgot ID / Password',
      'login.submit':     'Login',
      'login.no_account': "Don't have an account?",
      'login.register':   'Sign Up',

      /* ── Feed page ── */
      'feed.days_label':    'days ♥',
      'feed.together_for':  'Together for',
      'feed.add':           '+ Add Memory',
      'feed.empty_title':   'No memories yet',
      'feed.empty_sub':     'Start recording your first memory!',
      'feed.first_upload':  'Upload First Memory',
      'feed.prev':          'Prev',
      'feed.next':          'Next',

      /* ── Upload page ── */
      'upload.title':      '📷 Record a Memory',
      'upload.photo':      'Photo',
      'upload.click_to':   'Click to select a photo',
      'upload.file_hint':  'PNG, JPG, GIF, WEBP (max 16MB)',
      'upload.caption':    'Caption',
      'upload.location':   'Location',
      'upload.optional':   '(optional)',
      'upload.date':       'Date',
      'upload.cancel':     'Cancel',
      'upload.submit':     '✨ Upload',
      'upload.loading':    'Uploading...',

      /* ── Detail page ── */
      'detail.back':       '← Back',
      'detail.like':       'Like',
      'detail.comment':    'Comment',
      'detail.comment_ph': 'Leave a warm comment...',
      'detail.send':       'Post',
      'detail.delete':     'Delete',
    }
  };

  var currentLang = localStorage.getItem(LANG_KEY) || 'ko';

  function applyLang(lang) {
    var html = document.getElementById('html-root');
    if (html) html.lang = lang;

    /* 1. data-i18n → textContent */
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      var val = (TRANSLATIONS[lang] || {})[key];
      if (val != null) el.textContent = val;
    });

    /* 2. data-i18n-placeholder → placeholder */
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-placeholder');
      var val = (TRANSLATIONS[lang] || {})[key];
      if (val != null) el.placeholder = val;
    });

    /* 3. Legacy data-ko / data-en 하위 호환 */
    document.querySelectorAll('[data-ko][data-en]').forEach(function (el) {
      var val = el.getAttribute('data-' + lang);
      if (val != null) el.textContent = val;
    });

    /* 4. 언어 토글 버튼 레이블 갱신 */
    ['lang-btn', 'lang-btn-mobile'].forEach(function (id) {
      var btn = document.getElementById(id);
      if (btn) btn.textContent = lang === 'ko' ? 'EN' : '한';
    });

    localStorage.setItem(LANG_KEY, lang);
    currentLang = lang;
  }

  /* 언어 토글 (전역) */
  window.toggleLang = function () {
    applyLang(currentLang === 'ko' ? 'en' : 'ko');
  };

  /* 번역 함수 노출 */
  window.i18n = {
    t: function (key) {
      return (TRANSLATIONS[currentLang] || {})[key]
          || (TRANSLATIONS.ko || {})[key]
          || key;
    },
    lang: function () { return currentLang; }
  };

  /* 페이지 로드 시 적용 (스크립트는 </body> 직전에 위치) */
  if (currentLang !== 'ko') applyLang(currentLang);
})();
