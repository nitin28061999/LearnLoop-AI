
-- ============================================================
-- LearnLoop AI: Trusted Question Bank
-- ============================================================

CREATE TABLE public.questions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id uuid NOT NULL REFERENCES public.concepts(id) ON DELETE RESTRICT,
    question_text text NOT NULL,
    question_type text NOT NULL DEFAULT 'short_answer'
        CHECK (question_type IN ('short_answer', 'multiple_choice', 'numerical')),
    difficulty smallint NOT NULL DEFAULT 1
        CHECK (difficulty BETWEEN 1 AND 5),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT questions_text_not_empty
        CHECK (length(trim(question_text)) > 0),

    CONSTRAINT questions_id_concept_unique
        UNIQUE (id, concept_id)
);

CREATE TABLE public.question_answer_keys (
    question_id uuid PRIMARY KEY,
    concept_id uuid NOT NULL,
    expected_answer text NOT NULL,
    acceptable_answers jsonb NOT NULL DEFAULT '[]'::jsonb,
    grading_rubric text NOT NULL,
    misconception_targets jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT answer_keys_expected_answer_not_empty
        CHECK (length(trim(expected_answer)) > 0),

    CONSTRAINT answer_keys_rubric_not_empty
        CHECK (length(trim(grading_rubric)) > 0),

    CONSTRAINT answer_keys_acceptable_answers_array
        CHECK (jsonb_typeof(acceptable_answers) = 'array'),

    CONSTRAINT answer_keys_misconceptions_array
        CHECK (jsonb_typeof(misconception_targets) = 'array'),

    CONSTRAINT answer_keys_question_concept_fk
        FOREIGN KEY (question_id, concept_id)
        REFERENCES public.questions(id, concept_id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_questions_concept_active
    ON public.questions (concept_id, difficulty)
    WHERE is_active = true;

-- Updated-at triggers
CREATE TRIGGER set_questions_updated_at
    BEFORE UPDATE ON public.questions
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_question_answer_keys_updated_at
    BEFORE UPDATE ON public.question_answer_keys
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS
ALTER TABLE public.questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_answer_keys ENABLE ROW LEVEL SECURITY;

-- Students and teachers can read active questions.
CREATE POLICY "Authenticated users can read active questions"
    ON public.questions
    FOR SELECT
    TO authenticated
    USING (is_active = true);

-- No authenticated or anonymous access to answer keys.
-- Backend service_role accesses these records.

-- Explicit privileges
REVOKE ALL ON TABLE public.questions
    FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE public.question_answer_keys
    FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE public.questions TO authenticated;

GRANT ALL ON TABLE public.questions TO service_role;
GRANT ALL ON TABLE public.question_answer_keys TO service_role;
