-- Caccer Motorsports: inventory for the website and Santi's panel
-- Public (website): can read only cars with status 'available' and their photos.
-- Admins (Santi, Cristian): signed-in users listed in public.admins can do everything.

create table if not exists public.admins (
  email text primary key,
  created_at timestamptz not null default now()
);

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.admins a where lower(a.email) = lower(auth.jwt() ->> 'email'));
$$;

create table if not exists public.cars (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9-]+$'),
  status text not null default 'draft' check (status in ('draft', 'available', 'sold')),
  vin text check (vin is null or length(vin) = 17),
  year int not null check (year between 1950 and 2100),
  make text not null,
  model text not null,
  trim text,
  body text not null default 'suv' check (body in ('truck', 'suv', 'sedan', 'coupe', 'van', 'other')),
  drive text check (drive in ('4x4', 'AWD', 'FWD', 'RWD')),
  price numeric(10, 2) not null check (price >= 0),
  miles int not null check (miles >= 0),
  color text,
  engine text,
  specs jsonb not null default '{"es": [], "en": []}',
  chips jsonb not null default '{"es": [], "en": []}',
  features jsonb not null default '{"es": [], "en": []}',
  hotspots jsonb not null default '{}',
  featured boolean not null default false,
  sort int not null default 0,
  sold_at timestamptz,
  sold_price numeric(10, 2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.car_photos (
  id uuid primary key default gen_random_uuid(),
  car_id uuid not null references public.cars(id) on delete cascade,
  path text not null,
  kind text not null default 'ext' check (kind in ('ext', 'motor', 'interior', 'asientos', 'carga', 'audio')),
  position int not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists car_photos_car_idx on public.car_photos (car_id, kind, position);
create index if not exists cars_status_idx on public.cars (status, sort);

create or replace function public.touch_updated_at() returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  if new.status = 'sold' and old.status is distinct from 'sold' and new.sold_at is null then new.sold_at := now(); end if;
  if new.status <> 'sold' then new.sold_at := null; end if;
  return new;
end $$;
drop trigger if exists cars_touch on public.cars;
create trigger cars_touch before update on public.cars for each row execute function public.touch_updated_at();

alter table public.admins enable row level security;
alter table public.cars enable row level security;
alter table public.car_photos enable row level security;

drop policy if exists "admins read self" on public.admins;
create policy "admins read self" on public.admins for select to authenticated using (public.is_admin());

drop policy if exists "public reads available cars" on public.cars;
create policy "public reads available cars" on public.cars for select to anon, authenticated
  using (status = 'available' or public.is_admin());
drop policy if exists "admins write cars" on public.cars;
create policy "admins write cars" on public.cars for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

drop policy if exists "public reads photos of available cars" on public.car_photos;
create policy "public reads photos of available cars" on public.car_photos for select to anon, authenticated
  using (public.is_admin() or exists (select 1 from public.cars c where c.id = car_id and c.status = 'available'));
drop policy if exists "admins write photos" on public.car_photos;
create policy "admins write photos" on public.car_photos for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- Photo storage: public to view, only admins upload or delete
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('cars', 'cars', true, 10485760, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;

drop policy if exists "admins upload car photos" on storage.objects;
create policy "admins upload car photos" on storage.objects for insert to authenticated
  with check (bucket_id = 'cars' and public.is_admin());
drop policy if exists "admins update car photos" on storage.objects;
create policy "admins update car photos" on storage.objects for update to authenticated
  using (bucket_id = 'cars' and public.is_admin());
drop policy if exists "admins delete car photos" on storage.objects;
create policy "admins delete car photos" on storage.objects for delete to authenticated
  using (bucket_id = 'cars' and public.is_admin());

insert into public.admins (email) values ('santi.caccer@gmail.com') on conflict do nothing;
