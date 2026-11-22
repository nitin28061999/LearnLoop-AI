import pytest  # pyright: ignore[reportMissingImports]

from app.learning.bkt import BKTParameters, update_mastery  # pyright: ignore[reportMissingImports]


def test_default_bkt_parameters():
    parameters = BKTParameters()

    assert parameters.p_initial == 0.2
    assert parameters.p_learn == 0.1
    assert parameters.p_guess == 0.2
    assert parameters.p_slip == 0.1


def test_correct_answer_increases_mastery():
    parameters = BKTParameters()

    updated_mastery = update_mastery(
        prior_mastery=0.2,
        is_correct=True,
        parameters=parameters,
    )

    assert updated_mastery == pytest.approx(0.5764705882)


def test_incorrect_answer_decreases_mastery():
    parameters = BKTParameters()

    updated_mastery = update_mastery(
        prior_mastery=0.2,
        is_correct=False,
        parameters=parameters,
    )

    assert updated_mastery == pytest.approx(0.1272727273)


@pytest.mark.parametrize("invalid_mastery", [-0.1, 1.1])
def test_update_rejects_invalid_mastery(invalid_mastery):
    with pytest.raises(ValueError):
        update_mastery(
            prior_mastery=invalid_mastery,
            is_correct=True,
        )


def test_bkt_parameters_reject_invalid_probabilities():
    with pytest.raises(ValueError):
        BKTParameters(p_initial=1.5)


@pytest.mark.parametrize(
    "invalid_value",
    [float("nan"), float("inf"), float("-inf")],
)
def test_update_rejects_non_finite_mastery(invalid_value):
    with pytest.raises(ValueError):
        update_mastery(
            prior_mastery=invalid_value,
            is_correct=True,
        )


def test_update_rejects_non_boolean_answer():
    with pytest.raises(ValueError):
        update_mastery(
            prior_mastery=0.2,
            is_correct=1,  # pyright: ignore[reportArgumentType]
        )


def test_correct_answer_handles_zero_prior_mastery():
    updated_mastery = update_mastery(
        prior_mastery=0.0,
        is_correct=True,
    )

    assert updated_mastery == pytest.approx(0.1)


def test_incorrect_answer_handles_zero_prior_mastery():
    updated_mastery = update_mastery(
        prior_mastery=0.0,
        is_correct=False,
    )

    assert updated_mastery == pytest.approx(0.1)


def test_correct_answer_rejects_zero_evidence_probability():
    parameters = BKTParameters(p_slip=1.0)

    with pytest.raises(ValueError, match="zero evidence probability"):
        update_mastery(
            prior_mastery=1.0,
            is_correct=True,
            parameters=parameters,
        )


def test_incorrect_answer_rejects_zero_evidence_probability():
    parameters = BKTParameters(p_guess=1.0)

    with pytest.raises(ValueError, match="zero evidence probability"):
        update_mastery(
            prior_mastery=0.0,
            is_correct=False,
            parameters=parameters,
        )
