import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SchemaTree } from "@/components/shared/SchemaTree";
import * as introspectionApi from "@/api/introspection";
import * as mockProvider from "@/mock/mockProvider";

vi.mock("@/api/logger", () => ({
  logClientError: vi.fn(),
}));

vi.mock("@/api/introspection");
vi.mock("@/mock/mockProvider");

describe("SchemaTree", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(mockProvider.isMockDataEnabled).mockReturnValue(false);
  });

  it("prompts when no connection is selected", () => {
    render(<SchemaTree connectionRef="" isFileConnection={false} />);
    expect(screen.getByText(/Select a connection to browse schema metadata/i)).toBeInTheDocument();
  });

  it("loads and lists S3 files", async () => {
    vi.mocked(introspectionApi.listS3Files).mockResolvedValue([
      { name: "data.csv", key: "prefix/data.csv" },
    ]);

    render(<SchemaTree connectionRef="client_archival_s3" isFileConnection />);

    await waitFor(() => {
      expect(screen.getByText("data.csv")).toBeInTheDocument();
    });
    expect(introspectionApi.listS3Files).toHaveBeenCalledWith("client_archival_s3");
  });

  it("loads database schemas", async () => {
    vi.mocked(introspectionApi.listSchemas).mockResolvedValue([{ name: "crm_db" }]);

    render(<SchemaTree connectionRef="client_crm_mysql" isFileConnection={false} />);

    await waitFor(() => {
      expect(screen.getByText("crm_db")).toBeInTheDocument();
    });
  });

  it("shows a friendly error when schema load fails", async () => {
    vi.mocked(introspectionApi.listSchemas).mockRejectedValue(new Error("access denied"));

    render(<SchemaTree connectionRef="client_crm_mysql" isFileConnection={false} />);

    await waitFor(() => {
      expect(screen.getByText(/Unable to read schema metadata/i)).toBeInTheDocument();
    });
  });

  it("falls back to mock catalog when mock data is enabled", async () => {
    vi.mocked(mockProvider.isMockDataEnabled).mockReturnValue(true);
    vi.mocked(introspectionApi.listSchemas).mockRejectedValue(new Error("network"));

    render(<SchemaTree connectionRef="client_crm_mysql" isFileConnection={false} />);

    await waitFor(() => {
      expect(screen.getByText("crm_db")).toBeInTheDocument();
    });
  });

  it("calls onSelectFile when an S3 file row is clicked", async () => {
    const onSelectFile = vi.fn();
    vi.mocked(introspectionApi.listS3Files).mockResolvedValue([
      { name: "geo_address_mapping.csv", key: "path/geo_address_mapping.csv" },
    ]);

    render(
      <SchemaTree
        connectionRef="client_archival_s3"
        isFileConnection
        onSelectFile={onSelectFile}
      />,
    );

    const user = userEvent.setup();
    await waitFor(() => {
      expect(screen.getByText("geo_address_mapping.csv")).toBeInTheDocument();
    });
    await user.click(screen.getByText("geo_address_mapping.csv"));
    expect(onSelectFile).toHaveBeenCalledWith("geo_address_mapping.csv");
  });
});
