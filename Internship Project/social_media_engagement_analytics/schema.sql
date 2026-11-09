-- Optional SQL Server schema for storing cleaned post-level data.
-- Import the CSV into a staging table first, then map columns into this table.
CREATE TABLE dbo.SocialMediaPosts (
    PostId            NVARCHAR(100) NOT NULL PRIMARY KEY,
    Platform          NVARCHAR(100) NULL,
    PostDate          DATETIME2 NULL,
    ContentType       NVARCHAR(100) NULL,
    Caption           NVARCHAR(MAX) NULL,
    Hashtags          NVARCHAR(MAX) NULL,
    Likes             BIGINT NOT NULL DEFAULT 0,
    Comments          BIGINT NOT NULL DEFAULT 0,
    Shares            BIGINT NOT NULL DEFAULT 0,
    Impressions       BIGINT NULL,
    Reach             BIGINT NULL,
    Views             BIGINT NULL,
    TotalEngagement   AS (Likes + Comments + Shares) PERSISTED
);
GO

-- Example summary query: average engagement by platform.
SELECT
    Platform,
    COUNT(*) AS PostCount,
    AVG(CAST(TotalEngagement AS FLOAT)) AS AvgEngagement,
    SUM(TotalEngagement) AS TotalEngagement,
    AVG(CASE WHEN Impressions > 0
             THEN 100.0 * TotalEngagement / Impressions
        END) AS AvgEngagementRatePct
FROM dbo.SocialMediaPosts
GROUP BY Platform
ORDER BY AvgEngagement DESC;
GO

-- Example summary query: content type comparison.
SELECT
    ContentType,
    COUNT(*) AS PostCount,
    AVG(CAST(TotalEngagement AS FLOAT)) AS AvgEngagement,
    AVG(CAST(Likes AS FLOAT)) AS AvgLikes,
    AVG(CAST(Comments AS FLOAT)) AS AvgComments,
    AVG(CAST(Shares AS FLOAT)) AS AvgShares
FROM dbo.SocialMediaPosts
GROUP BY ContentType
ORDER BY AvgEngagement DESC;
GO
