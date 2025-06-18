{{
  config(
    materialized='table',
    description='Tag co-occurrence analysis mart showing which tags frequently appear together'
  )
}}

with photo_tag_pairs as (
    select 
        id as photo_id,
        created_at::date as photo_date,
        t1.tag as tag1,
        t2.tag as tag2,
        likes,
        downloads,
        views
    from {{ ref('stg_photos') }},
    lateral jsonb_array_elements_text(tags) as t1(tag),
    lateral jsonb_array_elements_text(tags) as t2(tag)
    where tags is not null
    and t1.tag < t2.tag  -- Avoid duplicates and self-pairs
),

tag_cooccurrence_stats as (
    select
        tag1,
        tag2,
        count(distinct photo_id) as cooccurrence_count,
        count(distinct photo_date) as days_appeared_together,
        sum(likes) as total_likes,
        sum(downloads) as total_downloads,
        sum(views) as total_views,
        round(avg(likes), 2) as avg_likes,
        round(avg(downloads), 2) as avg_downloads,
        round(avg(views), 2) as avg_views,
        
        -- Calculate tag pair strength
        round(
            count(distinct photo_id)::float / 
            (
                select count(distinct photo_id) 
                from photo_tag_pairs p2 
                where p2.tag1 = tag_cooccurrence_stats.tag1 or p2.tag2 = tag_cooccurrence_stats.tag1
            ) * 100, 
            2
        ) as tag1_cooccurrence_rate,
        
        min(photo_date) as first_cooccurrence_date,
        max(photo_date) as latest_cooccurrence_date,
        current_date as analysis_date
        
    from photo_tag_pairs
    group by tag1, tag2
),

ranked_cooccurrences as (
    select
        *,
        row_number() over (order by cooccurrence_count desc) as popularity_rank,
        row_number() over (order by avg_likes desc) as engagement_rank
    from tag_cooccurrence_stats
    where cooccurrence_count >= 2  -- Only include meaningful co-occurrences
)

select * from ranked_cooccurrences
order by cooccurrence_count desc 