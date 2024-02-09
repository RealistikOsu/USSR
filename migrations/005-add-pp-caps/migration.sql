CREATE TABLE pp_limits (
    mode tinyint(1) NOT NULL,
    relax tinyint(1) NOT NULL,
    pp int NOT NULL,
    flashlight_pp int NOT NULL
);

INSERT INTO pp_limits (mode, relax, pp, flashlight_pp)
VALUES
(0, 0, 700, 500),
(0, 1, 1400, 1000),
(0, 2, 650, 650), -- autopilot needs more thought one day
(1, 0, 700, 500),
(1, 1, 1200, 1000),
(2, 0, 700, 500),
(2, 1, 1000, 800),
(3, 0, 1200, 600);
