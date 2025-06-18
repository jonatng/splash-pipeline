{{
  config(
    materialized='view',
    description='Intermediate model calculating photographer performance metrics'
  )
}}

with photographer_stats as (
    select
        user_id,
        user_username,
        user_name,
        
        -- Basic counts
        count(distinct id) as total_photos,
        sum(likes) as total_likes,
        sum(downloads) as total_downloads,
        sum(views) as total_views,
        
        -- Averages
        round(avg(likes), 2) as avg_likes_per_photo,
        round(avg(downloads), 2) as avg_downloads_per_photo,
        round(avg(views), 2) as avg_views_per_photo,
        
        -- Performance metrics
        round(avg(like_rate), 2) as avg_like_rate,
        round(avg(download_rate), 2) as avg_download_rate,
        
        -- Photo characteristics
        round(avg(aspect_ratio), 2) as avg_aspect_ratio,
        mode() within group (order by orientation) as most_common_orientation,
        mode() within group (order by primary_tag) as most_common_tag,
        
        -- Activity metrics
        min(created_at) as first_photo_date,
        max(created_at) as latest_photo_date,
        count(distinct case when created_at >= current_date - interval '30 days' then id end) as recent_photos_count,
        
        -- Engagement scores (weighted metrics)
        round(
            (avg(likes) * 0.4 + avg(downloads) * 0.6) / 
            case when avg(views) > 0 then avg(views) else 1 end * 100, 
            2
        ) as engagement_score,
        
        current_date as analysis_date
        
    from {{ ref('stg_photos') }}
    where user_id is not null
    group by user_id, user_username, user_name
)

select * from photographer_stats
where total_photos >= 1  -- Include all photographers with at least 1 photo 