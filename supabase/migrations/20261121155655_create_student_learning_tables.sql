
-- ============================================================
-- LearnLoop AI: Student learning persistence
-- ============================================================

-- 1. Current mastery state: one row per student and concept.
CREATE TABLE public.student_concept_mastery (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL
        REFERENCES public.profiles(id) ON DELETE CASCADE,
    concept_id uuid NOT NULL
        REFERENCES public.concepts(id) ON DELETE CASCADE,

    mastery_probability numeric(6,5) NOT NULL DEFAULT 0.2
        CHECK (mastery_probability BETWEEN 0 AND 1),

    attempts_count integer NOT NULL DEFAULT 0
        CHECK (attempts_count >= 0),

    correct_count integer NOT NULL DEFAULT 0
        CHECK (correct_count >= 0 AND correct_count <= attempts_count),

    last_attempt_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT uq_student_concept_mastery
        UNIQUE (student_id, concept_id)
);

-- 2. Append-only answer history.
CREATE TABLE public.learning_attempts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL
        REFERENCES public.profiles(id) ON DELETE CASCADE,
    concept_id uuid NOT NULL
        REFERENCES public.concepts(id) ON DELETE CASCADE,

    question_text text NOT NULL,
    student_answer text NOT NULL,
    reasoning text,

    is_correct boolean NOT NULL,

    mastery_before numeric(6,5) NOT NULL
        CHECK (mastery_before BETWEEN 0 AND 1),

    mastery_after numeric(6,5) NOT NULL
        CHECK (mastery_after BETWEEN 0 AND 1),

    created_at timestamptz NOT NULL DEFAULT now()
);

-- 3. Indexes for student dashboard and learning history.
CREATE INDEX idx_mastery_student
    ON public.student_concept_mastery(student_id);

CREATE INDEX idx_attempts_student_concept_created
    ON public.learning_attempts(student_id, concept_id, created_at DESC);

CREATE INDEX idx_attempts_student_created
    ON public.learning_attempts(student_id, created_at DESC);

-- 4. Keep mastery updated_at current.
CREATE TRIGGER set_mastery_updated_at
    BEFORE UPDATE ON public.student_concept_mastery
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- 5. Enable row-level security.
ALTER TABLE public.student_concept_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_attempts ENABLE ROW LEVEL SECURITY;

-- 6. Students can read only their own records.
CREATE POLICY "Students can read own mastery"
    ON public.student_concept_mastery
    FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = student_id);

CREATE POLICY "Students can read own attempts"
    ON public.learning_attempts
    FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = student_id);

-- 7. Explicit privileges: clients read; backend writes.
REVOKE ALL ON TABLE
    public.student_concept_mastery,
    public.learning_attempts
FROM anon, authenticated;

GRANT SELECT ON TABLE
    public.student_concept_mastery,
    public.learning_attempts
TO authenticated;

GRANT ALL ON TABLE
    public.student_concept_mastery,
    public.learning_attempts
TO service_role;
