-- Big Tech pipeline schema
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
	signal_type text not null,
	snippet text,
	source text not null default 'html',
	inserted_at timestamptz not null default now()
);

create table if not exists public.contacts (
	id bigserial primary key,
	name text not null,
	title text,
	email text,
	organization text,
	inserted_at timestamptz not null default now()
);

-- Helpful indexes
create index if not exists idx_bigtech_signals_url on public.bigtech_signals(url);
create index if not exists idx_contacts_email on public.contacts(lower(email));

-- VC Partnerships pipeline schema
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

-- UT Alumni pipeline schema
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
