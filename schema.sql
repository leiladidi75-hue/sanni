create table if not exists technicians(
  id bigint generated always as identity primary key,
  name text not null check (char_length(name) between 2 and 60),
  phone text not null unique check (phone ~ '^[0-9]{8}$'),
  spec text not null check (char_length(spec) <= 30),
  city text not null check (char_length(city) <= 30),
  bio text check (char_length(bio) <= 300),
  approved boolean not null default false,
  code text,
  created_at timestamptz not null default now()
);
create table if not exists requests(
  id bigint generated always as identity primary key,
  client_name text not null check (char_length(client_name) between 2 and 60),
  phone text not null check (phone ~ '^[0-9]{8}$'),
  spec text not null check (char_length(spec) <= 30),
  city text not null check (char_length(city) <= 30),
  description text not null check (char_length(description) between 5 and 500),
  status text not null default 'open',
  created_at timestamptz not null default now()
);
alter table technicians enable row level security;
alter table requests enable row level security;

drop policy if exists "apply" on technicians;
create policy "apply" on technicians for insert to anon
  with check (approved = false and code is null);
drop policy if exists "post" on requests;
create policy "post" on requests for insert to anon
  with check (status = 'open');

create or replace view technicians_public as
  select id, name, spec, city, phone, bio, created_at
  from technicians where approved;
grant select on technicians_public to anon;

create or replace function list_requests(p_phone text, p_code text)
returns table(id bigint, client_name text, phone text, spec text, city text, description text, created_at timestamptz)
language plpgsql security definer set search_path = public as $$
begin
  if p_code is null or p_code = '' or not exists (
    select 1 from technicians t
    where t.phone = p_phone and t.code = p_code and t.approved
  ) then
    raise exception 'access denied';
  end if;
  return query
    select r.id, r.client_name, r.phone, r.spec, r.city, r.description, r.created_at
    from requests r
    where r.status = 'open' and r.created_at > now() - interval '14 days'
    order by r.created_at desc limit 100;
end $$;
grant execute on function list_requests(text, text) to anon;
