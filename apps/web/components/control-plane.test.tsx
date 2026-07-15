import { render, screen } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ControlPlane } from "./control-plane";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => undefined)));
});

describe("Scope Guard control plane", () => {
  it("renders the non-chat overview and provider label", () => {
    render(<ControlPlane />);
    expect(screen.getByText("Fast agents.")).toBeInTheDocument();
    expect(screen.getByText("codex_demo")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run signature demo/i })).toBeEnabled();
  });

  it("renders guarded task manifest review controls", () => {
    render(<ControlPlane initialView="task" />);
    expect(screen.getByText("Declare the outcome. Approve the boundary.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /interpret with gpt-5.6/i })).toBeEnabled();
    expect(screen.getByText(/inject failed rd social health check/i)).toBeInTheDocument();
  });

  it("renders execution empty state", () => {
    render(<ControlPlane initialView="execution" />);
    expect(screen.getByText("No active execution")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /prepare demo task/i })).toBeEnabled();
  });
});
