const STORAGE_PREFIX = "migration-toolkit:";

export function buildDraftKey(scope: string): string {
  return `${STORAGE_PREFIX}${scope}`;
}

export function readLocalDraft<T>(storageKey: string): T | null {
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function writeLocalDraft<T>(storageKey: string, value: T): void {
  window.localStorage.setItem(storageKey, JSON.stringify(value));
}

export function clearLocalDraft(storageKey: string): void {
  window.localStorage.removeItem(storageKey);
}
