export const setCookie = (name: string, value: string, days = 7) => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
};

export const getCookie = (name: string): string | null => {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
};

export const removeCookie = (name: string) => {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
};

// Generate a random UUID v4 for guest sessions and conversation IDs
export const generateId = () => crypto.randomUUID();

export const getOrCreateGuestSessionId = (): string => {
  let guestId = localStorage.getItem('guest_session_id');
  if (!guestId) {
    guestId = generateId();
    localStorage.setItem('guest_session_id', guestId);
  }
  return guestId;
};