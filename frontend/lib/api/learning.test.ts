import { afterEach, describe, expect, it, vi } from "vitest";

import { getNextQuestion, submitAttempt } from "./learning";

describe("getNextQuestion", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("fetches the next question with the authenticated user's access token", async () => {
    const question = {
      question_id: "11111111-1111-4111-8111-111111111111",
      concept_id: "22222222-2222-4222-8222-222222222222",
      question_text: "Explain the difference between a list and a tuple.",
      difficulty: 2,
    };

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(question), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000");

    await expect(getNextQuestion("test-access-token")).resolves.toEqual(
      question,
    );

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/learning/next-question",
      {
        method: "GET",
        headers: {
          Authorization: "Bearer test-access-token",
        },
        cache: "no-store",
      },
    );
  });

  it("rejects requests when the access token is missing", async () => {
    await expect(getNextQuestion("")).rejects.toThrow(
      "An access token is required.",
    );
  });

  it("throws an error when the backend request fails", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, { status: 401 }),
    );

    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000");

    await expect(getNextQuestion("invalid-token")).rejects.toThrow(
      "Failed to fetch the next question (401).",
    );
  });

  it("throws an error when the API base URL is not configured", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");

    await expect(getNextQuestion("test-access-token")).rejects.toThrow(
      "NEXT_PUBLIC_API_BASE_URL is not configured.",
    );
  });
});

describe("submitAttempt", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("submits the answer and reasoning and returns the backend evaluation", async () => {
    const request = {
      question_id: "11111111-1111-4111-8111-111111111111",
      student_answer: "A list is mutable, while a tuple is immutable.",
      reasoning: "Lists support item assignment; tuples do not.",
    };

    const evaluation = {
      concept_id: "22222222-2222-4222-8222-222222222222",
      mastery_before: 0.4,
      mastery_after: 0.68,
      is_correct: true,
      feedback: "Correct. You identified the key difference.",
      misconceptions: [],
    };

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(evaluation), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000");

    await expect(
      submitAttempt("test-access-token", request),
    ).resolves.toEqual(evaluation);

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/learning/attempts",
      {
        method: "POST",
        headers: {
          Authorization: "Bearer test-access-token",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
        cache: "no-store",
      },
    );
  });

  it("rejects submissions when the access token is missing", async () => {
    await expect(
      submitAttempt("", {
        question_id: "11111111-1111-4111-8111-111111111111",
        student_answer: "Answer",
        reasoning: "Reasoning",
      }),
    ).rejects.toThrow("An access token is required.");
  });

  it("throws an error when the backend rejects the submission", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, { status: 503 }),
    );

    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://127.0.0.1:8000");

    await expect(
      submitAttempt("test-access-token", {
        question_id: "11111111-1111-4111-8111-111111111111",
        student_answer: "Answer",
        reasoning: "Reasoning",
      }),
    ).rejects.toThrow(
      "Failed to submit the learning attempt (503).",
    );
  });
});
