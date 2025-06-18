{{
  config(
    materialized='view',
    description='Intermediate model calculating tag performance metrics'
  )
}}

with photo_tags as (
    select 
        id as photo_id,
        likes,
        downloads,
        views,
        created_at,
        jsonb_array_elements_text(tags) as tag_name
    from {{ ref('stg_photos') }}
    where tags is not null
),

tag_metrics as (
    select
        tag_name,
        count(distinct photo_id) as photo_count,
        sum(likes) as total_likes,
        sum(downloads) as total_downloads,
        sum(views) as total_views,
        round(avg(likes), 2) as avg_likes,
        round(avg(downloads), 2) as avg_downloads,
        round(avg(views), 2) as avg_views,
        
        -- Performance metrics
        round(avg(case when views > 0 then likes::float / views * 100 else 0 end), 2) as avg_like_rate,
        round(avg(case when views > 0 then downloads::float / views * 100 else 0 end), 2) as avg_download_rate,
        
        -- Recent activity (last 30 days)
        count(distinct case when created_at >= current_date - interval '30 days' then photo_id end) as recent_photos_count,
        
        -- Time series data
        min(created_at) as first_photo_date,
        max(created_at) as latest_photo_date,
        
        current_date as analysis_date
        
    from photo_tags
    group by tag_name
)

select * from tag_metrics
where photo_count >= 2  -- Only include tags with at least 2 photos 