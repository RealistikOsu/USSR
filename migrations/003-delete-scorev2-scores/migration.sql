-- Delete all scores with ScoreV2
DELETE FROM scores WHERE mods & 536870912;
DELETE FROM scores_relax WHERE mods & 536870912;
DELETE FROM scores_ap WHERE mods & 536870912;
