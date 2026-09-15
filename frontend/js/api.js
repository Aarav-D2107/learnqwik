/* ============================================================
   LEARNQWIK — API CLIENT

   The single place the frontend talks to the backend. No raw fetch()
   anywhere else in the application.

   Responsibilities:
     - resolve the backend URL from build-time configuration
     - attach the access token to authenticated requests
     - refresh the session once on a 401 and retry
     - turn structured backend errors into ApiError objects the UI can read
   ============================================================ */

const API_BASE = (window.LEARNQWIK_ENV && window.LEARNQWIK_ENV.API_BASE_URL) || "";

if (!API_BASE) {
  console.error(
    "LearnQwik: API_BASE_URL is not configured. Run `node build.js` in frontend/, " +
      "or check js/env.js."
  );
}

class ApiError extends Error {
  constructor(code, message, status, details) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details || null;
  }

  /** True when the failure is worth offering a retry button for. */
  get retryable() {
    return this.status === 0 || this.status >= 500 || this.code === "RATE_LIMITED";
  }

  get isAuthError() {
    return this.status === 401 || this.code === "SESSION_EXPIRED";
  }

  get isAiConfigError() {
    return this.code === "AI_NOT_CONFIGURED";
  }
}

const Api = {
  ApiError,
  baseUrl: API_BASE,

  /* -------------------- core -------------------- */
  async request(path, options = {}) {
    const { method = "GET", body, auth = true, isForm = false, retryOn401 = true } = options;

    const headers = {};
    if (!isForm) headers["Content-Type"] = "application/json";

    if (auth) {
      const token = Auth.accessToken();
      if (!token) throw new ApiError("NOT_AUTHENTICATED", "Please sign in to continue.", 401);
      headers.Authorization = "Bearer " + token;
    }

    let response;
    try {
      response = await fetch(API_BASE + path, {
        method,
        headers,
        body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
      });
    } catch (networkError) {
      throw new ApiError(
        "NETWORK_ERROR",
        "Couldn't reach the LearnQwik server. Check your connection and try again.",
        0
      );
    }

    if (response.status === 401 && auth && retryOn401) {
      const refreshed = await Auth.tryRefresh();
      if (refreshed) {
        return this.request(path, { ...options, retryOn401: false });
      }
      Auth.clearSession();
    }

    if (response.status === 204) return null;

    let payload = null;
    const text = await response.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (e) {
        payload = null;
      }
    }

    if (!response.ok) {
      const code = (payload && payload.error) || "REQUEST_FAILED";
      const message =
        (payload && payload.message) || "Something went wrong. Please try again.";
      throw new ApiError(code, message, response.status, payload && payload.fields);
    }

    return payload;
  },

  get(path, options) {
    return this.request(path, { ...options, method: "GET" });
  },
  post(path, body, options) {
    return this.request(path, { ...options, method: "POST", body });
  },
  del(path, options) {
    return this.request(path, { ...options, method: "DELETE" });
  },

  /* -------------------- health / config -------------------- */
  health() {
    return this.get("/health", { auth: false });
  },
  runtimeConfig() {
    return this.get("/api/config", { auth: false });
  },

  /* -------------------- auth -------------------- */
  signUp(email, password, fullName) {
    return this.post("/api/auth/signup", { email, password, full_name: fullName }, { auth: false });
  },
  signIn(email, password) {
    return this.post("/api/auth/login", { email, password }, { auth: false });
  },
  signOut() {
    return this.post("/api/auth/logout", {});
  },
  me() {
    return this.get("/api/auth/me");
  },

  /* -------------------- curriculum -------------------- */
  subjects() {
    return this.get("/api/subjects", { auth: !!Auth.accessToken() });
  },
  topics(subjectId) {
    return this.get(`/api/subjects/${encodeURIComponent(subjectId)}/topics`, {
      auth: !!Auth.accessToken(),
    });
  },
  topic(topicId) {
    return this.get(`/api/topics/${encodeURIComponent(topicId)}`, {
      auth: !!Auth.accessToken(),
    });
  },

  /* -------------------- quiz -------------------- */
  startQuiz(subjectId, topicId, mode) {
    return this.post("/api/quiz/start", {
      subject_id: subjectId,
      topic_id: topicId,
      mode: mode || "quiz",
    });
  },
  startReassessment(subjectId, topicId) {
    return this.post("/api/assessment/reassess", { subject_id: subjectId, topic_id: topicId });
  },
  saveAnswer(attemptId, questionId, selectedIndex, responseTimeMs) {
    return this.post(`/api/quiz/${attemptId}/answer`, {
      question_id: questionId,
      selected_index: selectedIndex,
      response_time_ms: responseTimeMs,
    });
  },
  completeQuiz(attemptId, violations, autoSubmitted, timeUsedSeconds) {
    return this.post(`/api/quiz/${attemptId}/complete`, {
      fullscreen_violations: violations || 0,
      auto_submitted: !!autoSubmitted,
      time_used_seconds: timeUsedSeconds,
    });
  },

  /* -------------------- analytics -------------------- */
  overview() {
    return this.get("/api/analytics/overview");
  },
  topicAnalytics(subjectId) {
    return this.get("/api/analytics/topics" + (subjectId ? `?subject_id=${subjectId}` : ""));
  },
  progress(topicId) {
    return this.get("/api/analytics/progress" + (topicId ? `?topic_id=${topicId}` : ""));
  },
  improvement() {
    return this.get("/api/analytics/improvement");
  },

  /* -------------------- recommendations / roadmap -------------------- */
  recommendations(params = {}) {
    const query = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
    ).toString();
    return this.get("/api/recommendations" + (query ? "?" + query : ""));
  },
  roadmap(subjectId) {
    return this.get(`/api/roadmap?subject_id=${encodeURIComponent(subjectId)}`);
  },
  recomputeRoadmap(subjectId, triggerAttemptId) {
    return this.post("/api/roadmap/recompute", {
      subject_id: subjectId,
      trigger_attempt_id: triggerAttemptId || null,
      force: true,
    });
  },
  roadmapVersions(subjectId) {
    return this.get(`/api/roadmap/versions?subject_id=${encodeURIComponent(subjectId)}`);
  },

  /* -------------------- AI -------------------- */
  askTutor({ message, subject, topic, conversation, documentId, pageContext }) {
    return this.post("/api/ai/tutor", {
      message,
      subject: subject || null,
      topic: topic || null,
      conversation: conversation || [],
      document_id: documentId || null,
      page_context: pageContext || null,
    });
  },
  explainAttempt(attemptId) {
    return this.post("/api/ai/explain", { attempt_id: attemptId });
  },

  /* -------------------- documents -------------------- */
  uploadDocument(file) {
    const form = new FormData();
    form.append("file", file);
    return this.request("/api/uploads", { method: "POST", body: form, isForm: true });
  },
  uploads() {
    return this.get("/api/uploads");
  },
  upload(fileId) {
    return this.get(`/api/uploads/${fileId}`);
  },
  uploadStatus(fileId) {
    return this.get(`/api/uploads/${fileId}/status`);
  },
  deleteUpload(fileId) {
    return this.del(`/api/uploads/${fileId}`);
  },
  documentSummary(fileId, regenerate) {
    return this.post(`/api/uploads/${fileId}/summary`, { regenerate: !!regenerate });
  },
  documentQuiz(fileId, questionCount, regenerate) {
    return this.post(`/api/uploads/${fileId}/quiz`, {
      question_count: questionCount || 8,
      regenerate: !!regenerate,
    });
  },
  gradeDocumentQuiz(fileId, quizId, answers) {
    return this.post(`/api/uploads/${fileId}/quiz/${quizId}/grade`, { answers });
  },
  askDocument(fileId, message, conversation, pageContext) {
    return this.post(`/api/uploads/${fileId}/ask`, {
      message,
      conversation: conversation || [],
      page_context: pageContext || null,
    });
  },
};

window.Api = Api;
window.ApiError = ApiError;
