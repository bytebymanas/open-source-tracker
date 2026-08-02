/* ============================================================
   api.js — Typed API layer with caching
   ============================================================ */
const API = (() => {
  const BASE = '/api';

  async function _fetch(path, opts = {}) {
    const res = await fetch(BASE + path, {
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      ...opts,
    });
    if (!res.ok) {
      let err = {};
      try { err = await res.json(); } catch (_) {}
      const e = new Error(err.message || err.detail || `HTTP ${res.status}`);
      e.status = res.status;
      e.data = err;
      throw e;
    }
    return res.json();
  }

  const get    = path        => _fetch(path);
  const post   = (path, b)   => _fetch(path, { method: 'POST',   body: JSON.stringify(b) });
  const patch  = (path, b)   => _fetch(path, { method: 'PATCH',  body: JSON.stringify(b) });
  const del    = path        => _fetch(path, { method: 'DELETE' });
  const postRaw= (path, b)   => _fetch(path, { method: 'POST',   body: JSON.stringify(b) });

  return {
    health:          ()          => get('/health'),
    leaderboard:     (p, d)      => get(`/leaderboard?period=${p||'all_time'}${d?'&department='+encodeURIComponent(d):''}`),
    departments:     ()          => get('/departments'),
    students:        ()          => get('/students'),
    importStudents:  (usernames) => post('/students/import', { usernames }),
    updateStudent:   (u, body)   => patch(`/students/${u}`, body),
    deleteStudent:   (u)         => del(`/students/${u}`),
    user:            (u)         => get(`/user/${u}`),
    contributions:   (u)         => get(`/user/${u}/contributions`),
    repos:           (u)         => get(`/user/${u}/repos`),
    annotations:     (qs)        => get(`/annotations${qs||''}`),
    deleteAnnotation:(id)        => del(`/annotations/${id}`),
    rateLimit:       ()          => get('/ratelimit'),
    weights:         ()          => get('/settings/weights'),
    updateWeights:   (body)      => postRaw('/settings/weights', body),
  };
})();
