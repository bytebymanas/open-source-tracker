/* ============================================================
   state.js — Simple client-side state & cache
   ============================================================ */
const State = (() => {
  const _state = {
    profileUsername: null,
    lbPeriod:        'all_time',
    lbDept:          '',
    lbSearch:        '',
    contribSearch:   '',
    contribDept:     '',
    activityFilter:  '',
    allStudents:     null,     // cached student list
    departments:     [],
  };

  const _cache = {};  // TTL response cache

  function get(key) { return _state[key]; }
  function set(key, val) { _state[key] = val; }

  // Simple TTL cache (60s default)
  function cache(key, fn, ttl = 60000) {
    const now = Date.now();
    if (_cache[key] && _cache[key].ts + ttl > now) {
      return Promise.resolve(_cache[key].data);
    }
    return fn().then(data => {
      _cache[key] = { data, ts: now };
      return data;
    });
  }

  function invalidate(key) {
    if (key) delete _cache[key];
    else Object.keys(_cache).forEach(k => delete _cache[k]);
  }

  return { get, set, cache, invalidate };
})();
