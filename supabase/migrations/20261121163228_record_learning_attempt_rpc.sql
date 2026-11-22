-- ============================================================
-- LearnLoop AI: Atomic learning attempt persistence
-- ============================================================

CREATE OR REPLACE FUNCTION public.record_learning_attempt(
    p_student_id uuid,
    p_concept_id uuid,
    p_question_text text,
    p_student_answer text,
    p_reasoning text,
    p_is_correct boolean,
    p_mastery_before numeric,
    p_mastery_after numeric,
    p_expected_attempts_count integer
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE
    v_current_attempts_count integer;
BEGIN
    -- Validate required inputs.
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

    -- Create the initial mastery row if it does not exist.
    -- Concurrent first attempts are handled by the unique constraint.
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

    -- Another request may have recorded an answer after our read.
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

    -- Persist the newly calculated mastery and counters.
    UPDATE public.student_concept_mastery
    SET
        mastery_probability = p_mastery_after,
        attempts_count = attempts_count + 1,
        correct_count = correct_count
            + CASE WHEN p_is_correct THEN 1 ELSE 0 END,
        last_attempt_at = now()
    WHERE student_id = p_student_id
      AND concept_id = p_concept_id;

    RETURN jsonb_build_object(
        'success', true,
        'reason', 'recorded'
    );
END;
$$;

-- Restrict RPC execution to the trusted backend service role.
REVOKE ALL ON FUNCTION public.record_learning_attempt(
    uuid, uuid, text, text, text, boolean, numeric, numeric, integer
) FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.record_learning_attempt(
    uuid, uuid, text, text, text, boolean, numeric, numeric, integer
) TO service_role;