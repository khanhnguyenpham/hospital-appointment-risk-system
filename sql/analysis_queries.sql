-- 1. Monthly appointment volume and no-show rate
SELECT
    substr(appointment_date, 1, 7) AS month,
    COUNT(*) AS appointments,
    ROUND(100.0 * AVG(no_show), 2) AS no_show_rate_pct
FROM appointments
WHERE status <> 'Cancelled'
GROUP BY month
ORDER BY month;

-- 2. Department performance
SELECT
    department,
    COUNT(*) AS appointments,
    ROUND(100.0 * AVG(no_show), 2) AS no_show_rate_pct,
    ROUND(AVG(CASE WHEN status = 'Completed' THEN wait_minutes END), 1) AS avg_wait_minutes
FROM appointments
WHERE status <> 'Cancelled'
GROUP BY department
ORDER BY no_show_rate_pct DESC;

-- 3. Reminder comparison (association, not causal proof)
SELECT
    reminder_sent,
    COUNT(*) AS appointments,
    ROUND(100.0 * AVG(no_show), 2) AS no_show_rate_pct
FROM appointments
WHERE status <> 'Cancelled'
GROUP BY reminder_sent;

-- 4. High-volume time slots
SELECT
    department,
    appointment_hour,
    COUNT(*) AS appointments,
    ROUND(100.0 * AVG(no_show), 2) AS no_show_rate_pct
FROM appointments
WHERE status <> 'Cancelled'
GROUP BY department, appointment_hour
HAVING COUNT(*) >= 20
ORDER BY appointments DESC;

