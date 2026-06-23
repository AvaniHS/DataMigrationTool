import { useEffect, useState } from "react";
import { readLocalDraft, writeLocalDraft } from "@/storage/localDraft";

export function useLocalDraft<T>(storageKey: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => readLocalDraft<T>(storageKey) ?? initialValue);

  useEffect(() => {
    writeLocalDraft(storageKey, value);
  }, [storageKey, value]);

  return [value, setValue] as const;
}
