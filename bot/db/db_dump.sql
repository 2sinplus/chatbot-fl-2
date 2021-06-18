--
-- Файл сгенерирован с помощью SQLiteStudio v3.2.1 в Пт июн 18 11:37:59 2021
--
-- Использованная кодировка текста: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Таблица: admins
CREATE TABLE admins (user_id INTEGER NOT NULL UNIQUE);

-- Таблица: castomers
CREATE TABLE castomers (user_id INTEGER NOT NULL, name CHAR NOT NULL, phone_number CHAR, address CHAR, delivery_time CHAR, payment_method CHAR);

-- Таблица: products
CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, manufacturer CHAR NOT NULL, taste CHAR NOT NULL, number_of_puffs INTEGER NOT NULL, amount INTEGER);

-- Таблица: products_stack
CREATE TABLE products_stack (user_id INTEGER NOT NULL, manufacturer CHAR NOT NULL, taste CHAR, number_of_puffs INTEGER, amount INTEGER);

-- Таблица: shopping_cart
CREATE TABLE shopping_cart (user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, count INTEGER NOT NULL);

-- Таблица: users
CREATE TABLE users (user_id INTEGER NOT NULL UNIQUE);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
