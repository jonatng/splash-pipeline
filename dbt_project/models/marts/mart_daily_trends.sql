{{
  config(
    materialized='table',
    description='Daily trends mart with aggregated photo metrics by day'
  )
}}

with daily_stats as (
    select
        created_at::date as trend_date,
        
        -- Basic counts
        count(distinct id) as total_photos,
        sum(likes) as total_likes,
        sum(downloads) as total_downloads,
        sum(views) as total_views,
        
        -- Averages
        round(avg(likes), 2) as avg_likes_per_photo,
        round(avg(downloads), 2) as avg_downloads_per_photo,
        round(avg(views), 2) as avg_views_per_photo,
        
        -- Engagement metrics
        round(avg(like_rate), 2) as avg_like_rate,
        round(avg(download_rate), 2) as avg_download_rate,
        
        -- Content characteristics
        count(distinct user_id) as unique_photographers,
        round(avg(aspect_ratio), 2) as avg_aspect_ratio,
        
        -- Orientation breakdown
        count(case when orientation = 'landscape' then 1 end) as landscape_photos,
        count(case when orientation = 'portrait' then 1 end) as portrait_photos,
        count(case when orientation = 'square' then 1 end) as square_photos,
        
        current_timestamp as created_at
        
    from {{ ref('stg_photos') }}
    group by created_at::date
),

daily_tags as (
    select
        created_at::date as trend_date,
        jsonb_agg(
            jsonb_build_object(
                'tag', tag_name,
                'count', tag_count
            ) order by tag_count desc
        ) filter (where rn <= 10) as top_tags
    from (
        select
            created_at::date,
            jsonb_array_elements_text(tags) as tag_name,
            count(*) as tag_count,
            row_number() over (partition by created_at::date order by count(*) desc) as rn
        from {{ ref('stg_photos') }}
        where tags is not null
        group by created_at::date, jsonb_array_elements_text(tags)
    ) ranked_tags
    group by created_at::date
),

daily_colors as (
    select
        created_at::date as trend_date,
        jsonb_agg(
            jsonb_build_object(
                'color', color,
                'count', color_count
            ) order by color_count desc
        ) filter (where rn <= 10) as top_colors
    from (
        select
            created_at::date,
            color,
            count(*) as color_count,
            row_number() over (partition by created_at::date order by count(*) desc) as rn
        from {{ ref('stg_photos') }}
        where color is not null
        group by created_at::date, color
    ) ranked_colors
    group by created_at::date
)

select
    ds.*,
    dt.top_tags,
    dc.top_colors
from daily_stats ds
left join daily_tags dt on ds.trend_date = dt.trend_date
left join daily_colors dc on ds.trend_date = dc.trend_date
order by ds.trend_date desc 