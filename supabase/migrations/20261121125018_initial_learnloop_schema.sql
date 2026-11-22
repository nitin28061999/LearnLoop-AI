
-- ============================================================
-- LearnLoop AI
-- Migration: Initial identity and curriculum schema
-- ============================================================

-- ------------------------------------------------------------
-- 1. PROFILES
-- One profile per Supabase Auth user.
-- New users are students by default.
-- Role changes must be performed by a trusted administrator.
-- ------------------------------------------------------------

create table public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,

    display_name text
        check (
            display_name is null
            or char_length(btrim(display_name)) between 1 and 80
        ),

    role text not null default 'student'
        check (role in ('student', 'teacher')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
    on public.profiles
    for select
    to authenticated
    using ((select auth.uid()) = id);

create policy "Users can create their own profile"
    on public.profiles
    for insert
    to authenticated
    with check ((select auth.uid()) = id);

create policy "Users can update their own profile"
    on public.profiles
    for update
    to authenticated
    using ((select auth.uid()) = id)
    with check ((select auth.uid()) = id);


-- ------------------------------------------------------------
-- 2. SUBJECTS
-- Stores curriculum subjects and syllabus metadata.
-- ------------------------------------------------------------

create table public.subjects (
    id uuid primary key default gen_random_uuid(),

    code text not null unique,
    name text not null,
    grade smallint not null
        check (grade between 1 and 12),

    board text not null default 'CBSE',
    description text,

    created_at timestamptz not null default now()
);

alter table public.subjects enable row level security;

create policy "Authenticated users can view subjects"
    on public.subjects
    for select
    to authenticated
    using (true);


-- ------------------------------------------------------------
-- 3. CONCEPTS
-- Individual learning concepts within a subject.
-- Supports concept graph visualization and BKT tracking.
-- ------------------------------------------------------------

create table public.concepts (
    id uuid primary key default gen_random_uuid(),

    subject_id uuid not null
        references public.subjects(id) on delete cascade,

    code text not null,
    title text not null,
    description text,

    chapter text not null,

    sequence_order integer not null default 0,

    difficulty smallint not null default 1
        check (difficulty between 1 and 5),

    created_at timestamptz not null default now(),

    constraint concepts_subject_code_unique
        unique (subject_id, code),

    -- Supports composite foreign keys in concept_prerequisites.
    constraint concepts_id_subject_unique
        unique (id, subject_id)
);

create index idx_concepts_subject_order
    on public.concepts(subject_id, sequence_order);

alter table public.concepts enable row level security;

create policy "Authenticated users can view concepts"
    on public.concepts
    for select
    to authenticated
    using (true);


-- ------------------------------------------------------------
-- 4. CONCEPT PREREQUISITES
-- Represents directed edges in the concept dependency graph.
-- concept_id depends on prerequisite_concept_id.
-- Both concepts must belong to the same subject.
-- ------------------------------------------------------------

create table public.concept_prerequisites (
    subject_id uuid not null,

    concept_id uuid not null,
    prerequisite_concept_id uuid not null,

    created_at timestamptz not null default now(),

    primary key (concept_id, prerequisite_concept_id),

    constraint no_self_prerequisite
        check (concept_id <> prerequisite_concept_id),

    constraint prerequisite_concept_fk
        foreign key (concept_id, subject_id)
        references public.concepts(id, subject_id)
        on delete cascade,

    constraint required_concept_fk
        foreign key (prerequisite_concept_id, subject_id)
        references public.concepts(id, subject_id)
        on delete cascade
);

create index idx_concept_prerequisites_required
    on public.concept_prerequisites(prerequisite_concept_id);

alter table public.concept_prerequisites enable row level security;

create policy "Authenticated users can view concept prerequisites"
    on public.concept_prerequisites
    for select
    to authenticated
    using (true);


-- ------------------------------------------------------------
-- 5. UPDATED_AT TRIGGER
-- Automatically updates profile timestamps.
-- ------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = pg_catalog.now();
    return new;
end;
$$;

revoke all on function public.set_updated_at()
    from public, anon, authenticated, service_role;

create trigger set_profiles_updated_at
    before update on public.profiles
    for each row
    execute function public.set_updated_at();


-- ------------------------------------------------------------
-- 6. EXPLICIT DATA API PRIVILEGES
-- No anonymous access.
-- Authenticated users get minimum required permissions.
-- Service role is reserved for trusted backend operations.
-- ------------------------------------------------------------

grant usage on schema public to authenticated, service_role;

-- Remove any automatic client-role table privileges.
revoke all on table
    public.profiles,
    public.subjects,
    public.concepts,
    public.concept_prerequisites
from anon, authenticated;

-- Profiles: users can read their own profile.
grant select on table public.profiles to authenticated;

-- Users can insert only their own ID and display name.
-- The role column retains its database default: student.
grant insert (id, display_name)
    on table public.profiles
    to authenticated;

-- Users can update only their display name.
grant update (display_name)
    on table public.profiles
    to authenticated;

-- Curriculum is readable by signed-in users.
grant select on table
    public.subjects,
    public.concepts,
    public.concept_prerequisites
to authenticated;

-- Trusted backend operations.
grant all privileges on table
    public.profiles,
    public.subjects,
    public.concepts,
    public.concept_prerequisites
to service_role;

-- ============================================================
-- END OF INITIAL MIGRATION
-- ============================================================
