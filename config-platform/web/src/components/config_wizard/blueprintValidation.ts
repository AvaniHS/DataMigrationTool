import type { Blueprint } from "@/components/migrations/types";
import type { ConnectionListItem } from "@/components/connections/types";
import type { BlueprintWizardStepId } from "./types";
import { connectionExportType, isFileConnectionType } from "./blueprintHelpers";

export type StepValidationResult = {
  valid: boolean;
  errors: string[];
};

function connectionRefSet(connections: ConnectionListItem[]): Set<string> {
  return new Set(connections.map((item) => item.ref));
}

function isFileSource(connectionRef: string, refs: Set<string>, connections: ConnectionListItem[]): boolean {
  if (!refs.has(connectionRef)) {
    return false;
  }
  const exportType = connectionExportType(connections, connectionRef);
  return exportType ? isFileConnectionType(exportType) : false;
}

export function validateSourcesStep(
  blueprint: Blueprint,
  connections: ConnectionListItem[],
): StepValidationResult {
  const errors: string[] = [];
  const refs = connectionRefSet(connections);
  const root = blueprint.sources.root_table;

  if (!root.connection_ref.trim()) {
    errors.push("Root source connection is required.");
  } else if (!refs.has(root.connection_ref)) {
    errors.push(`Root connection '${root.connection_ref}' does not exist.`);
  }

  if (!root.alias.trim()) {
    errors.push("Root source alias is required.");
  }

  if (root.connection_ref && refs.has(root.connection_ref)) {
    if (isFileSource(root.connection_ref, refs, connections)) {
      if (!root.file_name?.trim()) {
        errors.push("Root file name is required for file-backed sources.");
      }
    } else if (!root.schema.trim() || !root.table_name.trim()) {
      errors.push("Root schema and table are required for database sources.");
    }
  }

  blueprint.sources.joins.forEach((join, index) => {
    const label = `Join ${index + 1}`;
    if (!join.connection_ref.trim()) {
      errors.push(`${label}: connection is required.`);
    } else if (!refs.has(join.connection_ref)) {
      errors.push(`${label}: connection '${join.connection_ref}' does not exist.`);
    }
    if (!join.alias.trim()) {
      errors.push(`${label}: alias is required.`);
    }
    if (join.connection_ref && refs.has(join.connection_ref)) {
      if (isFileSource(join.connection_ref, refs, connections)) {
        if (!join.file_name?.trim()) {
          errors.push(`${label}: file name is required.`);
        }
      } else if (!join.schema.trim() || !join.table_name.trim()) {
        errors.push(`${label}: schema and table are required.`);
      }
    }
    if (join.conditions.length === 0) {
      errors.push(`${label}: at least one join condition is required.`);
    }
    join.conditions.forEach((condition, conditionIndex) => {
      if (!condition.left_expression.trim() || !condition.right_expression.trim()) {
        errors.push(`${label}: condition ${conditionIndex + 1} expressions are required.`);
      }
      if (!condition.operator.trim()) {
        errors.push(`${label}: condition ${conditionIndex + 1} operator is required.`);
      }
    });
  });

  return { valid: errors.length === 0, errors };
}

export function validateTargetStep(
  blueprint: Blueprint,
  connections: ConnectionListItem[],
): StepValidationResult {
  const errors: string[] = [];
  const refs = connectionRefSet(connections);
  const target = blueprint.target;

  if (!target.connection_ref.trim()) {
    errors.push("Target connection is required.");
  } else if (!refs.has(target.connection_ref)) {
    errors.push(`Target connection '${target.connection_ref}' does not exist.`);
  }
  if (!target.schema.trim()) {
    errors.push("Target schema is required.");
  }
  if (!target.table_name.trim()) {
    errors.push("Target table is required.");
  }
  if (target.primary_keys.length === 0) {
    errors.push("Select at least one primary key column.");
  }
  if (
    target.on_conflict === "IGNORE_AND_INSERT_UNPROCESSED" &&
    !target.unprocessed_table?.trim()
  ) {
    errors.push("Unprocessed table name is required for IGNORE_AND_INSERT_UNPROCESSED.");
  }

  return { valid: errors.length === 0, errors };
}

export function validateMappingsStep(blueprint: Blueprint): StepValidationResult {
  const errors: string[] = [];

  blueprint.derivations.forEach((derivation, index) => {
    if (!derivation.variable_name.trim()) {
      errors.push(`Derivation ${index + 1}: variable name is required.`);
    }
    if (!derivation.expression.trim()) {
      errors.push(`Derivation ${index + 1}: expression is required.`);
    }
  });

  if (blueprint.mappings.length === 0) {
    errors.push("At least one column mapping is required.");
  }

  blueprint.mappings.forEach((mapping) => {
    if (!mapping.target_column.trim()) {
      errors.push("Each mapping requires a target column.");
    }
    if (!mapping.source_type.trim()) {
      errors.push(`Mapping '${mapping.target_column}': source type is required.`);
    }
    if (!mapping.source_value.trim()) {
      errors.push(`Mapping '${mapping.target_column}': source value is required.`);
    }
    if (!mapping.cast_to.trim()) {
      errors.push(`Mapping '${mapping.target_column}': cast_to is required.`);
    }
  });

  return { valid: errors.length === 0, errors };
}

export function validateFiltersStep(blueprint: Blueprint): StepValidationResult {
  const errors: string[] = [];
  const chunking = blueprint.chunking_strategy;

  if (chunking.is_enabled) {
    if (!chunking.chunk_by_column?.trim()) {
      errors.push("Chunk column is required when chunking is enabled.");
    }
    if (!chunking.chunk_size || chunking.chunk_size < 1) {
      errors.push("Chunk size must be at least 1 when chunking is enabled.");
    }
  }

  blueprint.pre_filters.forEach((filter, index) => {
    if (!filter.trim()) {
      errors.push(`Pre-filter ${index + 1} cannot be empty.`);
    }
  });
  blueprint.post_filters.forEach((filter, index) => {
    if (!filter.trim()) {
      errors.push(`Post-filter ${index + 1} cannot be empty.`);
    }
  });

  return { valid: errors.length === 0, errors };
}

export function validateWizardStep(
  stepId: BlueprintWizardStepId,
  blueprint: Blueprint,
  connections: ConnectionListItem[],
): StepValidationResult {
  switch (stepId) {
    case "sources":
      return validateSourcesStep(blueprint, connections);
    case "target":
      return validateTargetStep(blueprint, connections);
    case "mappings":
      return validateMappingsStep(blueprint);
    case "filters":
      return validateFiltersStep(blueprint);
    case "review":
      return { valid: true, errors: [] };
    default:
      return { valid: true, errors: [] };
  }
}
