/**
 * Dev mock switch — UI can run without live API metadata (codeSanity §5).
 * Set VITE_USE_MOCK_DATA=false to disable mock migration list in dev.
 */
export function isMockDataEnabled(): boolean {
  const flag = import.meta.env.VITE_USE_MOCK_DATA;
  if (flag === "true") {
    return true;
  }
  if (flag === "false") {
    return false;
  }
  return import.meta.env.DEV;
}
