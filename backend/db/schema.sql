-- Outbound Pipelines Database Schema (Supabase/Postgres)
-- Big Tech Paid Projects
create table if not exists public.bigtech_pages (
	id bigserial primary key,
	url text not null unique,
	source text not null default 'unknown',
	raw_html_len integer not null default 0,
	inserted_at timestamptz not null default now(),
	updated_at timestamptz not null default now()
);

create table if not exists public.bigtech_signals (
	id bigserial primary key,
	url text not null,
	signal_type text,
	snippet text,
	source text not null default 'html',
	found_items integer,
	inserted_at timestamptz not null default now()
);

create index if not exists idx_bigtech_signals_url on public.bigtech_signals(url);

-- VC-Backed Series A+ Partnerships
create table if not exists public.vc_portfolios (
	id bigserial primary key,
	portfolio_url text not null unique,
	raw_html_len integer not null default 0,
	inserted_at timestamptz not null default now()
);

create table if not exists public.portfolio_companies (
	id bigserial primary key,
	name text,
	domain text,
	description text,
	tags text[],
	investors text[],
	funding_stage text,
	inserted_at timestamptz not null default now()
);

create table if not exists public.partnership_signals (
	id bigserial primary key,
	company_domain text not null,
	url text not null,
	signal_type text not null,
	snippet text,
	inserted_at timestamptz not null default now()
);

create index if not exists idx_partnership_signals_company on public.partnership_signals(company_domain);

-- UT Austin Alumni / Donor Fundraising
create table if not exists public.ut_pages (
	id bigserial primary key,
	url text not null unique,
	raw_html_len integer not null default 0,
	inserted_at timestamptz not null default now()
);

create table if not exists public.ut_donor_signals (
	id bigserial primary key,
	url text not null,
	snippet text,
	tag text,
	inserted_at timestamptz not null default now()
);

-- Shared Contacts (optional)
create table if not exists public.contacts (
	id bigserial primary key,
	name text not null,
	title text,
	email text,
	organization text,
	inserted_at timestamptz not null default now()
);

create index if not exists idx_contacts_email on public.contacts(lower(email));
