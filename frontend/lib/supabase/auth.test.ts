import { afterEach, describe, expect, it, vi } from "vitest";

import { signIn, signUp, signOut } from "./auth";
import { createClient } from "./client";

vi.mock("./client", () => ({
  createClient: vi.fn(),
}));

describe("Supabase authentication", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("signs in with email and password", async () => {
    const signInWithPassword = vi.fn().mockResolvedValue({
      data: {
        user: { id: "user-123" },
        session: { access_token: "token" },
      },
      error: null,
    });

    vi.mocked(createClient).mockReturnValue({
      auth: { signInWithPassword },
    } as never);

    await expect(
      signIn("student@example.com", "secure-password"),
    ).resolves.toMatchObject({
      user: { id: "user-123" },
      session: { access_token: "token" },
    });

    expect(signInWithPassword).toHaveBeenCalledWith({
      email: "student@example.com",
      password: "secure-password",
    });
  });

  it("registers a new user with a trimmed email address", async () => {
    const signUpMock = vi.fn().mockResolvedValue({
      data: {
        user: { id: "new-user-123" },
        session: null,
      },
      error: null,
    });

    vi.mocked(createClient).mockReturnValue({
      auth: { signUp: signUpMock },
    } as never);

    await expect(
      signUp(" student@example.com ", "secure-password"),
    ).resolves.toMatchObject({
      user: { id: "new-user-123" },
      session: null,
    });

    expect(signUpMock).toHaveBeenCalledWith({
      email: "student@example.com",
      password: "secure-password",
    });
  });

  it("signs out the current user", async () => {
    const signOutMock = vi.fn().mockResolvedValue({
      error: null,
    });

    vi.mocked(createClient).mockReturnValue({
      auth: { signOut: signOutMock },
    } as never);

    await expect(signOut()).resolves.toBeUndefined();

    expect(signOutMock).toHaveBeenCalledOnce();
  });

  it("propagates Supabase sign-in errors", async () => {
    const authError = new Error("Invalid login credentials");

    const signInWithPassword = vi.fn().mockResolvedValue({
      data: { user: null, session: null },
      error: authError,
    });

    vi.mocked(createClient).mockReturnValue({
      auth: { signInWithPassword },
    } as never);

    await expect(
      signIn("student@example.com", "wrong-password"),
    ).rejects.toThrow("Invalid login credentials");
  });
});
