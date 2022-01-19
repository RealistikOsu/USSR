/*
The RealistikOsu Database Structure.
This is a Ripple based db schema around which USSR was designed.
Dump: 24/12/21
*/

CREATE TABLE `achievements` (
  `id` int(11) NOT NULL,
  `name` text CHARACTER SET latin1 NOT NULL,
  `description` text CHARACTER SET latin1 NOT NULL,
  `icon` text CHARACTER SET latin1 NOT NULL,
  `version` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `anticheat`
--

CREATE TABLE `anticheat` (
  `dcid` bigint(20) NOT NULL,
  `api` varchar(255) NOT NULL,
  `allowed` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `ap_stats`
--

CREATE TABLE `ap_stats` (
  `id` int(11) NOT NULL,
  `username` varchar(30) CHARACTER SET latin1 NOT NULL,
  `username_aka` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `user_color` varchar(16) CHARACTER SET latin1 NOT NULL DEFAULT 'black',
  `user_style` varchar(128) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `favourite_mode` int(11) NOT NULL DEFAULT '0',
  `level_std` int(11) NOT NULL DEFAULT '1',
  `level_taiko` int(11) NOT NULL DEFAULT '1',
  `level_mania` int(11) NOT NULL DEFAULT '1',
  `level_ctb` int(11) NOT NULL DEFAULT '1',
  `total_score_std` int(11) NOT NULL DEFAULT '0',
  `total_score_taiko` int(11) NOT NULL DEFAULT '0',
  `total_score_mania` int(11) NOT NULL DEFAULT '0',
  `total_score_ctb` int(11) NOT NULL DEFAULT '0',
  `total_hits_std` int(11) NOT NULL DEFAULT '0',
  `total_hits_taiko` int(11) NOT NULL DEFAULT '0',
  `total_hits_ctb` int(11) NOT NULL DEFAULT '0',
  `total_hits_mania` int(11) NOT NULL DEFAULT '0',
  `playtime_std` int(11) NOT NULL DEFAULT '0',
  `playtime_taiko` int(11) NOT NULL DEFAULT '0',
  `playtime_mania` int(11) NOT NULL DEFAULT '0',
  `playtime_ctb` int(11) NOT NULL DEFAULT '0',
  `ranked_score_std` bigint(11) NOT NULL DEFAULT '0',
  `ranked_score_taiko` int(11) NOT NULL DEFAULT '0',
  `ranked_score_mania` int(11) NOT NULL DEFAULT '0',
  `ranked_score_ctb` int(11) NOT NULL DEFAULT '0',
  `avg_accuracy_std` double NOT NULL DEFAULT '0',
  `avg_accuracy_taiko` double NOT NULL DEFAULT '0',
  `avg_accuracy_mania` double NOT NULL DEFAULT '0',
  `avg_accuracy_ctb` double NOT NULL DEFAULT '0',
  `playcount_std` int(11) NOT NULL DEFAULT '0',
  `playcount_taiko` int(11) NOT NULL DEFAULT '0',
  `playcount_mania` int(11) NOT NULL DEFAULT '0',
  `playcount_ctb` int(11) NOT NULL DEFAULT '0',
  `pp_std` int(11) NOT NULL DEFAULT '0',
  `pp_mania` int(11) NOT NULL DEFAULT '0',
  `pp_ctb` int(11) NOT NULL DEFAULT '0',
  `pp_taiko` int(11) NOT NULL DEFAULT '0',
  `country` char(2) NOT NULL DEFAULT 'XX',
  `unrestricted_pp` int(11) NOT NULL DEFAULT '0',
  `ppboard` int(11) NOT NULL DEFAULT '1',
  `replays_watched_std` int(11) NOT NULL DEFAULT '0',
  `replays_watched_taiko` int(11) NOT NULL DEFAULT '0',
  `replays_watched_ctb` int(11) NOT NULL DEFAULT '0',
  `replays_watched_mania` int(11) NOT NULL DEFAULT '0',
  `achievements` bigint(15) NOT NULL DEFAULT '0',
  `max_combo_std` int(12) NOT NULL DEFAULT '0',
  `max_combo_taiko` int(12) NOT NULL DEFAULT '0',
  `max_combo_ctb` int(12) NOT NULL DEFAULT '0',
  `max_combo_mania` int(12) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `badges`
--

CREATE TABLE `badges` (
  `id` int(11) NOT NULL,
  `name` varchar(21485) NOT NULL,
  `icon` varchar(32) CHARACTER SET latin1 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `bancho_channels`
--

CREATE TABLE `bancho_channels` (
  `id` int(11) NOT NULL,
  `name` varchar(32) NOT NULL,
  `description` varchar(127) NOT NULL,
  `public_read` tinyint(4) NOT NULL,
  `public_write` tinyint(4) NOT NULL,
  `status` tinyint(4) NOT NULL,
  `temp` tinyint(1) NOT NULL DEFAULT '0',
  `hidden` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `bancho_settings`
--

CREATE TABLE `bancho_settings` (
  `id` int(11) NOT NULL,
  `name` varchar(32) NOT NULL,
  `value_int` int(11) NOT NULL DEFAULT '0',
  `value_string` varchar(512) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `bancho_tokens`
--

CREATE TABLE `bancho_tokens` (
  `id` int(11) NOT NULL,
  `token` varchar(16) CHARACTER SET latin1 NOT NULL,
  `osu_id` int(11) NOT NULL,
  `latest_message_id` int(11) NOT NULL,
  `latest_private_message_id` int(11) NOT NULL,
  `latest_packet_time` int(11) NOT NULL,
  `latest_heavy_packet_time` int(11) NOT NULL,
  `joined_channels` varchar(512) CHARACTER SET latin1 NOT NULL,
  `game_mode` tinyint(4) NOT NULL,
  `action` int(11) NOT NULL,
  `action_text` varchar(128) CHARACTER SET latin1 NOT NULL,
  `kicked` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `beatmaps`
--

CREATE TABLE `beatmaps` (
  `id` int(11) NOT NULL,
  `beatmap_id` int(11) NOT NULL DEFAULT '0',
  `beatmapset_id` int(11) NOT NULL DEFAULT '0',
  `beatmap_md5` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `song_name` text CHARACTER SET latin1 NOT NULL,
  `ar` float NOT NULL DEFAULT '0',
  `od` float NOT NULL DEFAULT '0',
  `mode` int(11) NOT NULL DEFAULT '0',
  `rating` int(11) NOT NULL DEFAULT '10',
  `difficulty_std` float NOT NULL DEFAULT '0',
  `difficulty_taiko` float NOT NULL DEFAULT '0',
  `difficulty_ctb` float NOT NULL DEFAULT '0',
  `difficulty_mania` float NOT NULL DEFAULT '0',
  `max_combo` int(11) NOT NULL DEFAULT '0',
  `hit_length` int(11) NOT NULL DEFAULT '0',
  `bpm` int(11) NOT NULL DEFAULT '0',
  `playcount` int(11) NOT NULL DEFAULT '0',
  `passcount` int(11) NOT NULL DEFAULT '0',
  `ranked` tinyint(4) NOT NULL DEFAULT '0',
  `latest_update` int(11) NOT NULL DEFAULT '0',
  `ranked_status_freezed` tinyint(1) NOT NULL DEFAULT '0',
  `pp_100` int(11) NOT NULL DEFAULT '0',
  `pp_99` int(11) NOT NULL DEFAULT '0',
  `pp_98` int(11) NOT NULL DEFAULT '0',
  `pp_95` int(11) NOT NULL DEFAULT '0',
  `disable_pp` tinyint(4) NOT NULL DEFAULT '0',
  `file_name` longtext,
  `rankedby` varchar(16) NOT NULL DEFAULT 'IDK',
  `priv_crawler` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `beatmaps_rating`
--

CREATE TABLE `beatmaps_rating` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `beatmap_md5` varchar(32) NOT NULL,
  `rating` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `clans`
--

CREATE TABLE `clans` (
  `id` int(11) NOT NULL,
  `name` text NOT NULL,
  `description` text NOT NULL,
  `icon` text NOT NULL,
  `tag` varchar(6) NOT NULL,
  `mlimit` int(11) NOT NULL DEFAULT '16'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `clans_invites`
--

CREATE TABLE `clans_invites` (
  `id` int(11) NOT NULL,
  `clan` int(11) NOT NULL,
  `invite` varchar(8) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `client_err_logs`
--

CREATE TABLE `client_err_logs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `timestamp` int(12) NOT NULL,
  `traceback` varchar(1024) NOT NULL,
  `config` varchar(2048) NOT NULL,
  `osu_ver` varchar(12) NOT NULL,
  `osu_hash` char(32) NOT NULL,
  `identity_verified` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `comments`
--

CREATE TABLE `comments` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `beatmap_id` int(11) NOT NULL DEFAULT '0',
  `beatmapset_id` int(11) NOT NULL DEFAULT '0',
  `score_id` int(11) NOT NULL DEFAULT '0',
  `mode` int(11) NOT NULL,
  `comment` varchar(128) CHARACTER SET utf8 NOT NULL,
  `time` int(11) NOT NULL,
  `who` varchar(11) NOT NULL,
  `special_format` varchar(2556) CHARACTER SET utf8 DEFAULT 'FFFFFF'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `first_places`
--

CREATE TABLE `first_places` (
  `id` int(100) NOT NULL,
  `score_id` bigint(100) NOT NULL,
  `user_id` int(15) NOT NULL,
  `score` bigint(20) NOT NULL,
  `max_combo` int(11) NOT NULL,
  `full_combo` tinyint(1) NOT NULL,
  `mods` int(11) NOT NULL,
  `300_count` int(11) NOT NULL,
  `100_count` int(11) NOT NULL,
  `50_count` int(11) NOT NULL,
  `miss_count` int(11) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `mode` tinyint(4) NOT NULL,
  `completed` tinyint(2) NOT NULL,
  `accuracy` float(15,12) NOT NULL,
  `pp` double NOT NULL,
  `play_time` int(11) NOT NULL,
  `beatmap_md5` varchar(32) NOT NULL,
  `relax` tinyint(2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `hw_user`
--

CREATE TABLE `hw_user` (
  `id` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `mac` varchar(32) CHARACTER SET latin1 NOT NULL,
  `unique_id` varchar(32) CHARACTER SET latin1 NOT NULL,
  `disk_id` varchar(32) CHARACTER SET latin1 NOT NULL,
  `client_hash` varchar(32) NOT NULL DEFAULT '',
  `occurencies` int(11) NOT NULL DEFAULT '0',
  `activated` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `identity_tokens`
--

CREATE TABLE `identity_tokens` (
  `userid` int(11) NOT NULL,
  `token` varchar(64) CHARACTER SET latin1 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `ip_user`
--

CREATE TABLE `ip_user` (
  `userid` int(11) NOT NULL,
  `ip` text CHARACTER SET latin1 NOT NULL,
  `occurencies` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `lastfm_flags`
--

CREATE TABLE `lastfm_flags` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `timestamp` int(12) NOT NULL,
  `flag_enum` int(11) NOT NULL,
  `flag_text` varchar(512) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `main_menu_icons`
--

CREATE TABLE `main_menu_icons` (
  `id` int(11) NOT NULL,
  `is_current` int(11) NOT NULL,
  `file_id` varchar(128) NOT NULL,
  `name` varchar(256) NOT NULL,
  `url` text CHARACTER SET utf8 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `new_achievements`
--

CREATE TABLE `new_achievements` (
  `id` int(11) NOT NULL,
  `file` varchar(128) NOT NULL,
  `name` varchar(128) NOT NULL,
  `desc` varchar(128) NOT NULL,
  `cond` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `password_recovery`
--

CREATE TABLE `password_recovery` (
  `id` int(11) NOT NULL,
  `k` varchar(80) CHARACTER SET latin1 NOT NULL,
  `u` varchar(30) CHARACTER SET latin1 NOT NULL,
  `t` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `privileges_groups`
--

CREATE TABLE `privileges_groups` (
  `id` int(11) NOT NULL,
  `name` varchar(32) CHARACTER SET latin1 NOT NULL,
  `privileges` int(11) NOT NULL,
  `color` varchar(32) CHARACTER SET latin1 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `profile_backgrounds`
--

CREATE TABLE `profile_backgrounds` (
  `uid` int(11) NOT NULL,
  `time` int(11) NOT NULL,
  `type` int(11) NOT NULL,
  `value` text CHARACTER SET latin1 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `rank_requests`
--

CREATE TABLE `rank_requests` (
  `id` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `bid` int(11) NOT NULL,
  `type` varchar(8) CHARACTER SET latin1 NOT NULL,
  `time` int(11) NOT NULL,
  `blacklisted` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `rap_logs`
--

CREATE TABLE `rap_logs` (
  `id` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `text` text NOT NULL,
  `datetime` int(11) NOT NULL,
  `through` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `remember`
--

CREATE TABLE `remember` (
  `id` int(11) NOT NULL,
  `userid` int(11) NOT NULL,
  `series_identifier` int(11) DEFAULT NULL,
  `token_sha` varchar(255) CHARACTER SET latin1 DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `id` int(11) NOT NULL,
  `from_uid` int(11) NOT NULL,
  `to_uid` int(11) NOT NULL,
  `reason` text NOT NULL,
  `chatlog` text NOT NULL,
  `time` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `rx_beatmap_playcount`
--

CREATE TABLE `rx_beatmap_playcount` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `beatmap_id` int(11) DEFAULT NULL,
  `game_mode` int(11) DEFAULT NULL,
  `playcount` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `rx_stats`
--

CREATE TABLE `rx_stats` (
  `id` int(11) NOT NULL,
  `username` varchar(30) CHARACTER SET latin1 NOT NULL,
  `username_aka` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `user_color` varchar(16) CHARACTER SET latin1 NOT NULL DEFAULT 'black',
  `user_style` varchar(128) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `favourite_mode` int(11) NOT NULL DEFAULT '0',
  `level_std` int(11) NOT NULL DEFAULT '1',
  `level_taiko` int(11) NOT NULL DEFAULT '1',
  `level_mania` int(11) NOT NULL DEFAULT '1',
  `level_ctb` int(11) NOT NULL DEFAULT '1',
  `total_score_std` int(11) NOT NULL DEFAULT '0',
  `total_score_taiko` int(11) NOT NULL DEFAULT '0',
  `total_score_mania` int(11) NOT NULL DEFAULT '0',
  `total_score_ctb` int(11) NOT NULL DEFAULT '0',
  `total_hits_std` int(11) NOT NULL DEFAULT '0',
  `total_hits_taiko` int(11) NOT NULL DEFAULT '0',
  `total_hits_ctb` int(11) NOT NULL DEFAULT '0',
  `total_hits_mania` int(11) NOT NULL DEFAULT '0',
  `playtime_std` int(11) NOT NULL DEFAULT '0',
  `playtime_taiko` int(11) NOT NULL DEFAULT '0',
  `playtime_mania` int(11) NOT NULL DEFAULT '0',
  `playtime_ctb` int(11) NOT NULL DEFAULT '0',
  `ranked_score_std` bigint(11) NOT NULL DEFAULT '0',
  `ranked_score_taiko` int(11) NOT NULL DEFAULT '0',
  `ranked_score_mania` int(11) NOT NULL DEFAULT '0',
  `ranked_score_ctb` int(11) NOT NULL DEFAULT '0',
  `avg_accuracy_std` double NOT NULL DEFAULT '0',
  `avg_accuracy_taiko` double NOT NULL DEFAULT '0',
  `avg_accuracy_mania` double NOT NULL DEFAULT '0',
  `avg_accuracy_ctb` double NOT NULL DEFAULT '0',
  `playcount_std` int(11) NOT NULL DEFAULT '0',
  `playcount_taiko` int(11) NOT NULL DEFAULT '0',
  `playcount_mania` int(11) NOT NULL DEFAULT '0',
  `playcount_ctb` int(11) NOT NULL DEFAULT '0',
  `pp_std` int(11) NOT NULL DEFAULT '0',
  `pp_mania` int(11) NOT NULL DEFAULT '0',
  `pp_ctb` int(11) NOT NULL DEFAULT '0',
  `pp_taiko` int(11) NOT NULL DEFAULT '0',
  `country` char(2) NOT NULL DEFAULT 'XX',
  `unrestricted_pp` int(11) NOT NULL DEFAULT '0',
  `ppboard` int(11) NOT NULL DEFAULT '1',
  `replays_watched_std` int(11) NOT NULL DEFAULT '0',
  `replays_watched_taiko` int(11) NOT NULL DEFAULT '0',
  `replays_watched_ctb` int(11) NOT NULL DEFAULT '0',
  `replays_watched_mania` int(11) NOT NULL DEFAULT '0',
  `achievements` bigint(15) NOT NULL DEFAULT '0',
  `max_combo_std` int(12) DEFAULT '0',
  `max_combo_taiko` int(12) NOT NULL DEFAULT '0',
  `max_combo_ctb` int(12) NOT NULL DEFAULT '0',
  `max_combo_mania` int(12) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `scores`
--

CREATE TABLE `scores` (
  `id` int(11) NOT NULL,
  `beatmap_md5` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `userid` int(11) NOT NULL,
  `score` bigint(20) DEFAULT NULL,
  `max_combo` int(11) NOT NULL DEFAULT '0',
  `full_combo` tinyint(1) NOT NULL DEFAULT '0',
  `mods` int(11) NOT NULL DEFAULT '0',
  `300_count` int(11) NOT NULL DEFAULT '0',
  `100_count` int(11) NOT NULL DEFAULT '0',
  `50_count` int(11) NOT NULL DEFAULT '0',
  `katus_count` int(11) NOT NULL DEFAULT '0',
  `gekis_count` int(11) NOT NULL DEFAULT '0',
  `misses_count` int(11) NOT NULL DEFAULT '0',
  `time` varchar(18) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `play_mode` tinyint(4) NOT NULL DEFAULT '0',
  `completed` tinyint(11) NOT NULL DEFAULT '0',
  `accuracy` float(15,12) DEFAULT NULL,
  `pp` double DEFAULT '0',
  `playtime` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `scores_ap`
--

CREATE TABLE `scores_ap` (
  `id` int(11) NOT NULL,
  `beatmap_md5` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `userid` int(11) NOT NULL,
  `score` bigint(20) DEFAULT NULL,
  `max_combo` int(11) NOT NULL DEFAULT '0',
  `full_combo` tinyint(1) NOT NULL DEFAULT '0',
  `mods` int(11) NOT NULL DEFAULT '0',
  `300_count` int(11) NOT NULL DEFAULT '0',
  `100_count` int(11) NOT NULL DEFAULT '0',
  `50_count` int(11) NOT NULL DEFAULT '0',
  `katus_count` int(11) NOT NULL DEFAULT '0',
  `gekis_count` int(11) NOT NULL DEFAULT '0',
  `misses_count` int(11) NOT NULL DEFAULT '0',
  `time` varchar(18) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `play_mode` tinyint(4) NOT NULL DEFAULT '0',
  `completed` tinyint(11) NOT NULL DEFAULT '0',
  `accuracy` float(15,12) DEFAULT NULL,
  `pp` double DEFAULT '0',
  `playtime` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `scores_relax`
--

CREATE TABLE `scores_relax` (
  `id` int(11) NOT NULL,
  `beatmap_md5` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `userid` int(11) NOT NULL,
  `score` bigint(20) DEFAULT NULL,
  `max_combo` int(11) NOT NULL DEFAULT '0',
  `full_combo` tinyint(1) NOT NULL DEFAULT '0',
  `mods` int(11) NOT NULL DEFAULT '0',
  `300_count` int(11) NOT NULL DEFAULT '0',
  `100_count` int(11) NOT NULL DEFAULT '0',
  `50_count` int(11) NOT NULL DEFAULT '0',
  `katus_count` int(11) NOT NULL DEFAULT '0',
  `gekis_count` int(11) NOT NULL DEFAULT '0',
  `misses_count` int(11) NOT NULL DEFAULT '0',
  `time` varchar(18) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `play_mode` tinyint(4) NOT NULL DEFAULT '0',
  `completed` tinyint(11) NOT NULL DEFAULT '0',
  `accuracy` float(15,12) DEFAULT NULL,
  `pp` double DEFAULT '0',
  `playtime` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `system_settings`
--

CREATE TABLE `system_settings` (
  `id` int(11) NOT NULL,
  `name` varchar(32) CHARACTER SET latin1 NOT NULL,
  `value_int` int(11) NOT NULL DEFAULT '0',
  `value_string` varchar(512) CHARACTER SET latin1 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `tokens`
--

CREATE TABLE `tokens` (
  `id` int(11) NOT NULL,
  `user` varchar(31) CHARACTER SET latin1 NOT NULL,
  `privileges` int(11) NOT NULL,
  `description` varchar(255) CHARACTER SET latin1 NOT NULL,
  `token` varchar(127) CHARACTER SET latin1 NOT NULL,
  `private` tinyint(4) NOT NULL,
  `last_updated` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(15) NOT NULL,
  `osuver` varchar(256) DEFAULT NULL,
  `username` varchar(30) CHARACTER SET latin1 NOT NULL,
  `username_safe` varchar(30) CHARACTER SET latin1 NOT NULL,
  `ban_datetime` varchar(30) NOT NULL DEFAULT '0',
  `password_md5` varchar(127) CHARACTER SET latin1 NOT NULL,
  `salt` varchar(32) CHARACTER SET latin1 NOT NULL,
  `email` varchar(254) CHARACTER SET latin1 NOT NULL,
  `register_datetime` int(10) NOT NULL,
  `rank` tinyint(1) NOT NULL DEFAULT '1',
  `allowed` tinyint(1) NOT NULL DEFAULT '1',
  `latest_activity` int(10) NOT NULL DEFAULT '0',
  `silence_end` int(11) NOT NULL DEFAULT '0',
  `silence_reason` varchar(127) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `password_version` tinyint(4) NOT NULL DEFAULT '1',
  `privileges` bigint(11) NOT NULL,
  `donor_expire` int(11) NOT NULL DEFAULT '0',
  `flags` int(11) NOT NULL DEFAULT '0',
  `achievements_version` int(11) NOT NULL DEFAULT '4',
  `achievements_0` int(11) NOT NULL DEFAULT '1',
  `achievements_1` int(11) NOT NULL DEFAULT '1',
  `notes` text,
  `frozen` int(11) NOT NULL DEFAULT '0',
  `freezedate` int(11) NOT NULL DEFAULT '0',
  `firstloginafterfrozen` int(11) NOT NULL DEFAULT '0',
  `bypass_hwid` tinyint(1) NOT NULL DEFAULT '0',
  `ban_reason` varchar(128) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users_achievements`
--

CREATE TABLE `users_achievements` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `achievement_id` int(11) NOT NULL,
  `time` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `users_beatmap_playcount`
--

CREATE TABLE `users_beatmap_playcount` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `beatmap_id` int(11) DEFAULT NULL,
  `game_mode` int(11) DEFAULT NULL,
  `playcount` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users_relationships`
--

CREATE TABLE `users_relationships` (
  `id` int(11) NOT NULL,
  `user1` int(11) NOT NULL,
  `user2` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `users_stats`
--

CREATE TABLE `users_stats` (
  `id` int(11) NOT NULL,
  `username` varchar(30) CHARACTER SET latin1 NOT NULL,
  `username_aka` varchar(64) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `user_color` varchar(16) CHARACTER SET latin1 NOT NULL DEFAULT 'black',
  `user_style` varchar(128) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `ranked_score_std` bigint(20) DEFAULT '0',
  `playcount_std` int(11) NOT NULL DEFAULT '0',
  `total_score_std` bigint(20) DEFAULT '0',
  `replays_watched_std` int(11) UNSIGNED NOT NULL DEFAULT '0',
  `ranked_score_taiko` bigint(20) DEFAULT '0',
  `playcount_taiko` int(11) NOT NULL DEFAULT '0',
  `total_score_taiko` bigint(20) DEFAULT '0',
  `replays_watched_taiko` int(11) NOT NULL DEFAULT '0',
  `ranked_score_ctb` bigint(20) DEFAULT '0',
  `playcount_ctb` int(11) NOT NULL DEFAULT '0',
  `total_score_ctb` bigint(20) DEFAULT '0',
  `replays_watched_ctb` int(11) NOT NULL DEFAULT '0',
  `ranked_score_mania` bigint(20) DEFAULT '0',
  `playcount_mania` int(11) NOT NULL DEFAULT '0',
  `total_score_mania` bigint(20) DEFAULT '0',
  `replays_watched_mania` int(10) UNSIGNED NOT NULL DEFAULT '0',
  `total_hits_std` int(11) NOT NULL DEFAULT '0',
  `total_hits_taiko` int(11) NOT NULL DEFAULT '0',
  `total_hits_ctb` int(11) NOT NULL DEFAULT '0',
  `total_hits_mania` int(11) NOT NULL DEFAULT '0',
  `country` char(2) CHARACTER SET latin1 NOT NULL DEFAULT 'XX',
  `unrestricted_pp` int(11) NOT NULL DEFAULT '0',
  `ppboard` int(11) NOT NULL DEFAULT '0',
  `show_country` tinyint(4) NOT NULL DEFAULT '1',
  `level_std` int(11) NOT NULL DEFAULT '1',
  `level_taiko` int(11) NOT NULL DEFAULT '1',
  `level_ctb` int(11) NOT NULL DEFAULT '1',
  `level_mania` int(11) NOT NULL DEFAULT '1',
  `playtime_std` int(11) NOT NULL DEFAULT '0',
  `playtime_taiko` int(11) NOT NULL DEFAULT '0',
  `playtime_ctb` int(11) NOT NULL DEFAULT '0',
  `playtime_mania` int(11) NOT NULL DEFAULT '0',
  `avg_accuracy_std` float(15,12) NOT NULL DEFAULT '0.000000000000',
  `avg_accuracy_taiko` float(15,12) NOT NULL DEFAULT '0.000000000000',
  `avg_accuracy_ctb` float(15,12) NOT NULL DEFAULT '0.000000000000',
  `avg_accuracy_mania` float(15,12) NOT NULL DEFAULT '0.000000000000',
  `pp_std` int(11) NOT NULL DEFAULT '0',
  `pp_taiko` int(11) NOT NULL DEFAULT '0',
  `pp_ctb` int(11) NOT NULL DEFAULT '0',
  `pp_mania` int(11) NOT NULL DEFAULT '0',
  `badges_shown` varchar(24) CHARACTER SET latin1 NOT NULL DEFAULT '1,0,0,0,0,0',
  `safe_title` tinyint(4) NOT NULL DEFAULT '0',
  `userpage_content` mediumtext CHARACTER SET latin1,
  `play_style` smallint(6) NOT NULL DEFAULT '0',
  `favourite_mode` tinyint(4) NOT NULL DEFAULT '0',
  `prefer_relax` int(11) NOT NULL DEFAULT '0',
  `custom_badge_icon` varchar(32) CHARACTER SET latin1 NOT NULL DEFAULT '',
  `custom_badge_name` varchar(256) NOT NULL DEFAULT '',
  `can_custom_badge` tinyint(1) NOT NULL DEFAULT '0',
  `show_custom_badge` tinyint(1) NOT NULL DEFAULT '0',
  `current_status` varchar(20000) NOT NULL DEFAULT 'Offline',
  `achievements` bigint(15) NOT NULL DEFAULT '0',
  `max_combo_std` int(12) NOT NULL DEFAULT '0',
  `max_combo_taiko` int(12) NOT NULL DEFAULT '0',
  `max_combo_ctb` int(12) NOT NULL DEFAULT '0',
  `max_combo_mania` int(12) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user_badges`
--

CREATE TABLE `user_badges` (
  `id` int(11) NOT NULL,
  `user` int(11) NOT NULL,
  `badge` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `user_clans`
--

CREATE TABLE `user_clans` (
  `id` int(11) NOT NULL,
  `user` int(11) NOT NULL,
  `clan` int(11) NOT NULL,
  `perms` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `ussr_achievements`
--

CREATE TABLE `ussr_achievements` (
  `id` int(11) NOT NULL DEFAULT '0',
  `file` varchar(128) NOT NULL,
  `name` varchar(128) NOT NULL,
  `desc` varchar(128) NOT NULL,
  `cond` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Table structure for table `seasonal_bg`
--

CREATE TABLE `seasonal_bg` (
  `id` int(11) NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `url` varchar(256) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `achievements`
--
ALTER TABLE `achievements`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `ap_stats`
--
ALTER TABLE `ap_stats`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `badges`
--
ALTER TABLE `badges`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `bancho_channels`
--
ALTER TABLE `bancho_channels`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `bancho_settings`
--
ALTER TABLE `bancho_settings`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `bancho_tokens`
--
ALTER TABLE `bancho_tokens`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `beatmaps`
--
ALTER TABLE `beatmaps`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id` (`id`),
  ADD KEY `id_2` (`id`),
  ADD KEY `index2` (`beatmap_md5`),
  ADD KEY `index3` (`beatmap_id`),
  ADD KEY `bmap_id` (`beatmapset_id`,`ranked`);

--
-- Indexes for table `beatmaps_rating`
--
ALTER TABLE `beatmaps_rating`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `clans`
--
ALTER TABLE `clans`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `clans_invites`
--
ALTER TABLE `clans_invites`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `client_err_logs`
--
ALTER TABLE `client_err_logs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `comments`
--
ALTER TABLE `comments`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `first_places`
--
ALTER TABLE `first_places`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `hw_user`
--
ALTER TABLE `hw_user`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `identity_tokens`
--
ALTER TABLE `identity_tokens`
  ADD UNIQUE KEY `userid` (`userid`);

--
-- Indexes for table `ip_user`
--
ALTER TABLE `ip_user`
  ADD PRIMARY KEY (`userid`),
  ADD UNIQUE KEY `userid` (`userid`);

--
-- Indexes for table `lastfm_flags`
--
ALTER TABLE `lastfm_flags`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `main_menu_icons`
--
ALTER TABLE `main_menu_icons`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `new_achievements`
--
ALTER TABLE `new_achievements`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `file` (`file`),
  ADD UNIQUE KEY `desc` (`desc`),
  ADD UNIQUE KEY `cond` (`cond`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `password_recovery`
--
ALTER TABLE `password_recovery`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `privileges_groups`
--
ALTER TABLE `privileges_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `profile_backgrounds`
--
ALTER TABLE `profile_backgrounds`
  ADD PRIMARY KEY (`uid`);

--
-- Indexes for table `rank_requests`
--
ALTER TABLE `rank_requests`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `bid` (`bid`);

--
-- Indexes for table `rap_logs`
--
ALTER TABLE `rap_logs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `remember`
--
ALTER TABLE `remember`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `rx_beatmap_playcount`
--
ALTER TABLE `rx_beatmap_playcount`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `playcount_index` (`user_id`,`beatmap_id`);

--
-- Indexes for table `rx_stats`
--
ALTER TABLE `rx_stats`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `scores`
--
ALTER TABLE `scores`
  ADD PRIMARY KEY (`id`),
  ADD KEY `index2` (`userid`),
  ADD KEY `beatmap_md5` (`beatmap_md5`);

--
-- Indexes for table `scores_ap`
--
ALTER TABLE `scores_ap`
  ADD PRIMARY KEY (`id`),
  ADD KEY `beatmap_md5` (`beatmap_md5`);

--
-- Indexes for table `scores_relax`
--
ALTER TABLE `scores_relax`
  ADD PRIMARY KEY (`id`),
  ADD KEY `beatmap_md5` (`beatmap_md5`);

--
-- Indexes for table `system_settings`
--
ALTER TABLE `system_settings`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tokens`
--
ALTER TABLE `tokens`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users_achievements`
--
ALTER TABLE `users_achievements`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users_beatmap_playcount`
--
ALTER TABLE `users_beatmap_playcount`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `playcount_index` (`user_id`,`beatmap_id`);

--
-- Indexes for table `users_relationships`
--
ALTER TABLE `users_relationships`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users_stats`
--
ALTER TABLE `users_stats`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user_badges`
--
ALTER TABLE `user_badges`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user_clans`
--
ALTER TABLE `user_clans`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `ussr_achievements`
--
ALTER TABLE `ussr_achievements`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `seasonal_bg`
  ADD PRIMARY KEY (`id`),
  ADD KEY `enabled` (`enabled`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ap_stats`
--
ALTER TABLE `ap_stats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `badges`
--
ALTER TABLE `badges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `bancho_channels`
--
ALTER TABLE `bancho_channels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `bancho_settings`
--
ALTER TABLE `bancho_settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `bancho_tokens`
--
ALTER TABLE `bancho_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `beatmaps`
--
ALTER TABLE `beatmaps`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `beatmaps_rating`
--
ALTER TABLE `beatmaps_rating`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `clans`
--
ALTER TABLE `clans`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `clans_invites`
--
ALTER TABLE `clans_invites`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `client_err_logs`
--
ALTER TABLE `client_err_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `comments`
--
ALTER TABLE `comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `first_places`
--
ALTER TABLE `first_places`
  MODIFY `id` int(100) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `hw_user`
--
ALTER TABLE `hw_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lastfm_flags`
--
ALTER TABLE `lastfm_flags`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `main_menu_icons`
--
ALTER TABLE `main_menu_icons`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `new_achievements`
--
ALTER TABLE `new_achievements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `password_recovery`
--
ALTER TABLE `password_recovery`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `privileges_groups`
--
ALTER TABLE `privileges_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rank_requests`
--
ALTER TABLE `rank_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rap_logs`
--
ALTER TABLE `rap_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `remember`
--
ALTER TABLE `remember`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rx_beatmap_playcount`
--
ALTER TABLE `rx_beatmap_playcount`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rx_stats`
--
ALTER TABLE `rx_stats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `scores`
--
ALTER TABLE `scores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `scores_ap`
--
ALTER TABLE `scores_ap`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2000000000;

--
-- AUTO_INCREMENT for table `scores_relax`
--
ALTER TABLE `scores_relax`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1073741824;

--
-- AUTO_INCREMENT for table `system_settings`
--
ALTER TABLE `system_settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tokens`
--
ALTER TABLE `tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(15) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users_achievements`
--
ALTER TABLE `users_achievements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users_beatmap_playcount`
--
ALTER TABLE `users_beatmap_playcount`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users_relationships`
--
ALTER TABLE `users_relationships`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users_stats`
--
ALTER TABLE `users_stats`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_badges`
--
ALTER TABLE `user_badges`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_clans`
--
ALTER TABLE `user_clans`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

-- AUTO_INCREMENT for table `seasonal_bg`
--
ALTER TABLE `seasonal_bg`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

-- Default Values
INSERT INTO `bancho_channels` (`id`, `name`, `description`, `public_read`, `public_write`, `status`, `temp`, `hidden`) VALUES
(1, '#osu', 'The primary general RealistikOsu chat channel.', 1, 1, 1, 0, 0),
(2, '#announce', 'The channel where all announcements are sent (such as new number 1 scores).', 1, 0, 1, 0, 0),
(3, '#polish', 'The chat for the Polish community of RealistikOsu!', 1, 1, 1, 0, 0),
(6, '#lobby', 'This is the lobby where you find games to play with others!', 1, 1, 1, 0, 1),
(7, '#ranked', 'This is where newly ranked maps will appear.', 1, 0, 1, 0, 0);

INSERT INTO `system_settings` (`id`, `name`, `value_int`, `value_string`) VALUES
(1, 'website_maintenance', 0, ''),
(2, 'game_maintenance', 0, ''),
(3, 'website_global_alert', 0, ''),
(4, 'website_home_alert', 0, ''),
(5, 'registrations_enabled', 1, ''),
(6, 'ccreation_enabled', 1, '');

-- Achievements
INSERT INTO `ussr_achievements` (`id`, `file`, `name`, `desc`, `cond`) VALUES
(1, 'osu-skill-pass-1', 'Rising Star', 'Can\'t go forward without the first steps.', '(score.mods & 1 == 0) and 1 <= score.sr < 2 and mode_vn == 0'),
(2, 'osu-skill-pass-2', 'Constellation Prize', 'Definitely not a consolation prize. Now things start getting hard!', '(score.mods & 1 == 0) and 2 <= score.sr < 3 and mode_vn == 0'),
(3, 'osu-skill-pass-3', 'Building Confidence', 'Oh, you\'ve SO got this.', '(score.mods & 1 == 0) and 3 <= score.sr < 4 and mode_vn == 0'),
(4, 'osu-skill-pass-4', 'Insanity Approaches', 'You\'re not twitching, you\'re just ready.', '(score.mods & 1 == 0) and 4 <= score.sr < 5 and mode_vn == 0'),
(5, 'osu-skill-pass-5', 'These Clarion Skies', 'Everything seems so clear now.', '(score.mods & 1 == 0) and 5 <= score.sr < 6 and mode_vn == 0'),
(6, 'osu-skill-pass-6', 'Above and Beyond', 'A cut above the rest.', '(score.mods & 1 == 0) and 6 <= score.sr < 7 and mode_vn == 0'),
(7, 'osu-skill-pass-7', 'Supremacy', 'All marvel before your prowess.', '(score.mods & 1 == 0) and 7 <= score.sr < 8 and mode_vn == 0'),
(8, 'osu-skill-pass-8', 'Absolution', 'My god, you\'re full of stars!', '(score.mods & 1 == 0) and 8 <= score.sr < 9 and mode_vn == 0'),
(9, 'osu-skill-pass-9', 'Event Horizon', 'No force dares to pull you under.', '(score.mods & 1 == 0) and 9 <= score.sr < 10 and mode_vn == 0'),
(10, 'osu-skill-pass-10', 'Phantasm', 'Fevered is your passion, extraordinary is your skill.', '(score.mods & 1 == 0) and 10 <= score.sr < 11 and mode_vn == 0'),
(11, 'osu-skill-fc-1', 'Totality', 'All the notes. Every single one.', 'score.full_combo and 1 <= score.sr < 2 and mode_vn == 0'),
(12, 'osu-skill-fc-2', 'Business As Usual', 'Two to go, please.', 'score.full_combo and 2 <= score.sr < 3 and mode_vn == 0'),
(13, 'osu-skill-fc-3', 'Building Steam', 'Hey, this isn\'t so bad.', 'score.full_combo and 3 <= score.sr < 4 and mode_vn == 0'),
(14, 'osu-skill-fc-4', 'Moving Forward', 'Bet you feel good about that.', 'score.full_combo and 4 <= score.sr < 5 and mode_vn == 0'),
(15, 'osu-skill-fc-5', 'Paradigm Shift', 'Surprisingly difficult.', 'score.full_combo and 5 <= score.sr < 6 and mode_vn == 0'),
(16, 'osu-skill-fc-6', 'Anguish Quelled', 'Don\'t choke.', 'score.full_combo and 6 <= score.sr < 7 and mode_vn == 0'),
(17, 'osu-skill-fc-7', 'Never Give Up', 'Excellence is its own reward.', 'score.full_combo and 7 <= score.sr < 8 and mode_vn == 0'),
(18, 'osu-skill-fc-8', 'Aberration', 'They said it couldn\'t be done. They were wrong.', 'score.full_combo and 8 <= score.sr < 9 and mode_vn == 0'),
(19, 'osu-skill-fc-9', 'Chosen', 'Reign among the Prometheans, where you belong.', 'score.full_combo and 9 <= score.sr < 10 and mode_vn == 0'),
(20, 'osu-skill-fc-10', 'Unfathomable', 'You have no equal.', 'score.full_combo and 10 <= score.sr < 11 and mode_vn == 0'),
(21, 'osu-combo-500', '500 Combo', '500 big ones! You\'re moving up in the world!', '500 <= score.max_combo < 750 and mode_vn == 0'),
(22, 'osu-combo-750', '750 Combo', '750 notes back to back? Woah.', '750 <= score.max_combo < 1000 and mode_vn == 0'),
(23, 'osu-combo-1000', '1000 Combo', 'A thousand reasons why you rock at this game.', '1000 <= score.max_combo < 2000 and mode_vn == 0'),
(24, 'osu-combo-2000', '2000 Combo', 'Nothing can stop you now.', '2000 <= score.max_combo and mode_vn == 0'),
(25, 'taiko-skill-pass-1', 'My First Don', 'Marching to the beat of your own drum. Literally.', '(score.mods & 1 == 0) and 1 <= score.sr < 2 and mode_vn == 1'),
(26, 'taiko-skill-pass-2', 'Katsu Katsu Katsu', 'Hora! Izuko!', '(score.mods & 1 == 0) and 2 <= score.sr < 3 and mode_vn == 1'),
(27, 'taiko-skill-pass-3', 'Not Even Trying', 'Muzukashii? Not even.', '(score.mods & 1 == 0) and 3 <= score.sr < 4 and mode_vn == 1'),
(28, 'taiko-skill-pass-4', 'Face Your Demons', 'The first trials are now behind you, but are you a match for the Oni?', '(score.mods & 1 == 0) and 4 <= score.sr < 5 and mode_vn == 1'),
(29, 'taiko-skill-pass-5', 'The Demon Within', 'No rest for the wicked.', '(score.mods & 1 == 0) and 5 <= score.sr < 6 and mode_vn == 1'),
(30, 'taiko-skill-pass-6', 'Drumbreaker', 'Too strong.', '(score.mods & 1 == 0) and 6 <= score.sr < 7 and mode_vn == 1'),
(31, 'taiko-skill-pass-7', 'The Godfather', 'You are the Don of Dons.', '(score.mods & 1 == 0) and 7 <= score.sr < 8 and mode_vn == 1'),
(32, 'taiko-skill-pass-8', 'Rhythm Incarnate', 'Feel the beat. Become the beat.', '(score.mods & 1 == 0) and 8 <= score.sr < 9 and mode_vn == 1'),
(33, 'taiko-skill-fc-1', 'Keeping Time', 'Don, then katsu. Don, then katsu..', 'score.full_combo and 1 <= score.sr < 2 and mode_vn == 1'),
(34, 'taiko-skill-fc-2', 'To Your Own Beat', 'Straight and steady.', 'score.full_combo and 2 <= score.sr < 3 and mode_vn == 1'),
(35, 'taiko-skill-fc-3', 'Big Drums', 'Bigger scores to match.', 'score.full_combo and 3 <= score.sr < 4 and mode_vn == 1'),
(36, 'taiko-skill-fc-4', 'Adversity Overcome', 'Difficult? Not for you.', 'score.full_combo and 4 <= score.sr < 5 and mode_vn == 1'),
(37, 'taiko-skill-fc-5', 'Demonslayer', 'An Oni felled forevermore.', 'score.full_combo and 5 <= score.sr < 6 and mode_vn == 1'),
(38, 'taiko-skill-fc-6', 'Rhythm\'s Call', 'Heralding true skill.', 'score.full_combo and 6 <= score.sr < 7 and mode_vn == 1'),
(39, 'taiko-skill-fc-7', 'Time Everlasting', 'Not a single beat escapes you.', 'score.full_combo and 7 <= score.sr < 8 and mode_vn == 1'),
(40, 'taiko-skill-fc-8', 'The Drummer\'s Throne', 'Percussive brilliance befitting royalty alone.', 'score.full_combo and 8 <= score.sr < 9 and mode_vn == 1'),
(41, 'fruits-skill-pass-1', 'A Slice Of Life', 'Hey, this fruit catching business isn\'t bad.', '(score.mods & 1 == 0) and 1 <= score.sr < 2 and mode_vn == 2'),
(42, 'fruits-skill-pass-2', 'Dashing Ever Forward', 'Fast is how you do it.', '(score.mods & 1 == 0) and 2 <= score.sr < 3 and mode_vn == 2'),
(43, 'fruits-skill-pass-3', 'Zesty Disposition', 'No scurvy for you, not with that much fruit.', '(score.mods & 1 == 0) and 3 <= score.sr < 4 and mode_vn == 2'),
(44, 'fruits-skill-pass-4', 'Hyperdash ON!', 'Time and distance is no obstacle to you.', '(score.mods & 1 == 0) and 4 <= score.sr < 5 and mode_vn == 2'),
(45, 'fruits-skill-pass-5', 'It\'s Raining Fruit', 'And you can catch them all.', '(score.mods & 1 == 0) and 5 <= score.sr < 6 and mode_vn == 2'),
(46, 'fruits-skill-pass-6', 'Fruit Ninja', 'Legendary techniques.', '(score.mods & 1 == 0) and 6 <= score.sr < 7 and mode_vn == 2'),
(47, 'fruits-skill-pass-7', 'Dreamcatcher', 'No fruit, only dreams now.', '(score.mods & 1 == 0) and 7 <= score.sr < 8 and mode_vn == 2'),
(48, 'fruits-skill-pass-8', 'Lord of the Catch', 'Your kingdom kneels before you.', '(score.mods & 1 == 0) and 8 <= score.sr < 9 and mode_vn == 2'),
(49, 'fruits-skill-fc-1', 'Sweet And Sour', 'Apples and oranges, literally.', 'score.full_combo and 1 <= score.sr < 2 and mode_vn == 2'),
(50, 'fruits-skill-fc-2', 'Reaching The Core', 'The seeds of future success.', 'score.full_combo and 2 <= score.sr < 3 and mode_vn == 2'),
(51, 'fruits-skill-fc-3', 'Clean Platter', 'Clean only of failure. It is completely full, otherwise.', 'score.full_combo and 3 <= score.sr < 4 and mode_vn == 2'),
(52, 'fruits-skill-fc-4', 'Between The Rain', 'No umbrella needed.', 'score.full_combo and 4 <= score.sr < 5 and mode_vn == 2'),
(53, 'fruits-skill-fc-5', 'Addicted', 'That was an overdose?', 'score.full_combo and 5 <= score.sr < 6 and mode_vn == 2'),
(54, 'fruits-skill-fc-6', 'Quickening', 'A dash above normal limits.', 'score.full_combo and 6 <= score.sr < 7 and mode_vn == 2'),
(55, 'fruits-skill-fc-7', 'Supersonic', 'Faster than is reasonably necessary.', 'score.full_combo and 7 <= score.sr < 8 and mode_vn == 2'),
(56, 'fruits-skill-fc-8', 'Dashing Scarlet', 'Speed beyond mortal reckoning.', 'score.full_combo and 8 <= score.sr < 9 and mode_vn == 2'),
(57, 'mania-skill-pass-1', 'First Steps', 'It isn\'t 9-to-5, but 1-to-9. Keys, that is.', '(score.mods & 1 == 0) and 1 <= score.sr < 2 and mode_vn == 3'),
(58, 'mania-skill-pass-2', 'No Normal Player', 'Not anymore, at least.', '(score.mods & 1 == 0) and 2 <= score.sr < 3 and mode_vn == 3'),
(59, 'mania-skill-pass-3', 'Impulse Drive', 'Not quite hyperspeed, but getting close.', '(score.mods & 1 == 0) and 3 <= score.sr < 4 and mode_vn == 3'),
(60, 'mania-skill-pass-4', 'Hyperspeed', 'Woah.', '(score.mods & 1 == 0) and 4 <= score.sr < 5 and mode_vn == 3'),
(61, 'mania-skill-pass-5', 'Ever Onwards', 'Another challenge is just around the corner.', '(score.mods & 1 == 0) and 5 <= score.sr < 6 and mode_vn == 3'),
(62, 'mania-skill-pass-6', 'Another Surpassed', 'Is there no limit to your skills?', '(score.mods & 1 == 0) and 6 <= score.sr < 7 and mode_vn == 3'),
(63, 'mania-skill-pass-7', 'Extra Credit', 'See me after class.', '(score.mods & 1 == 0) and 7 <= score.sr < 8 and mode_vn == 3'),
(64, 'mania-skill-pass-8', 'Maniac', 'There\'s just no stopping you.', '(score.mods & 1 == 0) and 8 <= score.sr < 9 and mode_vn == 3'),
(65, 'mania-skill-fc-1', 'Keystruck', 'The beginning of a new story', 'score.full_combo and 1 <= score.sr < 2 and mode_vn == 3'),
(66, 'mania-skill-fc-2', 'Keying In', 'Finding your groove.', 'score.full_combo and 2 <= score.sr < 3 and mode_vn == 3'),
(67, 'mania-skill-fc-3', 'Hyperflow', 'You can *feel* the rhythm.', 'score.full_combo and 3 <= score.sr < 4 and mode_vn == 3'),
(68, 'mania-skill-fc-4', 'Breakthrough', 'Many skills mastered, rolled into one.', 'score.full_combo and 4 <= score.sr < 5 and mode_vn == 3'),
(69, 'mania-skill-fc-5', 'Everything Extra', 'Giving your all is giving everything you have.', 'score.full_combo and 5 <= score.sr < 6 and mode_vn == 3'),
(70, 'mania-skill-fc-6', 'Level Breaker', 'Finesse beyond reason', 'score.full_combo and 6 <= score.sr < 7 and mode_vn == 3'),
(71, 'mania-skill-fc-7', 'Step Up', 'A precipice rarely seen.', 'score.full_combo and 7 <= score.sr < 8 and mode_vn == 3'),
(72, 'mania-skill-fc-8', 'Behind The Veil', 'Supernatural!', 'score.full_combo and 8 <= score.sr < 9 and mode_vn == 3'),
(73, 'osu-plays-5000', '5,000 Plays', 'There\'s a lot more where that came from.', '5000 <= stats.playcount and mode_vn == 0'),
(74, 'osu-plays-15000', '15,000 Plays', 'Must.. click.. circles..', '15000 <= stats.playcount and mode_vn == 0'),
(75, 'osu-plays-25000', '25,000 Plays', 'There\'s no going back.', '25000 <= stats.playcount and mode_vn == 0'),
(76, 'osu-plays-50000', '50,000 Plays', 'You\'re here forever.', '50000 <= stats.playcount and mode_vn == 0'),
(77, 'taiko-hits-30000', '30,000 Drum Hits', 'Did that drum have a face?', '30000 <= stats.total_hits and mode_vn == 1'),
(78, 'taiko-hits-300000', '300,000 Drum Hits', 'The rhythm never stops.', '300000 <= stats.total_hits and mode_vn == 1'),
(79, 'taiko-hits-3000000', '3,000,000 Drum Hits', 'Truly, the Don of dons.', '3000000 <= stats.total_hits and mode_vn == 1'),
(80, 'fruits-hits-20000', 'Catch 20,000 fruits', 'That is a lot of dietary fiber.', '20000 <= stats.total_hits and mode_vn == 2'),
(81, 'fruits-hits-200000', 'Catch 200,000 fruits', 'So, I heard you like fruit..', '200000 <= stats.total_hits and mode_vn == 2'),
(82, 'fruits-hits-2000000', 'Catch 2,000,000 fruits', 'Downright healthy.', '2000000 <= stats.total_hits and mode_vn == 2'),
(83, 'mania-hits-40000', '40,000 Keys', 'Just the start of the rainbow.', '40000 <= stats.total_hits and mode_vn == 3'),
(84, 'mania-hits-400000', '400,000 Keys', 'Four hundred thousand and still not even close.', '400000 <= stats.total_hits and mode_vn == 3'),
(85, 'mania-hits-4000000', '4,000,000 Keys', 'Is this the end of the rainbow?', '4000000 <= stats.total_hits and mode_vn == 3'),
(86, 'all-intro-suddendeath', 'Finality', 'High stakes, no regrets.', '(score.mods & 32 != 0) and score.passed'),
(87, 'all-intro-perfect', 'Perfectionist', 'Accept nothing but the best.', '(score.mods & 16384 != 0) and score.passed'),
(88, 'all-intro-hardrock', 'Rock Around The Clock', 'You can\'t stop the rock.', '(score.mods & 16 != 0) and score.passed'),
(89, 'all-intro-doubletime', 'Time And A Half', 'Having a right ol\' time. One and a half of them, almost.', '(score.mods & 64 != 0) and score.passed'),
(90, 'all-intro-nightcore', 'Sweet Rave Party', 'Founded in the fine tradition of changing things that were just fine as they were.', '(score.mods & 512 != 0) and score.passed'),
(91, 'all-intro-hidden', 'Blindsight', 'I can see just perfectly.', '(score.mods & 8 != 0) and score.passed'),
(92, 'all-intro-flashlight', 'Are You Afraid Of The Dark?', 'Harder than it looks, probably because it\'s hard to look.', '(score.mods & 1024 != 0) and score.passed'),
(93, 'all-intro-easy', 'Dial It Right Back', 'Sometimes you just want to take it easy.', '(score.mods & 2 != 0) and score.passed'),
(94, 'all-intro-nofail', 'Risk Averse', 'Safety nets are fun!', '(score.mods & 1 != 0) and score.passed'),
(95, 'all-intro-halftime', 'Slowboat', 'You got there. Eventually.', '(score.mods & 256 != 0) and score.passed'),
(96, 'all-intro-spunout', 'Burned Out', 'One cannot always spin to win.', '(score.mods & 4096 != 0) and score.passed');

-- Bot
INSERT INTO `users` (`id`, `osuver`, `username`, `username_safe`, `ban_datetime`, `password_md5`, `salt`, `email`, `register_datetime`, `rank`, `allowed`, `latest_activity`, `silence_end`, `silence_reason`, `password_version`, `privileges`, `donor_expire`, `flags`, `achievements_version`, `achievements_0`, `achievements_1`, `notes`, `frozen`, `freezedate`, `firstloginafterfrozen`, `bypass_hwid`, `ban_reason`) VALUES (999, NULL, 'RealistikBot', 'realistikbot', '0', 'ferdiuhgerggerger', '', 'rel@es.to', '1578160000', '4', '1', '1578160000', '0', '', '1', '942669823', '2147483647', '0', '0', '1', '1', 'Why are you running?', '0', '0', '0', '0', '');
INSERT INTO `users_stats` (`id`, `username`, `username_aka`, `user_color`, `user_style`, `ranked_score_std`, `playcount_std`, `total_score_std`, `replays_watched_std`, `ranked_score_taiko`, `playcount_taiko`, `total_score_taiko`, `replays_watched_taiko`, `ranked_score_ctb`, `playcount_ctb`, `total_score_ctb`, `replays_watched_ctb`, `ranked_score_mania`, `playcount_mania`, `total_score_mania`, `replays_watched_mania`, `total_hits_std`, `total_hits_taiko`, `total_hits_ctb`, `total_hits_mania`, `country`, `unrestricted_pp`, `ppboard`, `show_country`, `level_std`, `level_taiko`, `level_ctb`, `level_mania`, `playtime_std`, `playtime_taiko`, `playtime_ctb`, `playtime_mania`, `avg_accuracy_std`, `avg_accuracy_taiko`, `avg_accuracy_ctb`, `avg_accuracy_mania`, `pp_std`, `pp_taiko`, `pp_ctb`, `pp_mania`, `badges_shown`, `safe_title`, `userpage_content`, `play_style`, `favourite_mode`, `prefer_relax`, `custom_badge_icon`, `custom_badge_name`, `can_custom_badge`, `show_custom_badge`, `current_status`, `achievements`, `max_combo_std`, `max_combo_taiko`, `max_combo_ctb`, `max_combo_mania`) VALUES
(999, 'RealistikBot', '', 'black', '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'GB', 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0, 0, 0, 0, '3,4,11,0,0,0', 0, NULL, 0, 0, 0, '', '', 1, 1, 'Dead', 0, 0, 0, 0, 0);
INSERT INTO `rx_stats` (`id`, `username`, `username_aka`, `user_color`, `user_style`, `favourite_mode`, `level_std`, `level_taiko`, `level_mania`, `level_ctb`, `total_score_std`, `total_score_taiko`, `total_score_mania`, `total_score_ctb`, `total_hits_std`, `total_hits_taiko`, `total_hits_ctb`, `total_hits_mania`, `playtime_std`, `playtime_taiko`, `playtime_mania`, `playtime_ctb`, `ranked_score_std`, `ranked_score_taiko`, `ranked_score_mania`, `ranked_score_ctb`, `avg_accuracy_std`, `avg_accuracy_taiko`, `avg_accuracy_mania`, `avg_accuracy_ctb`, `playcount_std`, `playcount_taiko`, `playcount_mania`, `playcount_ctb`, `pp_std`, `pp_mania`, `pp_ctb`, `pp_taiko`, `country`, `unrestricted_pp`, `ppboard`, `replays_watched_std`, `replays_watched_taiko`, `replays_watched_ctb`, `replays_watched_mania`, `achievements`, `max_combo_std`, `max_combo_taiko`, `max_combo_ctb`, `max_combo_mania`) VALUES
(999, 'RealistikBot', '', 'black', '', 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'GB', 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0);
INSERT INTO `ap_stats` (`id`, `username`, `username_aka`, `user_color`, `user_style`, `favourite_mode`, `level_std`, `level_taiko`, `level_mania`, `level_ctb`, `total_score_std`, `total_score_taiko`, `total_score_mania`, `total_score_ctb`, `total_hits_std`, `total_hits_taiko`, `total_hits_ctb`, `total_hits_mania`, `playtime_std`, `playtime_taiko`, `playtime_mania`, `playtime_ctb`, `ranked_score_std`, `ranked_score_taiko`, `ranked_score_mania`, `ranked_score_ctb`, `avg_accuracy_std`, `avg_accuracy_taiko`, `avg_accuracy_mania`, `avg_accuracy_ctb`, `playcount_std`, `playcount_taiko`, `playcount_mania`, `playcount_ctb`, `pp_std`, `pp_mania`, `pp_ctb`, `pp_taiko`, `country`, `unrestricted_pp`, `ppboard`, `replays_watched_std`, `replays_watched_taiko`, `replays_watched_ctb`, `replays_watched_mania`, `achievements`, `max_combo_std`, `max_combo_taiko`, `max_combo_ctb`, `max_combo_mania`) VALUES
(999, 'RealistikBot', '', 'black', '', 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'GB', 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0);


-- These aren't really used...
INSERT INTO `bancho_settings` (`id`, `name`, `value_int`, `value_string`) VALUES
(1, 'bancho_maintenance', 0, ''),
(2, 'free_direct', 0, ''),
(3, 'menu_icon', 1, 'https://ussr.pl/static/logos/logo1.png | https://ussr.pl'),
(4, 'login_messages', 1, ''),
(5, 'restricted_joke', 0, 'You\'re banned from the server.'),
(6, 'login_notification', 1, 'You have connected to RealistikOsu!'),
(7, 'osu_versions', 0, ''),
(8, 'osu_md5s', 0, '');
