import { buildDraftKey } from "@/storage/localDraft";
import { useLocalDraft } from "@/hooks/useLocalDraft";

export function buildWizardStepDraftKey(migrationId: string, blueprintSequence: number): string {
  return buildDraftKey(`wizard-step:${migrationId}:${blueprintSequence}`);
}

export function useWizardStepIndex(
  migrationId: string,
  blueprintSequence: number,
  stepCount: number,
) {
  const storageKey = buildWizardStepDraftKey(migrationId, blueprintSequence);
  const [activeStepIndex, setActiveStepIndex] = useLocalDraft(storageKey, 0);

  const setStepIndex = (nextIndex: number) => {
    const bounded = Math.max(0, Math.min(stepCount - 1, nextIndex));
    setActiveStepIndex(bounded);
  };

  return [activeStepIndex, setStepIndex] as const;
}
