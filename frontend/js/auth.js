/* ============================================================
   LEARNQWIK — AUTHENTICATION

   Real Supabase Auth, proxied through the FastAPI backend. The browser
   holds a session token, never a Supabase credential: there is no anon
   key and no service-role key anywhere in this bundle.

   What lives in localStorage: the session tokens and the user's display
   name, so a refresh doesn't sign you out. That is session state, not
   learning data — every quiz attempt, mastery score, roadmap and upload
   lives in Postgres and is fetched from the backend on demand.
   ============================================================ */

const SESSION_KEY = "lq_session";

const Auth = {
  _session: null,
  _refreshing: null,

  load() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      this._session = raw ? JSON.parse(raw) : null;
    } catch (e) {
      this._session = null;
    }
    if (this._session && this._session.expires_at && Date.now() > this._session.expires_at) {
      // Expired on disk — keep the refresh token, drop the access token.
      this._session.access_token = null;
    }
    return this._session;
  },

  save(payload) {
    const expiresIn = payload.expires_in || 3600;
    this._session = {
      access_token: payload.access_token,
      refresh_token: payload.refresh_token,
      expires_at: Date.now() + (expiresIn - 60) * 1000,
      user: payload.user || null,
    };
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify(this._session));
    } catch (e) {
      /* private browsing — session lasts for this tab only */
    }
    return this._session;
  },

  clearSession() {
    this._session = null;
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (e) {}
  },

  accessToken() {
    if (!this._session) this.load();
    return this._session ? this._session.access_token : null;
  },

  user() {
    if (!this._session) this.load();
    return this._session ? this._session.user : null;
  },

  isSignedIn() {
    return !!this.accessToken();
  },

  async signUp(email, password, fullName) {
    const data = await Api.signUp(email, password, fullName);
    if (data.access_token) {
      this.save(data);
      return { signedIn: true, user: data.user };
    }
    // Email confirmation is on in this Supabase project.
    return { signedIn: false, message: data.message, user: data.user };
  },

  async signIn(email, password) {
    const data = await Api.signIn(email, password);
    this.save(data);
    return data.user;
  },

  async signOut() {
    try {
      if (this.accessToken()) await Api.signOut();
    } catch (e) {
      /* signing out locally matters more than the server round-trip */
    }
    this.clearSession();
  },

  /**
   * Exchanges the refresh token for a new access token. Called automatically
   * by the API client on a 401. Concurrent calls share one in-flight request.
   */
  async tryRefresh() {
    if (!this._session || !this._session.refresh_token) return false;
    if (this._refreshing) return this._refreshing;

    this._refreshing = (async () => {
      try {
        const data = await Api.request("/api/auth/refresh", {
          method: "POST",
          body: { refresh_token: this._session.refresh_token },
          auth: false,
        });
        if (data && data.access_token) {
          this.save(data);
          return true;
        }
        return false;
      } catch (e) {
        return false;
      } finally {
        this._refreshing = null;
      }
    })();

    return this._refreshing;
  },

  /** Confirms with the backend that the stored token is still valid. */
  async hydrate() {
    if (!this.accessToken()) {
      if (this._session && this._session.refresh_token) {
        const ok = await this.tryRefresh();
        if (!ok) {
          this.clearSession();
          return null;
        }
      } else {
        return null;
      }
    }
    try {
      const data = await Api.me();
      if (data && data.user) {
        this._session.user = data.user;
        this.save({ ...this._session, expires_in: 3600 });
        return data.user;
      }
    } catch (e) {
      if (e instanceof ApiError && e.isAuthError) this.clearSession();
    }
    return this.user();
  },
};

window.Auth = Auth;
Auth.load();
