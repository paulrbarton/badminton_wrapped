-- Staging model for divisions data
-- Loads raw division/draw information

with source as (
    select * from read_csv_auto('/Users/c16305a/Documents/ECS/Sandpit/badminton-wrapped/data/raw/divisions.csv', header=true)
),

renamed as (
    select
        draw_id,
        division_name,
        url,
        current_timestamp as loaded_at
    from source
)

select * from renamed
