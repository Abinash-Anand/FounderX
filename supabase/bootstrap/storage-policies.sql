do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'storage'
      and tablename = 'objects'
      and policyname = 'authenticated_pitch_deck_uploads'
  ) then
    create policy authenticated_pitch_deck_uploads
      on storage.objects
      for insert
      to authenticated
      with check (
        bucket_id = 'pitch-decks'
        and (storage.foldername(name))[1] = (select auth.uid())::text
      );
  end if;
end
$$;
