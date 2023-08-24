UPDATE scores AS s1
SET status = 4
WHERE status = 2
AND pp = (
    SELECT MAX(pp)
    FROM scores AS s2
    WHERE s1.mods = s2.mods
);

UPDATE scores_relax AS s1
SET status = 4
WHERE status = 2
AND pp = (
    SELECT MAX(pp)
    FROM scores_relax AS s2
    WHERE s1.mods = s2.mods
);

UPDATE scores_ap AS s1
SET status = 4
WHERE status = 2
AND pp = (
    SELECT MAX(pp)
    FROM scores_ap AS s2
    WHERE s1.mods = s2.mods
);