-- Staging model for matches data
-- Loads match-level information including teams and scores

with source as (
    select * from read_csv_auto('/Users/c16305a/Documents/ECS/Sandpit/badminton-wrapped/data/raw/{{ var("season") }}/matches.csv', header=true)
),

renamed as (
    select
        match_id,
        draw_id,
        division_name,
        match_date,
        home_team,
        away_team,
        score,
        url,
        '{{ var("season") }}' as season,
        current_timestamp as loaded_at
    from source
)

select * from renamed
