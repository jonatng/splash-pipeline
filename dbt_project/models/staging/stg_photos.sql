{{
  config(
    materialized='view',
    description='Staging model for Unsplash photos with cleaned and standardized data'
  )
}}

with source_photos as (
    select * from {{ ref('photos') }}
),

cleaned_photos as (
    select
        id,
        created_at,
        updated_at,
        width,
        height,
        color,
        blur_hash,
        coalesce(downloads, 0) as downloads,
        coalesce(likes, 0) as likes,
        coalesce(views, 0) as views,
        description,
        alt_description,
        urls,
        links,
        user_id,
        user_name,
        user_username,
        location,
        exif,
        tags,
        categories,
        extracted_at,
        
        -- Calculated fields
        cast(width as float) / cast(height as float) as aspect_ratio,
        case 
            when width > height then 'landscape'
            when height > width then 'portrait' 
            else 'square'
        end as orientation,
        
        -- Engagement metrics
        case when views > 0 then cast(likes as float) / cast(views as float) * 100 else 0 end as like_rate,
        case when views > 0 then cast(downloads as float) / cast(views as float) * 100 else 0 end as download_rate,
        
        -- Photo age
        date_part('day', current_date - created_at::date) as days_since_created,
        
        -- Extract main tag if available
        case 
            when tags is not null and json_array_length(tags) > 0 
            then tags->>0 
            else null 
        end as primary_tag

    from source_photos
)

select * from cleaned_photos 