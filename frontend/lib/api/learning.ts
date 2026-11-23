export interface AdaptiveQuestion {
  question_id: string;
  concept_id: string;
  question_text: string;
  difficulty: number;
}

export interface LearningAttemptRequest {
  question_id: string;
  student_answer: string;
  reasoning: string;
}

export interface MisconceptionFinding {
  code: string;
  evidence: string;
  explanation: string;
}

export interface LearningAttemptResponse {
  concept_id: string;
  mastery_before: number;
  mastery_after: number;
  is_correct: boolean;
  feedback: string;
  misconceptions: MisconceptionFinding[];
}

function getApiBaseUrl(): string {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  return apiBaseUrl.replace(/\/$/, "");
}

function validateAccessToken(accessToken: string): void {
  if (!accessToken.trim()) {
    throw new Error("An access token is required.");
  }
}

export async function getNextQuestion(
  accessToken: string,
): Promise<AdaptiveQuestion> {
  validateAccessToken(accessToken);

  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/learning/next-question`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch the next question (${response.status}).`,
    );
  }

  return (await response.json()) as AdaptiveQuestion;
}

export async function submitAttempt(
  accessToken: string,
  request: LearningAttemptRequest,
): Promise<LearningAttemptResponse> {
  validateAccessToken(accessToken);

  const response = await fetch(
    `${getApiBaseUrl()}/api/v1/learning/attempts`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `Failed to submit the learning attempt (${response.status}).`,
    );
  }

  return (await response.json()) as LearningAttemptResponse;
}
