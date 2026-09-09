-- EQUIPZILLA CRM OS · esquema físico V1 (PostgreSQL 15+)
-- Principios: nada se borra físicamente (deleted_at / merged_into_id), todo
-- cambio deja audit_logs, toda señal es un evento, todo score se explica.
-- Ver docs/crm-os/00-diseno.md para el modelo lógico.

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- búsqueda por similitud
CREATE EXTENSION IF NOT EXISTS unaccent;   -- normalización de nombres

-- ------------------------------------------------------------ usuarios
CREATE TABLE teams (
  team_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre      text NOT NULL UNIQUE,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
  user_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id     uuid REFERENCES teams(team_id),
  nombre      text NOT NULL,
  email       text NOT NULL UNIQUE,
  role        text NOT NULL CHECK (role IN ('sales','manager','admin','marketing','sourcing')),
  activo      boolean NOT NULL DEFAULT true,
  pipedrive_user_id integer,
  password_hash text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE permissions (
  role        text NOT NULL,
  object      text NOT NULL,          -- companies, contacts, demands, opportunities, machines, campaigns, config…
  action      text NOT NULL,          -- read, read_all, write, assign, delete, configure
  PRIMARY KEY (role, object, action)
);

-- ------------------------------------------------------------ empresas y personas
CREATE TABLE companies (
  company_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre              text NOT NULL,
  nombre_normalizado  text NOT NULL,                 -- lower, sin tildes, sin S.L./S.A.
  cif                 text,
  dominio             text,                          -- sin dominios genéricos
  telefono            text,
  email               text,
  direccion           text,
  ciudad              text,
  provincia           text,
  comunidad_autonoma  text,
  pais                text NOT NULL DEFAULT 'ES',
  codigo_postal       text,
  sector              text,
  actividad           text,                          -- CNAE o texto
  num_empleados       integer,
  facturacion         numeric(14,2),
  tipo_empresa        text CHECK (tipo_empresa IN ('empresa','autonomo','particular','administracion','otro')),
  icp                 text CHECK (icp IN ('A','B','C','D')),
  icp_secundario      text CHECK (icp_secundario IN ('A','B','C','D')),
  fit_score           smallint NOT NULL DEFAULT 0,
  intent_score        smallint NOT NULL DEFAULT 0,
  recency_score       smallint NOT NULL DEFAULT 0,
  value_score         smallint NOT NULL DEFAULT 0,
  total_score         smallint NOT NULL DEFAULT 0,
  indice_recurrencia  numeric(5,2),                 -- compras+alquileres por año
  canal_origen        text,                          -- primer canal por el que entró
  lifecycle_stage     text NOT NULL DEFAULT 'PROSPECT'
                      CHECK (lifecycle_stage IN ('PROSPECT','ENGAGED','CUSTOMER','RECURRING','DORMANT','EXCLUDED')),
  excluded            boolean NOT NULL DEFAULT false,
  excluded_reason     text,
  flota_propia        boolean,
  last_intent_at      timestamptz,
  owner_id            uuid REFERENCES users(user_id),
  source              text NOT NULL,                 -- pipedrive, brevo, smartlead, web, historico, manual
  source_id           text,
  merged_into_id      uuid REFERENCES companies(company_id),
  deleted_at          timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX companies_cif_uq ON companies (cif) WHERE cif IS NOT NULL AND deleted_at IS NULL AND merged_into_id IS NULL;
CREATE UNIQUE INDEX companies_dominio_uq ON companies (dominio) WHERE dominio IS NOT NULL AND deleted_at IS NULL AND merged_into_id IS NULL;
CREATE UNIQUE INDEX companies_nombre_prov_uq ON companies (nombre_normalizado, coalesce(provincia,'')) WHERE deleted_at IS NULL AND merged_into_id IS NULL;
CREATE INDEX companies_score_idx ON companies (total_score DESC) WHERE deleted_at IS NULL AND excluded = false;
CREATE INDEX companies_nombre_trgm ON companies USING gin (nombre_normalizado gin_trgm_ops);
CREATE INDEX companies_owner_idx ON companies (owner_id);

CREATE TABLE contacts (
  contact_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id          uuid REFERENCES companies(company_id),
  nombre              text,
  apellidos           text,
  cargo               text,
  departamento        text,
  rol                 text CHECK (rol IN ('propietario','gerente','compras','maquinaria','jefe_obra','operaciones','logistica','almacen','direccion','otro')),
  email               text,
  telefono            text,                          -- E.164
  whatsapp            text,
  linkedin            text,
  decisor             boolean,
  influencia          smallint CHECK (influencia BETWEEN 0 AND 5),
  preferred_channel   text CHECK (preferred_channel IN ('telefono','whatsapp','email','linkedin')),
  consentimiento      boolean,
  consentimiento_en   timestamptz,
  ultimo_contacto_at  timestamptz,
  ultima_respuesta_at timestamptz,
  owner_id            uuid REFERENCES users(user_id),
  source              text NOT NULL,
  source_id           text,
  merged_into_id      uuid REFERENCES contacts(contact_id),
  deleted_at          timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX contacts_email_uq ON contacts (lower(email)) WHERE email IS NOT NULL AND deleted_at IS NULL AND merged_into_id IS NULL;
CREATE UNIQUE INDEX contacts_tel_uq ON contacts (telefono) WHERE telefono IS NOT NULL AND deleted_at IS NULL AND merged_into_id IS NULL;
CREATE INDEX contacts_company_idx ON contacts (company_id);

-- ------------------------------------------------------------ necesidades (unidad central)
CREATE TABLE demands (
  demand_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id          uuid NOT NULL REFERENCES companies(company_id),
  contact_id          uuid REFERENCES contacts(contact_id),
  tipo_maquina        text,
  categoria           text NOT NULL,                 -- Miniexcavadoras, Plataformas de elevación, Telescópicas…
  marca               text,
  modelo              text,
  peso_t              numeric(6,2),
  potencia_kw         numeric(7,2),
  anio_min            smallint,
  anio_max            smallint,
  horas_min           integer,
  horas_max           integer,
  presupuesto_min     numeric(12,2),
  presupuesto_max     numeric(12,2),
  ubicacion           text,
  provincia           text,
  radio_km            integer,
  accesorios          text[],
  caracteristicas     jsonb NOT NULL DEFAULT '{}'::jsonb,
  uso                 text,
  duracion_necesidad  text,
  fecha_necesidad     date,
  urgencia            text CHECK (urgencia IN ('inmediata','1_mes','3_meses','sin_fecha')),
  financing_needed    boolean,
  renting_possible    boolean,
  buy_possible        boolean NOT NULL DEFAULT true,
  texto_original      text,                          -- lo que dijo el cliente, tal cual
  source              text NOT NULL,
  source_id           text,
  status              text NOT NULL DEFAULT 'NEW'
                      CHECK (status IN ('NEW','QUALIFYING','ACTIVE','SOURCING','MATCHED','NEGOTIATING','WON','LOST','EXPIRED','REACTIVATION')),
  intent_score        smallint NOT NULL DEFAULT 0,
  recency_score       smallint NOT NULL DEFAULT 0,
  owner_id            uuid REFERENCES users(user_id),
  last_activity_at    timestamptz,
  expires_at          timestamptz,
  deleted_at          timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX demands_company_idx ON demands (company_id);
CREATE INDEX demands_status_cat_idx ON demands (status, categoria) WHERE deleted_at IS NULL;
CREATE INDEX demands_expires_idx ON demands (expires_at) WHERE status IN ('ACTIVE','SOURCING','MATCHED');
CREATE UNIQUE INDEX demands_source_uq ON demands (source, source_id) WHERE source_id IS NOT NULL;

-- ------------------------------------------------------------ señales de intención
CREATE TABLE intent_signals (
  signal_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id    uuid REFERENCES companies(company_id),
  contact_id    uuid REFERENCES contacts(contact_id),
  demand_id     uuid REFERENCES demands(demand_id),
  machine_id    uuid,                                -- FK añadida tras crear machines
  type          text NOT NULL CHECK (type IN (
                  'solicitud_compra','respuesta_outbound','respuesta_whatsapp','email_abierto','email_respondido',
                  'clic','visita_repetida','consulta_maquina','solicitud_precio','solicitud_disponibilidad',
                  'calculadora_rent_vs_buy','alerta_creada','descarga','formulario','historico_alquiler',
                  'renting','visita_categoria','rechazo','autoreply')),
  source        text NOT NULL,                       -- brevo, smartlead, web, pipedrive, whatsapp, telefono
  source_id     text,
  occurred_at   timestamptz NOT NULL,
  strength      smallint NOT NULL DEFAULT 0,         -- copiado de score_rules en el momento de crearse
  metadata      jsonb NOT NULL DEFAULT '{}'::jsonb,  -- campaña, url, máquina, texto…
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX intent_signals_source_uq ON intent_signals (source, source_id) WHERE source_id IS NOT NULL;
CREATE INDEX intent_signals_company_time_idx ON intent_signals (company_id, occurred_at DESC);
CREATE INDEX intent_signals_demand_idx ON intent_signals (demand_id);

-- ------------------------------------------------------------ máquinas, proveedores, matching
CREATE TABLE suppliers (
  supplier_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre          text NOT NULL,
  tipo            text CHECK (tipo IN ('alquilador','distribuidor','particular','subasta','otro')),
  contacto        text,
  telefono        text,
  email           text,
  condiciones     jsonb NOT NULL DEFAULT '{}'::jsonb, -- comisión, consignación, plazo
  maquinas_vivas  integer NOT NULL DEFAULT 0,
  leads_generados integer NOT NULL DEFAULT 0,
  cierres         integer NOT NULL DEFAULT 0,
  deleted_at      timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE machines (
  machine_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ref               text,                            -- referencia interna (KB298, EL-JLG1930ES…)
  supplier_id       uuid REFERENCES suppliers(supplier_id),
  categoria         text NOT NULL,
  tipo              text,
  familia           text,
  marca             text,
  modelo            text,
  anio              smallint,
  horas             integer,
  precio            numeric(12,2),                   -- PVP
  precio_propietario numeric(12,2),
  precio_compra_teorico numeric(12,2),
  pvp_agil          numeric(12,2),                   -- precio para vender en 60–90 días
  semaforo          text CHECK (semaforo IN ('verde','ambar','rojo')),
  ubicacion         text,
  provincia         text,
  estado            text NOT NULL DEFAULT 'DISPONIBLE'
                    CHECK (estado IN ('DISPONIBLE','RESERVADA','VENDIDA','RETIRADA','PENDIENTE_VERIFICAR')),
  equipamiento      jsonb NOT NULL DEFAULT '{}'::jsonb,
  accesorios        text[],
  capacidad         text,                            -- "2.500 kg", "14 m"
  fotos             text[],                          -- URLs internas, sin marca de proveedor
  disponibilidad    date,
  publicado_en      text[],                          -- web, mascus, milanuncios
  fecha_alta        date,
  fecha_baja        date,
  verificado_en     date,                            -- última verificación con el propietario
  source            text NOT NULL,                   -- stock_sheet, marketplace, manual
  source_id         text,
  deleted_at        timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX machines_ref_uq ON machines (ref) WHERE ref IS NOT NULL AND deleted_at IS NULL;
CREATE UNIQUE INDEX machines_source_uq ON machines (source, source_id) WHERE source_id IS NOT NULL;
CREATE INDEX machines_cat_estado_idx ON machines (categoria, estado);
ALTER TABLE intent_signals ADD CONSTRAINT intent_signals_machine_fk FOREIGN KEY (machine_id) REFERENCES machines(machine_id);

CREATE TABLE machine_matches (
  match_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  demand_id     uuid NOT NULL REFERENCES demands(demand_id),
  machine_id    uuid NOT NULL REFERENCES machines(machine_id),
  score         smallint NOT NULL CHECK (score BETWEEN 0 AND 100),
  explicacion   jsonb NOT NULL,                      -- [{factor, puntos, detalle}]
  estado        text NOT NULL DEFAULT 'PROPUESTA' CHECK (estado IN ('PROPUESTA','ENVIADA','DESCARTADA','ELEGIDA')),
  descartada_por text,
  calculated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (demand_id, machine_id)
);
CREATE INDEX machine_matches_score_idx ON machine_matches (demand_id, score DESC);

-- ------------------------------------------------------------ pipeline y oportunidades
CREATE TABLE pipeline_stages (
  stage_id      text PRIMARY KEY,                    -- NEW, QUALIFIED, SOURCING, MATCHED, CONTACTED, INTERESTED, MACHINE_REVIEW, OFFER, NEGOTIATION, WON, LOST
  nombre        text NOT NULL,
  orden         smallint NOT NULL,
  probabilidad  smallint NOT NULL DEFAULT 0,
  dias_alerta   smallint,                            -- sin actividad → at risk
  pipedrive_stage_id integer,
  activo        boolean NOT NULL DEFAULT true
);

CREATE TABLE campaigns (
  campaign_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre        text NOT NULL,
  icp           text,
  segmento      text,
  lista         text,
  canal         text NOT NULL CHECK (canal IN ('email_abm','frio','whatsapp','linkedin','ads','seo','web','telefono')),
  mensaje       text,
  secuencia     jsonb,
  owner_id      uuid REFERENCES users(user_id),
  fecha         date,
  status        text NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','SCHEDULED','SENT','ACTIVE','PAUSED','DONE')),
  source        text,                                -- brevo, smartlead, google_ads
  source_id     text,
  enviados integer DEFAULT 0, entregados integer DEFAULT 0, abiertos integer DEFAULT 0,
  respuestas integer DEFAULT 0, respuestas_positivas integer DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX campaigns_source_uq ON campaigns (source, source_id) WHERE source_id IS NOT NULL;

CREATE TABLE campaign_members (
  campaign_id   uuid NOT NULL REFERENCES campaigns(campaign_id),
  contact_id    uuid NOT NULL REFERENCES contacts(contact_id),
  estado        text NOT NULL DEFAULT 'ENVIADO' CHECK (estado IN ('PENDIENTE','ENVIADO','ABIERTO','CLIC','RESPONDIO','RECHAZO','BAJA')),
  enviado_at    timestamptz,
  PRIMARY KEY (campaign_id, contact_id)
);

CREATE TABLE opportunities (
  opportunity_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id      uuid NOT NULL REFERENCES companies(company_id),
  contact_id      uuid REFERENCES contacts(contact_id),
  demand_id       uuid REFERENCES demands(demand_id),
  owner_id        uuid REFERENCES users(user_id),
  titulo          text NOT NULL,
  source          text NOT NULL,                     -- canal de origen (lead attribution)
  first_touch     text,
  last_touch      text,
  campaign_id     uuid REFERENCES campaigns(campaign_id),
  stage_id        text NOT NULL REFERENCES pipeline_stages(stage_id) DEFAULT 'NEW',
  stage_changed_at timestamptz NOT NULL DEFAULT now(),
  expected_value  numeric(12,2),
  expected_margin numeric(12,2),
  probability     smallint,
  next_action     text,
  next_action_date date,
  close_date      date,
  won_at          timestamptz,
  lost_at         timestamptz,
  lost_reason_id  text,                              -- obligatorio si stage = LOST (check abajo)
  lost_detail     text,
  pipedrive_deal_id integer,
  deleted_at      timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT opportunities_lost_reason_chk CHECK (stage_id <> 'LOST' OR lost_reason_id IS NOT NULL)
);
CREATE UNIQUE INDEX opportunities_pipedrive_uq ON opportunities (pipedrive_deal_id) WHERE pipedrive_deal_id IS NOT NULL;
CREATE INDEX opportunities_stage_idx ON opportunities (stage_id) WHERE deleted_at IS NULL;
CREATE INDEX opportunities_owner_next_idx ON opportunities (owner_id, next_action_date);
CREATE INDEX opportunities_company_idx ON opportunities (company_id);

CREATE TABLE opportunity_machines (                  -- máquinas candidatas de una oportunidad
  opportunity_id uuid NOT NULL REFERENCES opportunities(opportunity_id),
  machine_id     uuid NOT NULL REFERENCES machines(machine_id),
  rol            text NOT NULL DEFAULT 'CANDIDATA' CHECK (rol IN ('CANDIDATA','PROPUESTA','ELEGIDA','DESCARTADA')),
  PRIMARY KEY (opportunity_id, machine_id)
);

CREATE TABLE lost_reasons (
  lost_reason_id text PRIMARY KEY,                   -- precio, sin_maquina, competidor, compro_nueva, aplazo, financiacion, ubicacion, caracteristicas, vendedor, timing, otro
  nombre         text NOT NULL,
  activo         boolean NOT NULL DEFAULT true
);
ALTER TABLE opportunities ADD CONSTRAINT opportunities_lost_reason_fk FOREIGN KEY (lost_reason_id) REFERENCES lost_reasons(lost_reason_id);

-- ------------------------------------------------------------ ofertas y operaciones
CREATE TABLE offers (
  offer_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id  uuid NOT NULL REFERENCES opportunities(opportunity_id),
  machine_id      uuid REFERENCES machines(machine_id),
  precio          numeric(12,2) NOT NULL,
  alternativas    jsonb NOT NULL DEFAULT '[]'::jsonb, -- [{machine_id, precio}] opciones B y C
  servicios       jsonb NOT NULL DEFAULT '{}'::jsonb, -- transporte, garantía, mantenimiento, financiación
  enviada_at      timestamptz,
  estado          text NOT NULL DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR','ENVIADA','ACEPTADA','RECHAZADA','CADUCADA')),
  created_by      uuid REFERENCES users(user_id),
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE deals (                                 -- operación cerrada
  deal_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id  uuid NOT NULL UNIQUE REFERENCES opportunities(opportunity_id),
  offer_id        uuid REFERENCES offers(offer_id),
  precio_final    numeric(12,2) NOT NULL,
  coste           numeric(12,2),
  margen          numeric(12,2),
  comision_pct    numeric(5,2),
  servicios       jsonb NOT NULL DEFAULT '{}'::jsonb,
  dias_desde_demanda integer,
  dias_desde_alta_maquina integer,
  desviacion_vs_pvp numeric(6,2),
  closed_at       timestamptz NOT NULL DEFAULT now(),
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE deal_items (
  deal_item_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id       uuid NOT NULL REFERENCES deals(deal_id),
  machine_id    uuid REFERENCES machines(machine_id),
  descripcion   text,
  precio        numeric(12,2) NOT NULL,
  coste         numeric(12,2)
);

-- ------------------------------------------------------------ actividad, tareas, sourcing, alquiler
CREATE TABLE activities (
  activity_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id      uuid REFERENCES companies(company_id),
  contact_id      uuid REFERENCES contacts(contact_id),
  opportunity_id  uuid REFERENCES opportunities(opportunity_id),
  demand_id       uuid REFERENCES demands(demand_id),
  tipo            text NOT NULL CHECK (tipo IN ('llamada','email','whatsapp','reunion','visita','nota','sistema')),
  direccion       text CHECK (direccion IN ('saliente','entrante')),
  resumen         text,
  contenido       text,
  resultado       text,                              -- contactado, sin respuesta, interesado, no interesa…
  user_id         uuid REFERENCES users(user_id),
  occurred_at     timestamptz NOT NULL DEFAULT now(),
  source          text,
  source_id       text,
  created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX activities_company_time_idx ON activities (company_id, occurred_at DESC);
CREATE INDEX activities_opportunity_idx ON activities (opportunity_id);
CREATE UNIQUE INDEX activities_source_uq ON activities (source, source_id) WHERE source_id IS NOT NULL;

CREATE TABLE tasks (
  task_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id      uuid REFERENCES companies(company_id),
  opportunity_id  uuid REFERENCES opportunities(opportunity_id),
  demand_id       uuid REFERENCES demands(demand_id),
  assignee_id     uuid REFERENCES users(user_id),
  titulo          text NOT NULL,
  motivo          text,                              -- explicación (regla o IA) de por qué existe
  prioridad       smallint NOT NULL DEFAULT 2 CHECK (prioridad BETWEEN 1 AND 3),
  due_at          timestamptz,
  status          text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','DONE','SKIPPED')),
  skipped_reason  text,
  created_by      text NOT NULL DEFAULT 'user',      -- user, automation:<id>, ai:<agent>
  done_at         timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX tasks_assignee_due_idx ON tasks (assignee_id, status, due_at);

CREATE TABLE sourcing_requests (
  sourcing_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  demand_id       uuid NOT NULL REFERENCES demands(demand_id),
  owner_id        uuid REFERENCES users(user_id),
  especificacion  text NOT NULL,
  status          text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','BUSCANDO','ENCONTRADA','CERRADA','CANCELADA')),
  supplier_ids    uuid[],
  machine_id      uuid REFERENCES machines(machine_id),
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rental_history (
  rental_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id    uuid NOT NULL REFERENCES companies(company_id),
  contact_id    uuid REFERENCES contacts(contact_id),
  categoria     text NOT NULL,
  maquina       text,
  inicio        date,
  fin           date,
  importe       numeric(12,2),
  source        text NOT NULL,
  source_id     text,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX rental_history_source_uq ON rental_history (source, source_id) WHERE source_id IS NOT NULL;
CREATE INDEX rental_history_company_idx ON rental_history (company_id, categoria);

-- ------------------------------------------------------------ scoring configurable y explicable
CREATE TABLE score_config (
  key     text PRIMARY KEY,                          -- w_fit, w_intent, w_recency, w_value, hot, warm, nurture, half_life_days
  value   numeric NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE score_rules (
  rule_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind        text NOT NULL CHECK (kind IN ('fit','intent','value','exclusion')),
  nombre      text NOT NULL,
  condicion   jsonb NOT NULL,                        -- {field, op, value} o {signal_type}
  puntos      smallint NOT NULL,
  activa      boolean NOT NULL DEFAULT true,
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE scores (                                -- snapshot vigente por entidad
  entity_type   text NOT NULL CHECK (entity_type IN ('company','demand','opportunity')),
  entity_id     uuid NOT NULL,
  fit smallint NOT NULL DEFAULT 0, intent smallint NOT NULL DEFAULT 0,
  recency smallint NOT NULL DEFAULT 0, value smallint NOT NULL DEFAULT 0,
  total smallint NOT NULL DEFAULT 0,
  banda         text NOT NULL CHECK (banda IN ('HOT','WARM','NURTURE','LOW')),
  explicacion   jsonb NOT NULL,                      -- [{regla, puntos, detalle}]
  calculated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (entity_type, entity_id)
);

CREATE TABLE score_events (                          -- histórico de cada recálculo (para calibrar)
  score_event_id bigserial PRIMARY KEY,
  entity_type   text NOT NULL,
  entity_id     uuid NOT NULL,
  total smallint NOT NULL, fit smallint, intent smallint, recency smallint, value smallint,
  explicacion   jsonb NOT NULL,
  trigger       text,                                -- evento que provocó el recálculo
  calculated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX score_events_entity_idx ON score_events (entity_type, entity_id, calculated_at DESC);

CREATE TABLE match_config (
  factor  text PRIMARY KEY,                          -- categoria, presupuesto, anio, horas, ubicacion, marca_modelo, caracteristicas, disponibilidad
  peso    smallint NOT NULL,
  reglas  jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE stage_history (                         -- log de cambios de etapa: de → a, quién, cuándo (mide tiempos)
  stage_history_id bigserial PRIMARY KEY,
  opportunity_id  uuid NOT NULL REFERENCES opportunities(opportunity_id),
  from_stage      text REFERENCES pipeline_stages(stage_id),
  to_stage        text NOT NULL REFERENCES pipeline_stages(stage_id),
  user_id         uuid REFERENCES users(user_id),
  source          text,
  changed_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX stage_history_opp_idx ON stage_history (opportunity_id, changed_at);

CREATE TABLE channel_costs (                         -- coste por canal y mes → CAC real
  canal     text NOT NULL,                           -- brevo, smartlead, google_ads, seo, apify, herramientas, comercial
  mes       date NOT NULL,                           -- primer día del mes
  coste     numeric(12,2) NOT NULL,
  detalle   text,
  PRIMARY KEY (canal, mes)
);

-- ------------------------------------------------------------ eventos, automatizaciones, IA, auditoría
CREATE TABLE events (                                -- append-only
  event_id        bigserial PRIMARY KEY,
  type            text NOT NULL,
  occurred_at     timestamptz NOT NULL DEFAULT now(),
  company_id      uuid, contact_id uuid, demand_id uuid, opportunity_id uuid, machine_id uuid,
  actor_user_id   uuid REFERENCES users(user_id),
  source          text,
  source_id       text,
  payload         jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX events_company_time_idx ON events (company_id, occurred_at DESC);
CREATE INDEX events_type_time_idx ON events (type, occurred_at DESC);
CREATE UNIQUE INDEX events_source_uq ON events (type, source, source_id) WHERE source_id IS NOT NULL;

CREATE TABLE automations (
  automation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre        text NOT NULL,
  trigger_type  text NOT NULL,                       -- event type o 'schedule'
  condicion     jsonb NOT NULL,                      -- SI …
  accion        jsonb NOT NULL,                      -- ENTONCES … (create_task, notify, set_status, create_sourcing…)
  activa        boolean NOT NULL DEFAULT true,
  ultimo_run_at timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
  notification_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid NOT NULL REFERENCES users(user_id),
  tipo          text NOT NULL,                       -- cliente_caliente, maquina_encaja, demanda_sin_matching, oportunidad_enfriandose, historico_vuelve
  titulo        text NOT NULL,
  cuerpo        text,
  entity_type   text, entity_id uuid,
  leida_at      timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX notifications_user_idx ON notifications (user_id, leida_at, created_at DESC);

CREATE TABLE ai_insights (
  insight_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent         text NOT NULL,                       -- qualification, buyer_intelligence, follow_up, matching, market, sourcing, reactivation, copilot, growth
  entity_type   text NOT NULL,
  entity_id     uuid NOT NULL,
  resumen       text NOT NULL,
  recomendacion text,
  explicacion   jsonb NOT NULL,                      -- lista de razones con datos
  inputs_hash   text,                                -- para no recalcular sin cambios
  model         text,
  created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ai_insights_entity_idx ON ai_insights (entity_type, entity_id, created_at DESC);

CREATE TABLE tags (
  tag_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre   text NOT NULL UNIQUE,
  color    text
);
CREATE TABLE entity_tags (
  tag_id      uuid NOT NULL REFERENCES tags(tag_id),
  entity_type text NOT NULL,
  entity_id   uuid NOT NULL,
  PRIMARY KEY (tag_id, entity_type, entity_id)
);

CREATE TABLE merge_candidates (                      -- duplicados detectados, decisión humana
  merge_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type   text NOT NULL CHECK (entity_type IN ('company','contact')),
  entity_a      uuid NOT NULL,
  entity_b      uuid NOT NULL,
  motivo        text NOT NULL,                       -- mismo dominio, nombre similar 0.92, mismo teléfono…
  status        text NOT NULL DEFAULT 'PENDIENTE' CHECK (status IN ('PENDIENTE','FUSIONADO','DESCARTADO')),
  decided_by    uuid REFERENCES users(user_id),
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
  audit_id      bigserial PRIMARY KEY,
  entity_type   text NOT NULL,
  entity_id     uuid NOT NULL,
  action        text NOT NULL,                       -- create, update, merge, soft_delete, stage_change
  campo         text,
  valor_anterior jsonb,
  valor_nuevo   jsonb,
  user_id       uuid REFERENCES users(user_id),
  source        text,                                -- ui, api, sync:pipedrive, automation:<id>
  occurred_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_logs_entity_idx ON audit_logs (entity_type, entity_id, occurred_at DESC);

-- ------------------------------------------------------------ updated_at automático
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END $$ LANGUAGE plpgsql;
DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['users','companies','contacts','demands','suppliers','machines','campaigns',
                           'opportunities','offers','tasks','sourcing_requests'] LOOP
    EXECUTE format('CREATE TRIGGER %I_touch BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION touch_updated_at()', t, t);
  END LOOP; END $$;

-- ------------------------------------------------------------ semillas mínimas
INSERT INTO pipeline_stages (stage_id, nombre, orden, probabilidad, dias_alerta, pipedrive_stage_id) VALUES
  ('NEW','Nueva',1,5,2,45), ('QUALIFIED','Cualificada',2,10,3,33), ('SOURCING','Sourcing',3,10,5,NULL),
  ('MATCHED','Con máquina',4,20,3,33), ('CONTACTED','Contactada',5,25,3,NULL), ('INTERESTED','Interesada',6,35,7,NULL),
  ('MACHINE_REVIEW','Revisión de máquina',7,50,7,NULL), ('OFFER','Oferta',8,60,5,37), ('NEGOTIATION','Negociación',9,75,5,38),
  ('WON','Ganada',10,100,NULL,46), ('LOST','Perdida',11,0,NULL,NULL);

INSERT INTO lost_reasons (lost_reason_id, nombre) VALUES
  ('precio','Precio'), ('sin_maquina','No encontró máquina'), ('competidor','Compró a competidor'),
  ('compro_nueva','Compró nueva'), ('aplazo','Aplazó la compra'), ('financiacion','Financiación'),
  ('ubicacion','Ubicación'), ('caracteristicas','Características'), ('vendedor','Vendedor'), ('timing','Timing'),
  ('no_responde','No responde'), ('cancelado','Cancelado'), ('otro','Otro');

INSERT INTO score_config (key, value) VALUES
  ('w_fit',0.25), ('w_intent',0.35), ('w_recency',0.25), ('w_value',0.15),
  ('hot',80), ('warm',60), ('nurture',40), ('half_life_days',14);

INSERT INTO match_config (factor, peso) VALUES
  ('categoria',30), ('presupuesto',20), ('anio',10), ('horas',10), ('ubicacion',10),
  ('marca_modelo',10), ('caracteristicas',5), ('disponibilidad',5);

INSERT INTO score_rules (kind, nombre, condicion, puntos) VALUES
  ('fit','Actividad: excavaciones / movimiento de tierras', '{"field":"actividad","op":"~","value":"excavac|movimiento de tierras|derribo|demolic"}', 30),
  ('fit','Actividad: constructora / obra civil', '{"field":"actividad","op":"~","value":"constru|obra civil|infraestruct|urbaniz"}', 25),
  ('fit','Actividad: alquilador de maquinaria', '{"field":"actividad","op":"~","value":"alquil|rental"}', 25),
  ('fit','Actividad: industria / logística', '{"field":"actividad","op":"~","value":"industr|logist|almac|transport"}', 15),
  ('fit','Flota propia', '{"field":"flota_propia","op":"=","value":true}', 15),
  ('fit','ICP A', '{"field":"icp","op":"=","value":"A"}', 25),
  ('fit','ICP D', '{"field":"icp","op":"=","value":"D"}', 20),
  ('exclusion','Arquitectura, consultoría, BIM, promotoras, inmobiliarias, topografía, reformas, administrativas',
     '{"field":"actividad","op":"~","value":"arquitect|consultor|bim|project management|promotor|inmobiliari|topograf|reforma interior|gestor[ií]a|asesor[ií]a"}', 0),
  ('intent','Solicitud de compra', '{"signal_type":"solicitud_compra"}', 40),
  ('intent','Respuesta a outbound', '{"signal_type":"respuesta_outbound"}', 30),
  ('intent','Solicitud de precio', '{"signal_type":"solicitud_precio"}', 30),
  ('intent','Solicitud de disponibilidad', '{"signal_type":"solicitud_disponibilidad"}', 25),
  ('intent','Formulario web', '{"signal_type":"formulario"}', 25),
  ('intent','Consulta de máquina', '{"signal_type":"consulta_maquina"}', 15),
  ('intent','Clic en campaña', '{"signal_type":"clic"}', 8),
  ('intent','Visita repetida', '{"signal_type":"visita_repetida"}', 6),
  ('intent','Email abierto', '{"signal_type":"email_abierto"}', 2),
  ('intent','Rechazo explícito', '{"signal_type":"rechazo"}', -40);
