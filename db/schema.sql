-- tmvo.ru — модель базы данных (PostgreSQL 14+)
-- Этап 2 по ROADMAP.md. Схема повторяет структуру data/catalog.json и объекты заказа из api.js,
-- поэтому переход «демо → база» не требует менять фронтенд: сервер отдаёт те же поля.

------------------------------------------------------------------------------------------
-- КАТАЛОГ
------------------------------------------------------------------------------------------
CREATE TABLE categories (
  id          text PRIMARY KEY,                 -- matrasy, toppery, namatrasniki, detskie-matrasy, detskie-namatrasniki, sale
  name        text NOT NULL,                    -- «Матрасы»
  url         text NOT NULL,                    -- matrasy/
  sort        int  NOT NULL DEFAULT 0
);

CREATE TABLE products (
  id          text PRIMARY KEY,                 -- matras-zevs (последняя часть адреса страницы)
  category_id text NOT NULL REFERENCES categories(id),
  name        text NOT NULL,                    -- «Зевс»
  word        text NOT NULL DEFAULT '',         -- «Матрас» — для полного названия
  path        text NOT NULL UNIQUE,             -- matrasy/matras-zevs/
  is_active   boolean NOT NULL DEFAULT true,
  -- поля для фильтров (дублируют specs, чтобы искать быстро)
  hardness_top    text,                         -- Мягкий / Средней жесткости / Жесткий
  hardness_bottom text,
  is_two_sided    boolean,                      -- «Категория: Двухсторонний»
  has_springs     boolean,                      -- «Категория: Пружины»
  height_cm       numeric(5,1),
  specs       jsonb NOT NULL DEFAULT '{}',      -- все характеристики из листа «Х_…» как есть
  -- распродажа: штучные позиции
  base_product_id text REFERENCES products(id), -- обычная модель, если это позиция распродажи
  regular_price   int,                          -- обычная цена этого размера (для зачёркнутой цены)
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX products_category_idx ON products(category_id) WHERE is_active;

CREATE TABLE product_variants (                  -- размер = ширина × длина, своя цена
  product_id  text NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  width_cm    int  NOT NULL,
  length_cm   int  NOT NULL,
  price       int  NOT NULL CHECK (price > 0),  -- рубли, целые
  in_stock    int,                              -- для распродажи: сколько штук (NULL — под заказ)
  PRIMARY KEY (product_id, width_cm, length_cm)
);

CREATE TABLE product_images (
  id          bigserial PRIMARY KEY,
  product_id  text NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  file        text NOT NULL,                    -- img/products/matras-zevs.jpg или ссылка на хранилище
  is_main     boolean NOT NULL DEFAULT false,
  sort        int NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX product_images_main ON product_images(product_id) WHERE is_main;

CREATE TABLE promotions (                        -- скидка на товар на период [starts_on, ends_on)
  id          bigserial PRIMARY KEY,
  product_id  text NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  percent     int  NOT NULL CHECK (percent BETWEEN 1 AND 90),
  starts_on   date NOT NULL,
  ends_on     date NOT NULL CHECK (ends_on > starts_on),
  is_active   boolean NOT NULL DEFAULT true
);
CREATE INDEX promotions_active_idx ON promotions(product_id, starts_on, ends_on) WHERE is_active;
-- Цена со скидкой = ceil(price * (1 - percent/100) / 10) * 10 — так же, как TMVO_PRICE.priceOf в api.js

------------------------------------------------------------------------------------------
-- ЗАКАЗЫ
------------------------------------------------------------------------------------------
CREATE TYPE order_type   AS ENUM ('quick', 'full');
CREATE TYPE order_status AS ENUM ('draft', 'new', 'in_work', 'awaiting_payment', 'paid', 'delivery', 'done', 'canceled');

CREATE SEQUENCE order_number_seq START 1001;

CREATE TABLE orders (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  number          int  NOT NULL UNIQUE DEFAULT nextval('order_number_seq'),
  token           text NOT NULL,                -- случайная строка ≥ 32 символов: доступ покупателя к странице заказа
  type            order_type   NOT NULL,
  status          order_status NOT NULL,
  source          text,                         -- product / list / cart / checkout
  customer_phone  text NOT NULL,                -- +7XXXXXXXXXX
  customer_name   text NOT NULL DEFAULT '',
  customer_email  text NOT NULL DEFAULT '',
  customer_comment text NOT NULL DEFAULT '',
  delivery_method text,                         -- courier / pickup
  delivery_city   text, delivery_street text, delivery_floor text, delivery_flat text,
  delivery_lift   boolean,
  payment_method  text,                         -- cash / card_courier / sbp / bank_card / invoice
  payment_status  text NOT NULL DEFAULT 'not_paid',   -- not_paid / pending / paid / refunded
  total           int  NOT NULL DEFAULT 0,
  offer_accepted  boolean NOT NULL DEFAULT false,
  marketing       boolean NOT NULL DEFAULT false,
  manager_id      int,
  manager_comment text NOT NULL DEFAULT '',
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX orders_status_idx ON orders(status, created_at DESC);
CREATE INDEX orders_phone_idx  ON orders(customer_phone);

CREATE TABLE order_items (                       -- цена фиксируется на момент заказа
  order_id    uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  line        int  NOT NULL,
  product_id  text REFERENCES products(id),
  name        text NOT NULL,
  width_cm    int  NOT NULL, length_cm int NOT NULL,
  qty         int  NOT NULL CHECK (qty BETWEEN 1 AND 20),
  price       int  NOT NULL,                    -- цена за штуку с учётом скидки
  old_price   int,                              -- цена без скидки, если была скидка
  discount_pct int,
  sum         int  NOT NULL,
  PRIMARY KEY (order_id, line)
);

CREATE TABLE order_history (
  id        bigserial PRIMARY KEY,
  order_id  uuid NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  at        timestamptz NOT NULL DEFAULT now(),
  actor     text NOT NULL,                      -- site / manager:<логин> / yookassa
  text      text NOT NULL
);

CREATE TABLE callbacks (                         -- «Заказать звонок», «Остались вопросы»
  id          bigserial PRIMARY KEY,
  phone       text NOT NULL,
  name        text NOT NULL DEFAULT '',
  topic       text NOT NULL DEFAULT '',
  status      text NOT NULL DEFAULT 'new',      -- new / done
  created_at  timestamptz NOT NULL DEFAULT now()
);

-- Журнал согласий (152-ФЗ). Записи не изменяются и не удаляются вместе с заказом.
CREATE TABLE consents (
  id              bigserial PRIMARY KEY,
  order_id        uuid REFERENCES orders(id) ON DELETE SET NULL,
  callback_id     bigint REFERENCES callbacks(id) ON DELETE SET NULL,
  phone           text NOT NULL,
  privacy         boolean NOT NULL,
  personal_data   boolean NOT NULL,
  privacy_version text NOT NULL,
  consent_version text NOT NULL,
  form            text NOT NULL,                -- quick / checkout / callback / lead
  ip              inet,
  user_agent      text,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE payments (                          -- этап 3: ЮKassa
  id                  bigserial PRIMARY KEY,
  order_id            uuid NOT NULL REFERENCES orders(id),
  provider            text NOT NULL DEFAULT 'yookassa',
  provider_payment_id text UNIQUE,
  method              text NOT NULL,            -- sbp / bank_card
  amount              int  NOT NULL,
  status              text NOT NULL,            -- pending / succeeded / canceled / refunded
  raw                 jsonb,
  created_at          timestamptz NOT NULL DEFAULT now()
);

------------------------------------------------------------------------------------------
-- АДМИНКА
------------------------------------------------------------------------------------------
CREATE TABLE admin_users (
  id            serial PRIMARY KEY,
  login         text NOT NULL UNIQUE,
  password_hash text NOT NULL,                  -- bcrypt / argon2, никогда не хранить пароль открыто
  name          text NOT NULL DEFAULT '',
  role          text NOT NULL DEFAULT 'manager', -- manager / admin
  is_active     boolean NOT NULL DEFAULT true
);
ALTER TABLE orders ADD CONSTRAINT orders_manager_fk FOREIGN KEY (manager_id) REFERENCES admin_users(id);

CREATE TABLE admin_sessions (
  token       text PRIMARY KEY,
  user_id     int NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
  expires_at  timestamptz NOT NULL
);
