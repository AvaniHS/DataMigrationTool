import { useCallback, useEffect, useState } from "react";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import {
  listColumns,
  listFileColumns,
  listS3Files,
  listSchemas,
  listTables,
  type ColumnNode,
  type S3FileNode,
} from "@/api/introspection";
import { logClientError } from "@/api/logger";
import { ErrorAlertWithRetry } from "@/components/shared/ErrorAlertWithRetry";
import { isMockDataEnabled } from "@/mock/mockProvider";
import {
  MOCK_COLUMNS,
  MOCK_S3_FILES,
  MOCK_SCHEMAS,
  MOCK_TABLES,
} from "@/mock/introspectionSample";

type SchemaTreeProps = {
  connectionRef: string;
  isFileConnection: boolean;
  onSelectTable?: (schema: string, table: string) => void;
  onSelectFile?: (fileName: string) => void;
};

type ExpandedState = Record<string, boolean>;

function columnKey(schema: string, table: string) {
  return `${schema}/${table}`;
}

export function SchemaTree({
  connectionRef,
  isFileConnection,
  onSelectTable,
  onSelectFile,
}: SchemaTreeProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [tablesBySchema, setTablesBySchema] = useState<Record<string, string[]>>({});
  const [columnsByTable, setColumnsByTable] = useState<Record<string, ColumnNode[]>>({});
  const [files, setFiles] = useState<S3FileNode[]>([]);
  const [columnsByFile, setColumnsByFile] = useState<Record<string, ColumnNode[]>>({});
  const [expanded, setExpanded] = useState<ExpandedState>({});

  const toggleExpanded = (key: string) => {
    setExpanded((current) => ({ ...current, [key]: !current[key] }));
  };

  const loadMockDatabaseTree = useCallback(() => {
    setSchemas(MOCK_SCHEMAS.map((item) => item.name));
    const tables: Record<string, string[]> = {};
    for (const [schema, tableNodes] of Object.entries(MOCK_TABLES)) {
      tables[schema] = tableNodes.map((item) => item.name);
    }
    setTablesBySchema(tables);
    const columns: Record<string, ColumnNode[]> = {};
    for (const [key, columnNodes] of Object.entries(MOCK_COLUMNS)) {
      columns[key.replace("/", "/")] = columnNodes;
    }
    setColumnsByTable(columns);
  }, []);

  const loadDatabaseTree = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const schemaNodes = await listSchemas(connectionRef);
      setSchemas(schemaNodes.map((item) => item.name));
      setTablesBySchema({});
      setColumnsByTable({});
      setExpanded({});
    } catch (err) {
      if (isMockDataEnabled()) {
        logClientError("schema_tree_mock_fallback", { connectionRef, error: String(err) });
        loadMockDatabaseTree();
        return;
      }
      setError("Unable to read schema metadata. Check connection credentials and API access.");
      logClientError("schema_tree_load_failed", { connectionRef, error: String(err) });
    } finally {
      setLoading(false);
    }
  }, [connectionRef, loadMockDatabaseTree]);

  const loadFiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setFiles(await listS3Files(connectionRef));
      setColumnsByFile({});
      setExpanded({});
    } catch (err) {
      if (isMockDataEnabled()) {
        logClientError("schema_tree_s3_mock_fallback", { connectionRef, error: String(err) });
        setFiles(MOCK_S3_FILES);
        return;
      }
      setError("Unable to list files. Check bucket URI, IAM permissions, and API access.");
      logClientError("schema_tree_files_load_failed", { connectionRef, error: String(err) });
    } finally {
      setLoading(false);
    }
  }, [connectionRef]);

  useEffect(() => {
    if (!connectionRef) {
      return;
    }
    if (isFileConnection) {
      void loadFiles();
      return;
    }
    void loadDatabaseTree();
  }, [connectionRef, isFileConnection, loadDatabaseTree, loadFiles]);

  const ensureTablesLoaded = async (schema: string) => {
    if (tablesBySchema[schema]) {
      return;
    }
    try {
      const tableNodes = await listTables(connectionRef, schema);
      setTablesBySchema((current) => ({
        ...current,
        [schema]: tableNodes.map((item) => item.name),
      }));
    } catch (err) {
      if (isMockDataEnabled()) {
        setTablesBySchema((current) => ({
          ...current,
          [schema]: (MOCK_TABLES[schema] ?? []).map((item) => item.name),
        }));
        return;
      }
      setError("Unable to read tables for the selected schema.");
      logClientError("schema_tree_tables_failed", { connectionRef, schema, error: String(err) });
    }
  };

  const ensureColumnsLoaded = async (schema: string, table: string) => {
    const key = columnKey(schema, table);
    if (columnsByTable[key]) {
      return;
    }
    try {
      const columnNodes = await listColumns(connectionRef, schema, table);
      setColumnsByTable((current) => ({ ...current, [key]: columnNodes }));
    } catch (err) {
      if (isMockDataEnabled()) {
        setColumnsByTable((current) => ({
          ...current,
          [key]: MOCK_COLUMNS[key] ?? [],
        }));
        return;
      }
      setError("Unable to read columns for the selected table.");
      logClientError("schema_tree_columns_failed", {
        connectionRef,
        schema,
        table,
        error: String(err),
      });
    }
  };

  const ensureFileColumnsLoaded = async (fileName: string) => {
    if (columnsByFile[fileName]) {
      return;
    }
    try {
      const columnNodes = await listFileColumns(connectionRef, fileName);
      setColumnsByFile((current) => ({ ...current, [fileName]: columnNodes }));
    } catch (err) {
      setError("Unable to read columns from the selected file sample.");
      logClientError("schema_tree_file_columns_failed", {
        connectionRef,
        fileName,
        error: String(err),
      });
    }
  };

  const handleSchemaClick = async (schema: string) => {
    toggleExpanded(`schema:${schema}`);
    await ensureTablesLoaded(schema);
  };

  const handleTableClick = async (schema: string, table: string) => {
    toggleExpanded(`table:${schema}.${table}`);
    await ensureColumnsLoaded(schema, table);
    onSelectTable?.(schema, table);
  };

  const handleFileClick = async (fileName: string) => {
    toggleExpanded(`file:${fileName}`);
    await ensureFileColumnsLoaded(fileName);
    onSelectFile?.(fileName);
  };

  if (!connectionRef) {
    return (
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Select a connection to browse schema metadata.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 1, maxHeight: 360, overflow: "auto" }}>
      <Typography variant="caption" color="text.secondary" sx={{ px: 1 }}>
        Schema tree · {connectionRef}
      </Typography>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
          <CircularProgress size={20} />
        </Box>
      )}

      {error && (
        <Box sx={{ p: 1 }}>
          <ErrorAlertWithRetry
            message={error}
            onRetry={() => (isFileConnection ? void loadFiles() : void loadDatabaseTree())}
          />
        </Box>
      )}

      {!loading && !error && isFileConnection && (
        <List dense disablePadding>
          {files.map((file) => {
            const fileOpen = expanded[`file:${file.name}`];
            const columns = columnsByFile[file.name] ?? [];
            return (
              <Box key={file.key}>
                <ListItemButton onClick={() => void handleFileClick(file.name)} sx={{ py: 0.25 }}>
                  <IconButton size="small" edge="start" tabIndex={-1}>
                    {fileOpen ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
                  </IconButton>
                  <ListItemText primary={file.name} secondary={file.key} />
                </ListItemButton>
                <Collapse in={fileOpen} unmountOnExit>
                  <List dense disablePadding sx={{ pl: 4 }}>
                    {columns.map((column) => (
                      <ListItemButton key={column.name} sx={{ py: 0 }}>
                        <ListItemText
                          primary={column.name}
                          secondary={`${column.data_type}${column.is_nullable ? "" : " · NOT NULL"}`}
                        />
                      </ListItemButton>
                    ))}
                    {columns.length === 0 && (
                      <Typography variant="body2" color="text.secondary" sx={{ pl: 2, py: 0.5 }}>
                        Loading columns…
                      </Typography>
                    )}
                  </List>
                </Collapse>
              </Box>
            );
          })}
          {files.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ p: 1 }}>
              No CSV files found for this connection.
            </Typography>
          )}
        </List>
      )}

      {!loading && !error && !isFileConnection && (
        <List dense disablePadding>
          {schemas.map((schema) => {
            const schemaOpen = expanded[`schema:${schema}`];
            const tables = tablesBySchema[schema] ?? [];
            return (
              <Box key={schema}>
                <ListItemButton onClick={() => void handleSchemaClick(schema)} sx={{ py: 0.25 }}>
                  <IconButton size="small" edge="start" tabIndex={-1}>
                    {schemaOpen ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
                  </IconButton>
                  <ListItemText primary={schema} />
                </ListItemButton>
                <Collapse in={schemaOpen} unmountOnExit>
                  <List dense disablePadding sx={{ pl: 3 }}>
                    {tables.map((table) => {
                      const tableOpen = expanded[`table:${schema}.${table}`];
                      const columns = columnsByTable[columnKey(schema, table)] ?? [];
                      return (
                        <Box key={table}>
                          <ListItemButton
                            onClick={() => void handleTableClick(schema, table)}
                            sx={{ py: 0.25 }}
                          >
                            <IconButton size="small" edge="start" tabIndex={-1}>
                              {tableOpen ? (
                                <ExpandMoreIcon fontSize="small" />
                              ) : (
                                <ChevronRightIcon fontSize="small" />
                              )}
                            </IconButton>
                            <ListItemText primary={table} />
                          </ListItemButton>
                          <Collapse in={tableOpen} unmountOnExit>
                            <List dense disablePadding sx={{ pl: 4 }}>
                              {columns.map((column) => (
                                <ListItemButton key={column.name} sx={{ py: 0 }}>
                                  <ListItemText
                                    primary={column.name}
                                    secondary={`${column.data_type}${column.is_nullable ? "" : " · NOT NULL"}`}
                                  />
                                </ListItemButton>
                              ))}
                            </List>
                          </Collapse>
                        </Box>
                      );
                    })}
                  </List>
                </Collapse>
              </Box>
            );
          })}
        </List>
      )}
    </Paper>
  );
}
