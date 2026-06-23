import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/layouts/AppLayout";
import { ConfigBuilderView } from "@/views/ConfigBuilderView";
import { ConnectionsView } from "@/views/ConnectionsView";
import { DatabaseStudioView } from "@/views/DatabaseStudioView";
import { MigrationDetailView } from "@/views/MigrationDetailView";
import { MigrationRunnerView } from "@/views/MigrationRunnerView";
import { ValidationEngineView } from "@/views/ValidationEngineView";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/migrations" replace />} />
        <Route path="connections" element={<ConnectionsView />} />
        <Route path="migrations" element={<ConfigBuilderView />} />
        <Route path="migrations/:migrationId" element={<MigrationDetailView />} />
        <Route path="run" element={<MigrationRunnerView />} />
        <Route path="studio" element={<DatabaseStudioView />} />
        <Route path="validation" element={<ValidationEngineView />} />
        <Route path="*" element={<Navigate to="/migrations" replace />} />
      </Route>
    </Routes>
  );
}
