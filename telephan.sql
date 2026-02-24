-- création de la base de données mes_kpi si elle n'existe pas déjà
CREATE DATABASE IF NOT EXISTS mes_kpi
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mes_kpi;

-- Table dimensionnelle pour le temps
CREATE TABLE dim_time (
  time_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  date           DATE NOT NULL,
  hour           TINYINT NULL,          -- 0-23, NULL si tu restes au grain "jour"
  year           SMALLINT NOT NULL,
  month          TINYINT NOT NULL,
  day            TINYINT NOT NULL,
  week           TINYINT NOT NULL,
  quarter        TINYINT NOT NULL,
  shift          VARCHAR(20) NULL,
  UNIQUE KEY uq_dim_time (date, hour)
) ENGINE=InnoDB;

-- Table dimensionnelle pour les machines
CREATE TABLE dim_machine (
  machine_id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  mes_resource_id  INT NOT NULL,        -- mes4.tblresource.ResourceID
  name             VARCHAR(100) NOT NULL,
  type             VARCHAR(50) NULL,
  area             VARCHAR(100) NULL,
  UNIQUE KEY uq_machine_mes (mes_resource_id)
) ENGINE=InnoDB;

-- Table dimensionnelle pour les produits
CREATE TABLE dim_product (
  product_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  mes_pno      INT NOT NULL,            -- mes4.tblparts.PNo
  name         VARCHAR(255) NULL,
  family       VARCHAR(100) NULL,
  UNIQUE KEY uq_product_mes (mes_pno)
) ENGINE=InnoDB;

-- Table dimensionnelle pour les commandes
CREATE TABLE dim_order (
  order_id     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  mes_ono      INT NOT NULL,            -- mes4.tblfinorder.ONo
  product_id   INT UNSIGNED NULL,
  customer     VARCHAR(100) NULL,
  order_type   VARCHAR(50) NULL,
  UNIQUE KEY uq_order_mes (mes_ono),
  CONSTRAINT fk_dim_order_product
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id)
) ENGINE=InnoDB;

-- Table dimensionnelle pour les opérations des étapes de fabrication
CREATE TABLE dim_step_operation (
  step_id                 INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  workplan_no             INT NOT NULL,          -- WPNo
  step_no                 INT NOT NULL,          -- StepNo
  operation_no            INT NULL,              -- OpNo si tu l’utilises
  theoretical_cycle_time  INT NULL,              -- en secondes, mappé depuis WorkingTimeCalc
  planned_machine_id      INT UNSIGNED NULL,
  UNIQUE KEY uq_step_wp_step (workplan_no, step_no),
  CONSTRAINT fk_step_planned_machine
    FOREIGN KEY (planned_machine_id) REFERENCES dim_machine(machine_id)
) ENGINE=InnoDB;

-- Table dimensionnelle pour les buffers
CREATE TABLE dim_buffer (
  buffer_id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  mes_resource_id    INT NOT NULL,      -- mes4.tblbuffer.ResourceID
  mes_bufno          INT NOT NULL,      -- mes4.tblbuffer.BufNo
  buffer_type        TINYINT NOT NULL,  -- 1=stock, 2=fifo, 3=stack, etc.
  capacity_positions INT NULL,          -- nb de slots estimé
  area               VARCHAR(100) NULL,
  UNIQUE KEY uq_buffer_mes (mes_resource_id, mes_bufno)
) ENGINE=InnoDB;

-- Table dimensionnelle pour les erreurs
CREATE TABLE dim_error (
  error_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  mes_error_id    INT NOT NULL,         -- mes4.tblerrorcodes.ErrorId
  code            VARCHAR(50) NULL,
  description     VARCHAR(255) NULL,
  severity        ENUM('minor','major','critical') DEFAULT 'minor',
  UNIQUE KEY uq_error_mes (mes_error_id)
) ENGINE=InnoDB;

-- Table de faits pour l'état des machines
CREATE TABLE fact_machine_state (
  machine_state_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  time_id            INT UNSIGNED NOT NULL,
  machine_id         INT UNSIGNED NOT NULL,

  busy_seconds       INT UNSIGNED NOT NULL DEFAULT 0,
  available_seconds  INT UNSIGNED NOT NULL DEFAULT 0,
  error_seconds      INT UNSIGNED NOT NULL DEFAULT 0,

  CONSTRAINT fk_ms_time
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_ms_machine
    FOREIGN KEY (machine_id) REFERENCES dim_machine(machine_id),

  INDEX idx_ms_time_machine (time_id, machine_id)
) ENGINE=InnoDB;

-- Table de faits pour les exécutions des étapes de fabrication
CREATE TABLE fact_step_execution (
  step_execution_id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  time_id               INT UNSIGNED NOT NULL,     -- début ou fin de step
  machine_id            INT UNSIGNED NOT NULL,
  product_id            INT UNSIGNED NULL,
  order_id              INT UNSIGNED NULL,
  step_id               INT UNSIGNED NULL,

  cycle_time_seconds    INT UNSIGNED NULL,         -- End - Start
  quantity_input        INT UNSIGNED DEFAULT 0,
  quantity_output_ok    INT UNSIGNED DEFAULT 0,
  quantity_output_nok   INT UNSIGNED DEFAULT 0,

  energy_mws            BIGINT NULL,               -- énergie électrique [mWs]
  air_mnl               BIGINT NULL,               -- air comprimé [mNl]

  CONSTRAINT fk_fse_time
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_fse_machine
    FOREIGN KEY (machine_id) REFERENCES dim_machine(machine_id),
  CONSTRAINT fk_fse_product
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
  CONSTRAINT fk_fse_order
    FOREIGN KEY (order_id) REFERENCES dim_order(order_id),
  CONSTRAINT fk_fse_step
    FOREIGN KEY (step_id) REFERENCES dim_step_operation(step_id),

  INDEX idx_fse_time_machine (time_id, machine_id),
  INDEX idx_fse_product (product_id),
  INDEX idx_fse_order (order_id)
) ENGINE=InnoDB;

-- Table de faits pour les événements qualité
CREATE TABLE fact_quality_event (
  quality_event_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  time_id            INT UNSIGNED NOT NULL,
  machine_id         INT UNSIGNED NULL,
  product_id         INT UNSIGNED NULL,
  order_id           INT UNSIGNED NULL,
  error_id           INT UNSIGNED NOT NULL,

  piece_count        INT UNSIGNED NOT NULL DEFAULT 1,
  is_critical        TINYINT(1) NOT NULL DEFAULT 0,

  CONSTRAINT fk_fqe_time
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_fqe_machine
    FOREIGN KEY (machine_id) REFERENCES dim_machine(machine_id),
  CONSTRAINT fk_fqe_product
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
  CONSTRAINT fk_fqe_order
    FOREIGN KEY (order_id) REFERENCES dim_order(order_id),
  CONSTRAINT fk_fqe_error
    FOREIGN KEY (error_id) REFERENCES dim_error(error_id),

  INDEX idx_fqe_time (time_id),
  INDEX idx_fqe_product (product_id),
  INDEX idx_fqe_machine (machine_id)
) ENGINE=InnoDB;

-- Table de faits pour les snapshots de stock dans les buffers
CREATE TABLE fact_stock_snapshot (
  stock_snapshot_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  time_id             INT UNSIGNED NOT NULL,
  buffer_id           INT UNSIGNED NOT NULL,
  product_id          INT UNSIGNED NULL,

  quantity            INT UNSIGNED NOT NULL DEFAULT 0,
  positions_used      INT UNSIGNED NOT NULL DEFAULT 0,

  CONSTRAINT fk_fss_time
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_fss_buffer
    FOREIGN KEY (buffer_id) REFERENCES dim_buffer(buffer_id),
  CONSTRAINT fk_fss_product
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),

  INDEX idx_fss_time_buffer (time_id, buffer_id),
  INDEX idx_fss_product (product_id)
) ENGINE=InnoDB;

-- Table de faits pour les livraisons des commandes
CREATE TABLE fact_order_delivery (
  order_delivery_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id                  INT UNSIGNED NOT NULL,
  product_id                INT UNSIGNED NULL,

  time_start_id             INT UNSIGNED NOT NULL,
  time_end_id               INT UNSIGNED NOT NULL,
  time_planned_start_id     INT UNSIGNED NULL,
  time_planned_end_id       INT UNSIGNED NULL,

  real_lead_time_seconds    INT UNSIGNED NULL,
  planned_lead_time_seconds INT UNSIGNED NULL,
  delivered_on_time         TINYINT(1) NOT NULL DEFAULT 0,

  CONSTRAINT fk_fod_order
    FOREIGN KEY (order_id) REFERENCES dim_order(order_id),
  CONSTRAINT fk_fod_product
    FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
  CONSTRAINT fk_fod_time_start
    FOREIGN KEY (time_start_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_fod_time_end
    FOREIGN KEY (time_end_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_fod_time_pstart
    FOREIGN KEY (time_planned_start_id) REFERENCES dim_time(time_id),
  CONSTRAINT fk_fod_time_pend
    FOREIGN KEY (time_planned_end_id) REFERENCES dim_time(time_id),

  INDEX idx_fod_product (product_id),
  INDEX idx_fod_delivered (delivered_on_time)
) ENGINE=InnoDB;

-- Table de staging pour l'import des données énergie depuis CSV
CREATE TABLE staging_energy (
  energy_id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  time_seconds        DOUBLE NULL,
  pressure_bar        DOUBLE NULL,
  flow_rate_l_min     DOUBLE NULL,
  active_power_l1_w   DOUBLE NULL,
  active_power_l2_w   DOUBLE NULL,
  active_power_l3_w   DOUBLE NULL,
  raw_line            TEXT NULL,
  loaded_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  COMMENT='Import brut depuis dataEnergy.csv (Time [s]; Pressure [bar]; Flow Rate [l/min]; Active Power L1/L2/L3 [W])';

-- Table de staging pour l'import des données robotino comprimé depuis CSV
CREATE TABLE staging_robotino (
  robotino_id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ts                        DATETIME NULL,
  power_voltage             DOUBLE NULL,
  power_output_current      DOUBLE NULL,
  power_battery_low         TINYINT(1) NULL,
  power_ext_power           TINYINT(1) NULL,
  power_num_chargers        INT NULL,
  charger_0_chargingCurrent DOUBLE NULL,
  charger_0_state           VARCHAR(50) NULL,
  charger_0_batteryVoltage  DOUBLE NULL,
  charger_1_chargingCurrent DOUBLE NULL,
  charger_1_state           VARCHAR(50) NULL,
  charger_1_batteryVoltage  DOUBLE NULL,
  odometry_x                DOUBLE NULL,
  odometry_y                DOUBLE NULL,
  odometry_phi              DOUBLE NULL,
  odometry_vx               DOUBLE NULL,
  odometry_vy               DOUBLE NULL,
  odometry_omega            DOUBLE NULL,
  raw_json                  JSON NULL,
  loaded_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_robotino_ts (ts)
) ENGINE=InnoDB
  COMMENT='Import brut depuis robotino_data.csv (timestamp + mesures puissance/odom). Colonnes principales + reste dans raw_json optionnel.';
