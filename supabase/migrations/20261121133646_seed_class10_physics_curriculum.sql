
-- ============================================================
-- LearnLoop AI
-- Migration: Seed CBSE Class 10 Physics curriculum (2026-27)
-- ============================================================

DO $$
DECLARE
    v_subject_id uuid;
BEGIN

    -- --------------------------------------------------------
    -- 1. SUBJECT
    -- --------------------------------------------------------

    INSERT INTO public.subjects (
        code,
        name,
        grade,
        board,
        description
    )
    VALUES (
        'CBSE-CLASS10-PHYSICS',
        'Physics',
        10,
        'CBSE',
        'CBSE Class 10 Physics curriculum aligned with the 2026-27 Science syllabus and NCERT textbook.'
    )
    ON CONFLICT (code)
    DO UPDATE SET
        name = EXCLUDED.name,
        grade = EXCLUDED.grade,
        board = EXCLUDED.board,
        description = EXCLUDED.description
    RETURNING id INTO v_subject_id;


    -- --------------------------------------------------------
    -- 2. CONCEPTS
    -- difficulty: 1 = introductory, 5 = advanced
    -- sequence_order follows the chapter learning sequence.
    -- --------------------------------------------------------

    INSERT INTO public.concepts (
        subject_id,
        code,
        title,
        description,
        chapter,
        sequence_order,
        difficulty
    )
    SELECT
        v_subject_id,
        c.code,
        c.title,
        c.description,
        c.chapter,
        c.sequence_order,
        c.difficulty
    FROM (
        VALUES

        -- CHAPTER 1: LIGHT - REFLECTION AND REFRACTION

        ('light_ray_basics',
         'Light Rays and Beam of Light',
         'Understand light rays, beams and the rectilinear propagation model.',
         'Light - Reflection and Refraction', 1, 1),

        ('laws_of_reflection',
         'Laws of Reflection',
         'Understand the laws of reflection and the relationship between angles of incidence and reflection.',
         'Light - Reflection and Refraction', 2, 1),

        ('spherical_mirrors',
         'Spherical Mirrors',
         'Understand concave and convex mirrors and their image-forming behaviour.',
         'Light - Reflection and Refraction', 3, 2),

        ('mirror_terminology',
         'Terminology of Spherical Mirrors',
         'Identify pole, centre of curvature, principal axis, principal focus and focal length.',
         'Light - Reflection and Refraction', 4, 2),

        ('mirror_sign_convention',
         'Mirror Sign Convention',
         'Apply the Cartesian sign convention to distances and heights in spherical mirrors.',
         'Light - Reflection and Refraction', 5, 3),

        ('mirror_formula',
         'Mirror Formula',
         'Apply the mirror formula to calculate object distance, image distance and focal length.',
         'Light - Reflection and Refraction', 6, 4),

        ('mirror_magnification',
         'Magnification by Spherical Mirrors',
         'Calculate magnification and interpret image size and orientation.',
         'Light - Reflection and Refraction', 7, 3),

        ('refraction_basics',
         'Refraction of Light',
         'Understand the bending of light when it passes between different transparent media.',
         'Light - Reflection and Refraction', 8, 2),

        ('laws_of_refraction',
         'Laws of Refraction',
         'Understand the laws governing refraction and the relationship between incident and refracted rays.',
         'Light - Reflection and Refraction', 9, 3),

        ('refractive_index',
         'Refractive Index',
         'Understand and calculate the refractive index of a medium.',
         'Light - Reflection and Refraction', 10, 3),

        ('glass_slab_refraction',
         'Refraction Through a Glass Slab',
         'Trace light through a rectangular glass slab and understand lateral displacement.',
         'Light - Reflection and Refraction', 11, 3),

        ('spherical_lenses',
         'Spherical Lenses',
         'Understand convex and concave lenses and image formation by spherical lenses.',
         'Light - Reflection and Refraction', 12, 2),

        ('lens_sign_convention',
         'Lens Sign Convention',
         'Apply the Cartesian sign convention to spherical lenses.',
         'Light - Reflection and Refraction', 13, 3),

        ('lens_formula',
         'Lens Formula',
         'Apply the lens formula to calculate object distance, image distance and focal length.',
         'Light - Reflection and Refraction', 14, 4),

        ('lens_magnification',
         'Magnification by Spherical Lenses',
         'Calculate lens magnification and interpret image characteristics.',
         'Light - Reflection and Refraction', 15, 3),

        ('power_of_lens',
         'Power of a Lens',
         'Calculate lens power using focal length and understand its unit, the dioptre.',
         'Light - Reflection and Refraction', 16, 3),


        -- CHAPTER 2: HUMAN EYE AND COLOURFUL WORLD

        ('human_eye_lens_function',
         'Functioning of the Human Eye',
         'Understand how the eye lens forms an image on the retina.',
         'Human Eye and Colourful World', 17, 2),

        ('accommodation_of_eye',
         'Power of Accommodation',
         'Understand how the eye changes its focal length to see objects at different distances.',
         'Human Eye and Colourful World', 18, 3),

        ('defects_of_vision',
         'Defects of Vision',
         'Understand common vision defects and why clear image formation is affected.',
         'Human Eye and Colourful World', 19, 3),

        ('myopia_and_correction',
         'Myopia and Its Correction',
         'Understand short-sightedness and its correction using a suitable concave lens.',
         'Human Eye and Colourful World', 20, 3),

        ('hypermetropia_and_correction',
         'Hypermetropia and Its Correction',
         'Understand long-sightedness and its correction using a suitable convex lens.',
         'Human Eye and Colourful World', 21, 3),

        ('presbyopia',
         'Presbyopia',
         'Understand age-related changes in accommodation and the use of corrective lenses.',
         'Human Eye and Colourful World', 22, 2),

        ('prism_refraction',
         'Refraction Through a Glass Prism',
         'Understand the path of light through a prism and the deviation of light.',
         'Human Eye and Colourful World', 23, 3),

        ('dispersion_of_light',
         'Dispersion of Light',
         'Understand the splitting of white light into its constituent colours.',
         'Human Eye and Colourful World', 24, 2),

        ('scattering_of_light',
         'Scattering of Light',
         'Understand scattering of light and its applications. The colour of the Sun at sunrise and sunset is excluded from summative assessment.',
         'Human Eye and Colourful World', 25, 3),

        ('atmospheric_refraction',
         'Atmospheric Refraction',
         'Explore atmospheric refraction as an NCERT supporting concept.',
         'Human Eye and Colourful World', 26, 3),


        -- CHAPTER 3: ELECTRICITY

        ('electric_charge',
         'Electric Charge',
         'Understand electric charge as the basis for electric current.',
         'Electricity', 27, 1),

        ('electric_current',
         'Electric Current',
         'Understand electric current as the rate of flow of electric charge and its SI unit.',
         'Electricity', 28, 2),

        ('potential_difference',
         'Potential Difference',
         'Understand potential difference, its role in driving current and its measurement.',
         'Electricity', 29, 2),

        ('electric_circuit',
         'Electric Circuits',
         'Identify circuit components and understand conventional circuit diagrams.',
         'Electricity', 30, 2),

        ('ohms_law',
         'Ohm''s Law',
         'Understand the relationship between current and potential difference for an ohmic conductor.',
         'Electricity', 31, 3),

        ('resistance_and_resistivity',
         'Resistance and Resistivity',
         'Understand resistance, resistivity and the factors affecting the resistance of a conductor.',
         'Electricity', 32, 3),

        ('series_combination',
         'Series Combination of Resistors',
         'Calculate equivalent resistance and understand current and voltage distribution in series circuits.',
         'Electricity', 33, 3),

        ('parallel_combination',
         'Parallel Combination of Resistors',
         'Calculate equivalent resistance and understand current and voltage distribution in parallel circuits.',
         'Electricity', 34, 3),

        ('heating_effect',
         'Heating Effect of Electric Current',
         'Understand Joule heating and its applications in everyday electrical devices.',
         'Electricity', 35, 3),

        ('electric_power',
         'Electric Power',
         'Understand electrical power, energy consumption and commercial units of electrical energy.',
         'Electricity', 36, 3),

        ('power_relations',
         'Relationships Between Power, Voltage and Current',
         'Apply relationships between P, V, I and R to solve numerical problems.',
         'Electricity', 37, 4),


        -- CHAPTER 4: MAGNETIC EFFECTS OF ELECTRIC CURRENT

        ('magnetic_field',
         'Magnetic Field',
         'Understand magnetic fields and the region in which magnetic force can be experienced.',
         'Magnetic Effects of Electric Current', 38, 2),

        ('magnetic_field_lines',
         'Magnetic Field Lines',
         'Interpret magnetic field lines and their direction and relative strength.',
         'Magnetic Effects of Electric Current', 39, 2),

        ('field_around_conductor',
         'Magnetic Field Around a Current-Carrying Conductor',
         'Understand the magnetic field produced by a straight current-carrying conductor.',
         'Magnetic Effects of Electric Current', 40, 3),

        ('right_hand_thumb_rule',
         'Right-Hand Thumb Rule',
         'Determine the direction of the magnetic field around a current-carrying conductor.',
         'Magnetic Effects of Electric Current', 41, 3),

        ('field_around_coil_solenoid',
         'Magnetic Field Around a Coil and Solenoid',
         'Understand magnetic fields produced by current-carrying circular coils and solenoids.',
         'Magnetic Effects of Electric Current', 42, 3),

        ('force_on_current_conductor',
         'Force on a Current-Carrying Conductor',
         'Understand the force experienced by a current-carrying conductor in a magnetic field.',
         'Magnetic Effects of Electric Current', 43, 3),

        ('flemings_left_hand_rule',
         'Fleming''s Left-Hand Rule',
         'Determine the direction of force on a current-carrying conductor in a magnetic field.',
         'Magnetic Effects of Electric Current', 44, 3),

        ('direct_current',
         'Direct Current',
         'Understand direct current and its direction of flow.',
         'Magnetic Effects of Electric Current', 45, 2),

        ('alternating_current',
         'Alternating Current',
         'Understand alternating current and how its direction changes periodically.',
         'Magnetic Effects of Electric Current', 46, 3),

        ('frequency_of_ac',
         'Frequency of Alternating Current',
         'Understand the frequency of AC and its relationship with periodic changes in current.',
         'Magnetic Effects of Electric Current', 47, 3),

        ('advantages_of_ac',
         'Advantages of AC Over DC',
         'Compare alternating and direct current and understand practical advantages of AC.',
         'Magnetic Effects of Electric Current', 48, 3),

        ('domestic_electric_circuits',
         'Domestic Electric Circuits',
         'Understand domestic wiring, live and neutral wires, earthing, fuses and electrical safety.',
         'Magnetic Effects of Electric Current', 49, 3),

        ('electric_motor',
         'Electric Motor',
         'Understand the principle and working of an electric motor, including the role of magnetic force.',
         'Magnetic Effects of Electric Current', 50, 4),

        ('electromagnetic_induction',
         'Electromagnetic Induction',
         'Understand electromagnetic induction and how changing magnetic fields produce induced current.',
         'Magnetic Effects of Electric Current', 51, 4),

        ('electric_generator',
         'Electric Generator',
         'Understand the principle and working of an electric generator and the conversion of mechanical energy into electrical energy.',
         'Magnetic Effects of Electric Current', 52, 4)

    ) AS c(
        code,
        title,
        description,
        chapter,
        sequence_order,
        difficulty
    )
    ON CONFLICT (subject_id, code)
    DO UPDATE SET
        title = EXCLUDED.title,
        description = EXCLUDED.description,
        chapter = EXCLUDED.chapter,
        sequence_order = EXCLUDED.sequence_order,
        difficulty = EXCLUDED.difficulty;


    -- --------------------------------------------------------
    -- 3. CONCEPT PREREQUISITES
    -- Each row means: concept_code depends on prerequisite_code.
    -- --------------------------------------------------------

    INSERT INTO public.concept_prerequisites (
        subject_id,
        concept_id,
        prerequisite_concept_id
    )
    SELECT
        v_subject_id,
        child.id,
        prerequisite.id
    FROM (
        VALUES

        -- LIGHT
        ('laws_of_reflection', 'light_ray_basics'),
        ('spherical_mirrors', 'laws_of_reflection'),
        ('mirror_terminology', 'spherical_mirrors'),
        ('mirror_sign_convention', 'mirror_terminology'),
        ('mirror_formula', 'mirror_sign_convention'),
        ('mirror_magnification', 'mirror_formula'),

        ('refraction_basics', 'light_ray_basics'),
        ('laws_of_refraction', 'refraction_basics'),
        ('refractive_index', 'laws_of_refraction'),
        ('glass_slab_refraction', 'refractive_index'),

        ('spherical_lenses', 'refraction_basics'),
        ('lens_sign_convention', 'spherical_lenses'),
        ('lens_formula', 'lens_sign_convention'),
        ('lens_magnification', 'lens_formula'),
        ('power_of_lens', 'lens_formula'),

        -- HUMAN EYE
        ('human_eye_lens_function', 'spherical_lenses'),
        ('accommodation_of_eye', 'human_eye_lens_function'),
        ('defects_of_vision', 'accommodation_of_eye'),
        ('myopia_and_correction', 'defects_of_vision'),
        ('myopia_and_correction', 'lens_formula'),
        ('hypermetropia_and_correction', 'defects_of_vision'),
        ('hypermetropia_and_correction', 'lens_formula'),
        ('presbyopia', 'accommodation_of_eye'),

        ('prism_refraction', 'refraction_basics'),
        ('dispersion_of_light', 'prism_refraction'),
        ('scattering_of_light', 'light_ray_basics'),
        ('atmospheric_refraction', 'refraction_basics'),

        -- ELECTRICITY
        ('electric_current', 'electric_charge'),
        ('electric_circuit', 'electric_current'),
        ('electric_circuit', 'potential_difference'),
        ('ohms_law', 'electric_current'),
        ('ohms_law', 'potential_difference'),
        ('resistance_and_resistivity', 'ohms_law'),
        ('series_combination', 'resistance_and_resistivity'),
        ('parallel_combination', 'resistance_and_resistivity'),
        ('heating_effect', 'electric_current'),
        ('heating_effect', 'resistance_and_resistivity'),
        ('electric_power', 'potential_difference'),
        ('electric_power', 'electric_current'),
        ('power_relations', 'electric_power'),
        ('power_relations', 'ohms_law'),

        -- MAGNETIC EFFECTS
        ('magnetic_field_lines', 'magnetic_field'),
        ('field_around_conductor', 'magnetic_field'),
        ('field_around_conductor', 'electric_current'),
        ('right_hand_thumb_rule', 'field_around_conductor'),
        ('field_around_coil_solenoid', 'magnetic_field_lines'),
        ('field_around_coil_solenoid', 'electric_current'),
        ('force_on_current_conductor', 'magnetic_field_lines'),
        ('force_on_current_conductor', 'electric_current'),
        ('flemings_left_hand_rule', 'force_on_current_conductor'),
        ('alternating_current', 'direct_current'),
        ('frequency_of_ac', 'alternating_current'),
        ('advantages_of_ac', 'alternating_current'),
        ('advantages_of_ac', 'direct_current'),
        ('domestic_electric_circuits', 'alternating_current'),
        ('domestic_electric_circuits', 'electric_power'),

        -- ADDITIONAL MAGNETIC EFFECTS CONCEPTS
        ('electric_motor', 'force_on_current_conductor'),
        ('electric_motor', 'flemings_left_hand_rule'),
        ('electromagnetic_induction', 'magnetic_field_lines'),
        ('electromagnetic_induction', 'field_around_coil_solenoid'),
        ('electric_generator', 'electromagnetic_induction')

    ) AS e(child_code, prerequisite_code)

    JOIN public.concepts AS child
        ON child.subject_id = v_subject_id
        AND child.code = e.child_code

    JOIN public.concepts AS prerequisite
        ON prerequisite.subject_id = v_subject_id
        AND prerequisite.code = e.prerequisite_code

    ON CONFLICT (concept_id, prerequisite_concept_id)
    DO NOTHING;


    -- --------------------------------------------------------
    -- 4. VALIDATE THE DEPENDENCY GRAPH
    -- Reject the seed if any prerequisite cycle exists.
    -- --------------------------------------------------------

    IF EXISTS (
        WITH RECURSIVE dependency_walk (
            start_id,
            current_id,
            path,
            cycle_found
        ) AS (
            SELECT
                cp.concept_id,
                cp.prerequisite_concept_id,
                ARRAY[
                    cp.concept_id,
                    cp.prerequisite_concept_id
                ],
                cp.concept_id = cp.prerequisite_concept_id
            FROM public.concept_prerequisites AS cp
            WHERE cp.subject_id = v_subject_id

            UNION ALL

            SELECT
                dw.start_id,
                cp.prerequisite_concept_id,
                dw.path || cp.prerequisite_concept_id,
                cp.prerequisite_concept_id = ANY(dw.path)
            FROM dependency_walk AS dw
            JOIN public.concept_prerequisites AS cp
                ON cp.subject_id = v_subject_id
                AND cp.concept_id = dw.current_id
            WHERE NOT dw.cycle_found
        )
        SELECT 1
        FROM dependency_walk
        WHERE cycle_found
    ) THEN
        RAISE EXCEPTION
            'Concept prerequisite graph contains a cycle for subject %',
            v_subject_id;
    END IF;

END;
$$;

-- ============================================================
-- END OF CURRICULUM SEED MIGRATION
-- ============================================================
