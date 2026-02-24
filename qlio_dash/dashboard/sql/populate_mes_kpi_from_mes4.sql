USE mes_kpi;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE fact_quality_event;
TRUNCATE TABLE fact_stock_snapshot;
TRUNCATE TABLE fact_order_delivery;
TRUNCATE TABLE fact_step_execution;
TRUNCATE TABLE fact_machine_state;
TRUNCATE TABLE dim_step_operation;
TRUNCATE TABLE dim_order;
TRUNCATE TABLE dim_buffer;
TRUNCATE TABLE dim_error;
TRUNCATE TABLE dim_product;
TRUNCATE TABLE dim_machine;
TRUNCATE TABLE dim_time;
SET FOREIGN_KEY_CHECKS = 1;

/* Time dimension (hour grain) from all relevant MES timestamps */
INSERT IGNORE INTO dim_time (
  `date`, `hour`, `year`, `month`, `day`, `week`, `quarter`, `shift`
)
SELECT
  DATE(src.ts) AS `date`,
  HOUR(src.ts) AS `hour`,
  YEAR(src.ts) AS `year`,
  MONTH(src.ts) AS `month`,
  DAY(src.ts) AS `day`,
  WEEK(src.ts, 3) AS `week`,
  QUARTER(src.ts) AS `quarter`,
  CASE
    WHEN HOUR(src.ts) BETWEEN 6 AND 13 THEN 'Matin'
    WHEN HOUR(src.ts) BETWEEN 14 AND 21 THEN 'Apres-midi'
    ELSE 'Nuit'
  END AS `shift`
FROM (
  SELECT TimeStamp AS ts FROM mes4.tblmachinereport WHERE TimeStamp IS NOT NULL
  UNION
  SELECT TimeStamp AS ts FROM mes4.tblpartsreport WHERE TimeStamp IS NOT NULL
  UNION
  SELECT TimeStamp AS ts FROM mes4.tblbufferpos WHERE TimeStamp IS NOT NULL
  UNION
  SELECT Start AS ts FROM mes4.tblfinstep WHERE Start IS NOT NULL
  UNION
  SELECT End AS ts FROM mes4.tblfinstep WHERE End IS NOT NULL
  UNION
  SELECT PlannedStart AS ts FROM mes4.tblfinstep WHERE PlannedStart IS NOT NULL
  UNION
  SELECT PlannedEnd AS ts FROM mes4.tblfinstep WHERE PlannedEnd IS NOT NULL
  UNION
  SELECT Start AS ts FROM mes4.tblfinorder WHERE Start IS NOT NULL
  UNION
  SELECT End AS ts FROM mes4.tblfinorder WHERE End IS NOT NULL
  UNION
  SELECT PlannedStart AS ts FROM mes4.tblfinorder WHERE PlannedStart IS NOT NULL
  UNION
  SELECT PlannedEnd AS ts FROM mes4.tblfinorder WHERE PlannedEnd IS NOT NULL
) src;

/* Machines */
INSERT INTO dim_machine (mes_resource_id, name, type, area)
SELECT
  r.ResourceID,
  COALESCE(NULLIF(r.ResourceName, ''), CONCAT('R-', r.ResourceID)) AS name,
  CAST(r.ResourceType AS CHAR(50)) AS type,
  COALESCE(NULLIF(r.Description, ''), NULLIF(r.ResourceName, ''), CONCAT('Resource ', r.ResourceID)) AS area
FROM mes4.tblresource r;

/* Products */
INSERT INTO dim_product (mes_pno, name, family)
SELECT
  p.PNo,
  COALESCE(NULLIF(p.Short, ''), NULLIF(p.Description, ''), CONCAT('PNo-', p.PNo)) AS name,
  CONCAT('Type ', COALESCE(p.Type, 0)) AS family
FROM mes4.tblparts p;

/* Orders + customer + derived product */
INSERT INTO dim_order (mes_ono, product_id, customer, order_type)
SELECT
  fo.ONo,
  dp.product_id,
  COALESCE(NULLIF(c.Company, ''), CONCAT('CNo ', COALESCE(fo.CNo, 0))) AS customer,
  CONCAT('State ', COALESCE(fo.State, 0)) AS order_type
FROM mes4.tblfinorder fo
LEFT JOIN mes4.tblcustomer c
  ON c.CNo = fo.CNo
LEFT JOIN (
  SELECT fs.ONo, MAX(NULLIF(fs.NewPNo, 0)) AS derived_pno
  FROM mes4.tblfinstep fs
  GROUP BY fs.ONo
) pmap
  ON pmap.ONo = fo.ONo
LEFT JOIN dim_product dp
  ON dp.mes_pno = pmap.derived_pno;

/* Step operations (de-duplicated by WPNo/StepNo) */
INSERT INTO dim_step_operation (
  workplan_no, step_no, operation_no, theoretical_cycle_time, planned_machine_id
)
SELECT
  x.WPNo,
  x.StepNo,
  x.operation_no,
  x.theoretical_cycle_time,
  dm.machine_id
FROM (
  SELECT
    fs.WPNo,
    fs.StepNo,
    MAX(fs.OpNo) AS operation_no,
    CAST(ROUND(AVG(
      CASE
        WHEN fs.Start IS NOT NULL AND fs.End IS NOT NULL
         AND TIMESTAMPDIFF(SECOND, fs.Start, fs.End) >= 0
        THEN TIMESTAMPDIFF(SECOND, fs.Start, fs.End)
        ELSE NULL
      END
    )) AS SIGNED) AS theoretical_cycle_time,
    MAX(COALESCE(fs.ResourceID, 0)) AS planned_resource_id
  FROM mes4.tblfinstep fs
  WHERE fs.WPNo IS NOT NULL
  GROUP BY fs.WPNo, fs.StepNo
) x
LEFT JOIN dim_machine dm
  ON dm.mes_resource_id = x.planned_resource_id;

/* Buffers */
INSERT INTO dim_buffer (
  mes_resource_id, mes_bufno, buffer_type, capacity_positions, area
)
SELECT
  b.ResourceId,
  b.BufNo,
  COALESCE(b.Type, 0) AS buffer_type,
  CASE
    WHEN (COALESCE(b.Sides, 0) * COALESCE(b.Rows, 0) * COALESCE(b.Columns, 0)) > 0
      THEN (COALESCE(b.Sides, 0) * COALESCE(b.Rows, 0) * COALESCE(b.Columns, 0))
    ELSE COALESCE(bp.pos_count, 0)
  END AS capacity_positions,
  CONCAT(COALESCE(NULLIF(r.ResourceName, ''), CONCAT('R-', b.ResourceId)), ' / B', b.BufNo) AS area
FROM mes4.tblbuffer b
LEFT JOIN mes4.tblresource r
  ON r.ResourceID = b.ResourceId
LEFT JOIN (
  SELECT ResourceId, BufNo, COUNT(*) AS pos_count
  FROM mes4.tblbufferpos
  GROUP BY ResourceId, BufNo
) bp
  ON bp.ResourceId = b.ResourceId AND bp.BufNo = b.BufNo;

/* Errors (including unknown codes seen in partsreport) */
INSERT INTO dim_error (mes_error_id, code, description, severity)
SELECT
  e.ErrorId AS mes_error_id,
  COALESCE(NULLIF(e.Short, ''), CONCAT('ERR_', e.ErrorId)) AS code,
  COALESCE(NULLIF(e.Description, ''), CONCAT('Erreur ', e.ErrorId)) AS description,
  CASE
    WHEN e.ErrorId >= 100 THEN 'critical'
    WHEN e.ErrorId > 0 THEN 'major'
    ELSE 'minor'
  END AS severity
FROM mes4.tblerrorcodes e
UNION
SELECT
  x.ErrorID AS mes_error_id,
  CONCAT('ERR_', x.ErrorID) AS code,
  CONCAT('Erreur ', x.ErrorID) AS description,
  CASE
    WHEN x.ErrorID >= 100 THEN 'critical'
    WHEN x.ErrorID > 0 THEN 'major'
    ELSE 'minor'
  END AS severity
FROM (
  SELECT DISTINCT ErrorID
  FROM mes4.tblpartsreport
  WHERE ErrorID IS NOT NULL
) x
LEFT JOIN mes4.tblerrorcodes e
  ON e.ErrorId = x.ErrorID
WHERE e.ErrorId IS NULL;

/* Machine state facts (hourly approximation from reports) */
INSERT INTO fact_machine_state (
  time_id, machine_id, busy_seconds, available_seconds, error_seconds
)
SELECT
  dt.time_id,
  dm.machine_id,
  SUM(CASE WHEN COALESCE(mr.Busy, 0) <> 0 THEN 60 ELSE 0 END) AS busy_seconds,
  COUNT(*) * 60 AS available_seconds,
  SUM(
    CASE
      WHEN (COALESCE(mr.ErrorL0, 0) + COALESCE(mr.ErrorL1, 0) + COALESCE(mr.ErrorL2, 0)) > 0
        THEN 60
      ELSE 0
    END
  ) AS error_seconds
FROM mes4.tblmachinereport mr
JOIN dim_machine dm
  ON dm.mes_resource_id = mr.ResourceID
JOIN dim_time dt
  ON dt.`date` = DATE(mr.TimeStamp)
 AND dt.`hour` = HOUR(mr.TimeStamp)
WHERE mr.TimeStamp IS NOT NULL
GROUP BY dt.time_id, dm.machine_id;

/* Step execution facts (1 row per finished/started MES step row) */
INSERT INTO fact_step_execution (
  time_id, machine_id, product_id, order_id, step_id,
  cycle_time_seconds, quantity_input, quantity_output_ok, quantity_output_nok,
  energy_mws, air_mnl
)
SELECT
  dt.time_id,
  dm.machine_id,
  dp.product_id,
  do2.order_id,
  dso.step_id,
  CASE
    WHEN fs.Start IS NOT NULL AND fs.End IS NOT NULL
     AND TIMESTAMPDIFF(SECOND, fs.Start, fs.End) >= 0
      THEN TIMESTAMPDIFF(SECOND, fs.Start, fs.End)
    ELSE NULL
  END AS cycle_time_seconds,
  CASE WHEN COALESCE(fs.ResourceID, 0) > 0 THEN 1 ELSE 0 END AS quantity_input,
  CASE
    WHEN fs.End IS NOT NULL AND COALESCE(fs.ErrorStep, 0) = 0 THEN 1
    ELSE 0
  END AS quantity_output_ok,
  CASE
    WHEN fs.End IS NOT NULL AND COALESCE(fs.ErrorStep, 0) <> 0 THEN 1
    ELSE 0
  END AS quantity_output_nok,
  NULLIF(COALESCE(fs.ElectricEnergyReal, fs.ElectricEnergyCalc, 0), 0) AS energy_mws,
  NULLIF(COALESCE(fs.CompressedAirReal, fs.CompressedAirCalc, 0), 0) AS air_mnl
FROM mes4.tblfinstep fs
JOIN dim_time dt
  ON dt.`date` = DATE(COALESCE(fs.End, fs.Start, fs.PlannedEnd, fs.PlannedStart))
 AND dt.`hour` = HOUR(COALESCE(fs.End, fs.Start, fs.PlannedEnd, fs.PlannedStart))
JOIN dim_machine dm
  ON dm.mes_resource_id = COALESCE(fs.ResourceID, 0)
LEFT JOIN dim_product dp
  ON dp.mes_pno = NULLIF(fs.NewPNo, 0)
LEFT JOIN dim_order do2
  ON do2.mes_ono = fs.ONo
LEFT JOIN dim_step_operation dso
  ON dso.workplan_no = fs.WPNo AND dso.step_no = fs.StepNo
WHERE COALESCE(fs.End, fs.Start, fs.PlannedEnd, fs.PlannedStart) IS NOT NULL;

/* Quality events (only rows with actual error codes > 0) */
INSERT INTO fact_quality_event (
  time_id, machine_id, product_id, order_id, error_id, piece_count, is_critical
)
SELECT
  dt.time_id,
  dm.machine_id,
  dp.product_id,
  NULL AS order_id,
  de.error_id,
  1 AS piece_count,
  CASE WHEN de.severity = 'critical' THEN 1 ELSE 0 END AS is_critical
FROM mes4.tblpartsreport pr
JOIN dim_time dt
  ON dt.`date` = DATE(pr.TimeStamp)
 AND dt.`hour` = HOUR(pr.TimeStamp)
LEFT JOIN dim_machine dm
  ON dm.mes_resource_id = pr.ResourceID
LEFT JOIN dim_product dp
  ON dp.mes_pno = NULLIF(pr.PNo, 0)
JOIN dim_error de
  ON de.mes_error_id = pr.ErrorID
WHERE pr.TimeStamp IS NOT NULL
  AND COALESCE(pr.ErrorID, 0) > 0;

/* Stock snapshots from current MES buffer positions history */
INSERT INTO fact_stock_snapshot (
  time_id, buffer_id, product_id, quantity, positions_used
)
SELECT
  dt.time_id,
  db.buffer_id,
  dp.product_id,
  GREATEST(
    COALESCE(bp.Quantity, 0),
    CASE WHEN COALESCE(bp.PNo, 0) > 0 THEN 1 ELSE 0 END
  ) AS quantity,
  CASE
    WHEN COALESCE(bp.Booked, 0) <> 0
      OR COALESCE(bp.PNo, 0) > 0
      OR COALESCE(bp.Quantity, 0) > 0
      OR COALESCE(bp.BoxID, 0) > 0
      OR COALESCE(bp.PalletID, 0) > 0
    THEN 1
    ELSE 0
  END AS positions_used
FROM mes4.tblbufferpos bp
JOIN dim_time dt
  ON dt.`date` = DATE(bp.TimeStamp)
 AND dt.`hour` = HOUR(bp.TimeStamp)
JOIN dim_buffer db
  ON db.mes_resource_id = bp.ResourceId
 AND db.mes_bufno = bp.BufNo
LEFT JOIN dim_product dp
  ON dp.mes_pno = NULLIF(bp.PNo, 0)
WHERE bp.TimeStamp IS NOT NULL;

/* Order deliveries */
INSERT INTO fact_order_delivery (
  order_id, product_id,
  time_start_id, time_end_id, time_planned_start_id, time_planned_end_id,
  real_lead_time_seconds, planned_lead_time_seconds, delivered_on_time
)
SELECT
  do2.order_id,
  do2.product_id,
  dt_start.time_id,
  dt_end.time_id,
  dt_pstart.time_id,
  dt_pend.time_id,
  CASE
    WHEN fo.Start IS NOT NULL AND fo.End IS NOT NULL AND TIMESTAMPDIFF(SECOND, fo.Start, fo.End) >= 0
      THEN TIMESTAMPDIFF(SECOND, fo.Start, fo.End)
    ELSE NULL
  END AS real_lead_time_seconds,
  CASE
    WHEN fo.PlannedStart IS NOT NULL AND fo.PlannedEnd IS NOT NULL AND TIMESTAMPDIFF(SECOND, fo.PlannedStart, fo.PlannedEnd) >= 0
      THEN TIMESTAMPDIFF(SECOND, fo.PlannedStart, fo.PlannedEnd)
    ELSE NULL
  END AS planned_lead_time_seconds,
  CASE
    WHEN fo.End IS NOT NULL AND fo.PlannedEnd IS NOT NULL AND fo.End <= fo.PlannedEnd THEN 1
    ELSE 0
  END AS delivered_on_time
FROM mes4.tblfinorder fo
JOIN dim_order do2
  ON do2.mes_ono = fo.ONo
JOIN dim_time dt_start
  ON fo.Start IS NOT NULL
 AND dt_start.`date` = DATE(fo.Start)
 AND dt_start.`hour` = HOUR(fo.Start)
JOIN dim_time dt_end
  ON fo.End IS NOT NULL
 AND dt_end.`date` = DATE(fo.End)
 AND dt_end.`hour` = HOUR(fo.End)
LEFT JOIN dim_time dt_pstart
  ON fo.PlannedStart IS NOT NULL
 AND dt_pstart.`date` = DATE(fo.PlannedStart)
 AND dt_pstart.`hour` = HOUR(fo.PlannedStart)
LEFT JOIN dim_time dt_pend
  ON fo.PlannedEnd IS NOT NULL
 AND dt_pend.`date` = DATE(fo.PlannedEnd)
 AND dt_pend.`hour` = HOUR(fo.PlannedEnd)
WHERE fo.Start IS NOT NULL
  AND fo.End IS NOT NULL;
