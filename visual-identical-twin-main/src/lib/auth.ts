function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const prefix = `${name}=`;
  const match = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

export function getCsrfToken() {
  return readCookie("csrftoken");
}

export async function ensureLoginCsrf(nextPath = "/") {
  const next = encodeURIComponent(nextPath);
  await fetch(`/accounts/csrf/?next=${next}`, {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
}

export function redirectToLogin(nextPath = "/") {
  const next = encodeURIComponent(nextPath);
  window.location.href = `/login?next=${next}`;
}

export function submitLogout(nextPath = "/") {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/accounts/logout/";
  form.style.display = "none";

  const csrf = readCookie("csrftoken");
  if (csrf) {
    const csrfInput = document.createElement("input");
    csrfInput.type = "hidden";
    csrfInput.name = "csrfmiddlewaretoken";
    csrfInput.value = csrf;
    form.appendChild(csrfInput);
  }

  const nextInput = document.createElement("input");
  nextInput.type = "hidden";
  nextInput.name = "next";
  nextInput.value = `/login?next=${encodeURIComponent(nextPath)}`;
  form.appendChild(nextInput);

  document.body.appendChild(form);
  form.submit();
}
