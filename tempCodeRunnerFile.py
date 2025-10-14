    for lab in LABS:
        lab_quoted = f'"{lab}"'
        response = supabase.table("participants").select("*", count="exact").eq(lab_quoted, "Yes").execute()
        lab_counts[lab] = response.count