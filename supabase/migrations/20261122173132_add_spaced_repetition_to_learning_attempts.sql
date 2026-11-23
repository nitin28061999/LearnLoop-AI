-- ============================================================
-- LearnLoop AI: Persist spaced-repetition scheduling atomically
-- ============================================================

-- 1. Add scheduling state to each student's concept mastery row.
ALTER TABLE public.student_concept_mastery
    ADD COLUMN repetition_count integer NOT NULL DEFAULT 0
        CHECK (repetition_count >= 0),
    ADD COLUMN review_interval_days integer NOT NULL DEFAULT 0
        CHECK (review_interval_days >= 0),
    ADD COLUMN ease_factor numeric NOT NULL DEFAULT 2.5
        CHECK (
            ease_factor >= 1.3
            AND ease_factor::text NOT IN ('NaN', 'Infinity', '-Infinity')
        ),
    ADD COLUMN next_review_at timestamptz,
    ADD COLUMN last_reviewed_at timestamptz;

-- Support efficient retrieval of concepts due for review.
CREATE INDEX idx_student_concept_mastery_next_review
    ON public.student_concept_mastery (student_id, next_review_at)
    WHERE next_review_at IS NOT NULL;


-- 2. Remove the previous nine-parameter RPC signature.
DROP FUNCTION IF EXISTS public.record_learning_attempt(
    uuid, uuid, text, text, text, boolean, numeric, numeric, integer
);


-- 3. Replace it with the expanded atomic RPC.
CREATE FUNCTION public.record_learning_attempt(
    p_student_id uuid,
    p_concept_id uuid,
    p_question_text text,
    p_student_answer text,
    p_reasoning text,
    p_is_correct boolean,
    p_mastery_before numeric,
    p_mastery_after numeric,
    p_expected_attempts_count integer,
    p_repetition_count integer,
    p_review_interval_days integer,
    p_ease_factor numeric,
    p_next_review_at timestamptz,
    p_last_reviewed_at timestamptz
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_current_attempts_count integer;
BEGIN
    -- Validate required learning-attempt inputs.
    IF p_student_id IS NULL
       OR p_concept_id IS NULL
       OR p_question_text IS NULL
       OR length(trim(p_question_text)) = 0
       OR p_student_answer IS NULL
       OR length(trim(p_student_answer)) = 0
       OR p_is_correct IS NULL
       OR p_mastery_before IS NULL
       OR p_mastery_before < 0
       OR p_mastery_before > 1
       OR p_mastery_after IS NULL
       OR p_mastery_after < 0
       OR p_mastery_after > 1
       OR p_expected_attempts_count IS NULL
       OR p_expected_attempts_count < 0
    THEN
        RAISE EXCEPTION 'Invalid learning attempt input.';
    END IF;

    -- Validate spaced-repetition state.
    IF p_repetition_count IS NULL
       OR p_repetition_count < 0
       OR p_review_interval_days IS NULL
       OR p_review_interval_days < 1
       OR p_ease_factor IS NULL
       OR p_ease_factor < 1.3
       OR p_ease_factor::text IN ('NaN', 'Infinity', '-Infinity')
       OR p_next_review_at IS NULL
       OR p_last_reviewed_at IS NULL
       OR p_next_review_at <= p_last_reviewed_at
    THEN
        RAISE EXCEPTION 'Invalid spaced-repetition input.';
    END IF;

    -- Create the initial mastery row if it does not exist.
    INSERT INTO public.student_concept_mastery (
        student_id,
        concept_id,
        mastery_probability,
        attempts_count,
        correct_count
    )
    VALUES (
        p_student_id,
        p_concept_id,
        p_mastery_before,
        0,
        0
    )
    ON CONFLICT (student_id, concept_id) DO NOTHING;

    -- Lock the mastery row before checking the expected count.
    SELECT attempts_count
    INTO v_current_attempts_count
    FROM public.student_concept_mastery
    WHERE student_id = p_student_id
      AND concept_id = p_concept_id
    FOR UPDATE;

    -- Reject stale calculations so concurrent requests cannot
    -- overwrite newer mastery or review-scheduling state.
    IF v_current_attempts_count <> p_expected_attempts_count THEN
        RETURN jsonb_build_object(
            'success', false,
            'reason', 'stale_attempt_count'
        );
    END IF;

    -- Append the answer history.
    INSERT INTO public.learning_attempts (
        student_id,
        concept_id,
        question_text,
        student_answer,
        reasoning,
        is_correct,
        mastery_before,
        mastery_after
    )
    VALUES (
        p_student_id,
        p_concept_id,
        p_question_text,
        p_student_answer,
        p_reasoning,
        p_is_correct,
        p_mastery_before,
        p_mastery_after
    );

    -- Persist mastery, counters, and review schedule together.
    UPDATE public.student_concept_mastery
    SET
        mastery_probability = p_mastery_after,
        attempts_count = attempts_count + 1,
        correct_count = correct_count
            + CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        last_attempt_at = now(),
        repetition_count = p_repetition_count,
        review_interval_days = p_review_interval_days,
        ease_factor = p_ease_factor,
        next_review_at = p_next_review_at,
        last_reviewed_at = p_last_reviewed_at
    WHERE student_id = p_student_id
      AND concept_id = p_concept_id;

    RETURN jsonb_build_object(
        'success', true,
        'reason', 'recorded'
    );
END;
$$;


-- 4. Restrict RPC execution to the trusted backend service role.
REVOKE ALL ON FUNCTION public.record_learning_attempt(
    uuid, uuid, text, text, text, boolean, numeric, numeric, integer,
    integer, integer, numeric, timestamptz, timestamptz
) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.record_learning_attempt(
    uuid, uuid, text, text, text, boolean, numeric, numeric, integer,
    integer, integer, numeric, timestamptz, timestamptz
) TO service_role;