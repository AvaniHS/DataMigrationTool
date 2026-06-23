import { buildDraftKey } from "@/storage/localDraft";
import { useLocalDraft } from "@/hooks/useLocalDraft";

export function useWizardStepIndex(migrationId: string, stepCount: number) {
  const storageKey = buildDraftKey(`wizard-step:${migrationId}`);
  const [activeStepIndex, setActiveStepIndex] = useLocalDraft(storageKey, 0);

  const setStepIndex = (nextIndex: number) => {
    const bounded = Math.max(0, Math.min(stepCount - 1, nextIndex));
    setActiveStepIndex(bounded);
  };

  return [activeStepIndex, setStepIndex] as const;
}
