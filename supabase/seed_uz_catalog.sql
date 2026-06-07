-- V44 + Seed Data for uz_product_catalog
-- Run this in Supabase SQL Editor after migration V44

-- 1. Create table (idempotent)
CREATE TABLE IF NOT EXISTS uz_product_catalog (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category            VARCHAR(100) NOT NULL,
    subcategory         VARCHAR(100),
    product_name        TEXT NOT NULL,
    brand               VARCHAR(100),
    price_uzs           NUMERIC NOT NULL,
    price_uzs_original  NUMERIC,
    specs               JSONB DEFAULT '{}',
    rating              NUMERIC DEFAULT 0,
    reviews_count       INTEGER DEFAULT 0,
    url                 TEXT,
    category_url        TEXT,
    confidence          NUMERIC DEFAULT 0.5,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uz_catalog_category ON uz_product_catalog(category);
CREATE INDEX IF NOT EXISTS idx_uz_catalog_brand ON uz_product_catalog(brand);
GRANT SELECT, INSERT, UPDATE ON uz_product_catalog TO anon, authenticated, service_role;

-- 2. Seed data: Uzum Market electronics pricing
INSERT INTO uz_product_catalog (category, subcategory, product_name, brand, price_uzs, price_uzs_original, specs, rating, reviews_count, url, category_url, confidence, notes)
VALUES

-- ========== LED LAMPS ==========
('Lighting', 'LED Bulbs', 'LED лампочка E27 9W 220V светодиодная лампа', 'Unbranded', 15000, 18000,
 '{"wattage": "9W", "base": "E27", "voltage": "220V", "color_temp": "6500K", "lifespan": "20000h"}',
 4.0, 15, 'https://uzum.uz/ru/product/led-lampochka-e27-2507923', 'https://uzum.uz/ru/category/svetodiodnye-lampy', 0.6, 'Базовая светодиодная лампа 9W E27. Аналог 60W накаливания.'),

('Lighting', 'LED Bulbs', 'LED лампа E27 12W энергосберегающая', 'Akfa', 15800, 18000,
 '{"wattage": "12W", "base": "E27", "lumens": "960-1200", "voltage": "120-250V", "color_temp": "3000-6500K"}',
 4.2, 30, 'https://uzum.uz/ru/product/led-lampa-akfa-12w-e27-12345', 'https://uzum.uz/ru/category/svetodiodnye-lampy', 0.6, 'Производство Узбекистан (Akfa Lighting).'),

('Lighting', 'LED Bulbs', 'LED лампа A60 15W E27 6500K', 'Unbranded', 22000, 25000,
 '{"wattage": "15W", "base": "E27", "lumens": "1500", "voltage": "220V", "color_temp": "6500K", "lifespan": "30000h"}',
 4.0, 10, 'https://uzum.uz/ru/category/svetodiodnye-lampy', 'https://uzum.uz/ru/category/svetodiodnye-lampy', 0.5, 'Яркая лампа для больших помещений.'),

('Lighting', 'LED Floodlights', 'LED прожектор 50W уличный IP65', 'Unbranded', 85000, 100000,
 '{"wattage": "50W", "ip_rating": "IP65", "material": "Aluminum", "lumens": "5000", "beam_angle": "120°"}',
 4.3, 25, 'https://uzum.uz/ru/category/svetodiodnye-lampy', 'https://uzum.uz/ru/category/svetodiodnye-lampy', 0.5, 'Уличный светодиодный прожектор для фасада/двора.'),

('Lighting', 'LED Panels', 'LED панель 600x600mm 48W', 'Unbranded', 120000, 140000,
 '{"wattage": "48W", "size": "600x600mm", "lumens": "4800", "color_temp": "4000K", "ip_rating": "IP20"}',
 4.0, 8, 'https://uzum.uz/ru/category/svetodiodnye-lampy', 'https://uzum.uz/ru/category/svetodiodnye-lampy', 0.5, 'Офисная светодиодная панель.'),

('Lighting', 'LED Strip Lights', 'RGB LED лента 5M 5050 SMD с пультом', 'Unbranded', 35000, 45000,
 '{"led_type": "5050 SMD", "length": "5M", "voltage": "DC 12V", "color": "RGB", "control": "IR remote"}',
 4.1, 40, 'https://uzum.uz/ru/category/svetodiodnye-lampy', 'https://uzum.uz/ru/category/svetodiodnye-lampy', 0.6, 'Светодиодная лента с пультом ДУ и блоком питания.'),

-- ========== POWER BANKS ==========
('Electronics', 'Power Banks', 'Внешний аккумулятор 20000 мА/ч 22.5W с быстрой зарядкой', 'Unbranded', 115000, 119500,
 '{"capacity": "20000mAh", "output": "22.5W PD", "input": "USB-C", "cells": "Li-polymer", "features": "digital display, dual USB-A + USB-C"}',
 4.5, 149, 'https://uzum.uz/ru/shop/powerbank', 'https://uzum.uz/ru/shop/powerbank', 0.6, 'Распродажа. Популярный power bank на Uzum.'),

('Electronics', 'Power Banks', 'Внешний аккумулятор 20000mAh 66W с быстрой зарядкой', 'Unbranded', 169750, 175000,
 '{"capacity": "20000mAh", "output": "66W PD", "input": "USB-C 30W", "cells": "Li-polymer", "features": "3 outputs, LED display"}',
 4.7, 72, 'https://uzum.uz/ru/shop/powerbank', 'https://uzum.uz/ru/shop/powerbank', 0.6, 'Мощный 66W PD. Заряжает ноутбук.'),

('Electronics', 'Power Banks', 'Внешний аккумулятор Xiaomi 20000mAh 18W-50W', 'Xiaomi', 172757, 178100,
 '{"capacity": "20000mAh", "output": "50W", "cells": "Li-ion", "features": "USB-C bidirectional, 2x USB-A"}',
 4.6, 76, 'https://uzum.uz/ru/shop/powerbank', 'https://uzum.uz/ru/shop/powerbank', 0.7, 'Оригинальный Xiaomi power bank. Гарантия.'),

('Electronics', 'Power Banks', 'Внешний аккумулятор 20000mA 22.5W + 4 кабеля в комплекте', 'Unbranded', 115430, 119000,
 '{"capacity": "20000mAh", "output": "22.5W", "features": "4 cables included, digital display"}',
 4.6, 84, 'https://uzum.uz/ru/shop/powerbank', 'https://uzum.uz/ru/shop/powerbank', 0.6, 'Комплект с 4 кабелями (Type-C, Lightning, Micro USB).'),

('Electronics', 'Power Banks', 'Внешний аккумулятор 10000mAh 22.5W компактный', 'Unbranded', 75000, 85000,
 '{"capacity": "10000mAh", "output": "22.5W PD", "cells": "Li-polymer", "features": "ultra-slim, digital display"}',
 4.4, 95, 'https://uzum.uz/ru/shop/powerbank', 'https://uzum.uz/ru/shop/powerbank', 0.6, 'Компактный power bank для ежедневного ношения.'),

-- ========== TWS EARPHONES ==========
('Electronics', 'TWS Earphones', 'Беспроводные наушники TWS Bluetooth 5.3', 'Unbranded', 48000, 60000,
 '{"bluetooth": "5.3", "driver": "10mm", "battery_earbud": "25mAh", "battery_case": "180mAh", "playtime": "3-5h", "charging": "Type-C"}',
 4.2, 200, 'https://uzum.uz/ru/product/besprovodnye-naushniki-tws-1149160', 'https://uzum.uz/ru/category/naushniki-redmi', 0.6, 'Базовые TWS наушники. Доступная цена.'),

('Electronics', 'TWS Earphones', 'Redmi Buds 4 Active', 'Xiaomi', 85000, 100000,
 '{"bluetooth": "5.3", "driver": "12mm", "battery_earbud": "40mAh", "battery_case": "400mAh", "playtime": "5-7h", "waterproof": "IPX4", "charging": "Type-C"}',
 4.5, 500, 'https://uzum.uz/ru/category/naushniki-redmi', 'https://uzum.uz/ru/category/naushniki-redmi', 0.7, 'Оригинальные Redmi. Популярная модель.'),

('Electronics', 'TWS Earphones', 'Lenovo LP75 TWS наушники', 'Lenovo', 60000, 75000,
 '{"bluetooth": "5.3", "driver": "13mm", "battery_earbud": "35mAh", "battery_case": "300mAh", "playtime": "4-6h", "charging": "Type-C"}',
 4.3, 150, 'https://uzum.uz/ru/category/naushniki-redmi', 'https://uzum.uz/ru/category/naushniki-redmi', 0.6, 'Lenovo LP75 с LED дисплеем на кейсе.'),

('Electronics', 'TWS Earphones', 'Huawei FreeBuds SE 2', 'Huawei', 496000, 550000,
 '{"bluetooth": "5.2", "driver": "10mm", "anc": "no", "battery_earbud": "41mAh", "battery_case": "410mAh", "playtime": "6-9h", "waterproof": "IPX4"}',
 4.6, 120, 'https://uzum.uz/ru/category/naushniki-redmi', 'https://uzum.uz/ru/category/naushniki-redmi', 0.7, 'Оригинальные Huawei FreeBuds SE 2. Хорошее качество звука.'),

('Electronics', 'TWS Earphones', 'Samsung Galaxy Buds3 Pro', 'Samsung', 2000000, 2300000,
 '{"bluetooth": "5.3", "anc": "Adaptive ANC", "driver": "dual", "battery_earbud": "58mAh", "battery_case": "500mAh", "playtime": "8h", "waterproof": "IP57"}',
 4.7, 80, 'https://uzum.uz/ru/category/naushniki-samsung', 'https://uzum.uz/ru/category/naushniki-samsung', 0.7, 'Премиум TWS с адаптивным шумоподавлением.'),

-- ========== PHONE CABLES ==========
('Electronics', 'Phone Cables', 'Зарядный кабель USB Type-C/Lightning 1м', 'Triumph', 25000, 35000,
 '{"connector": "USB to Type-C/Lightning/Micro", "power": "3A", "length": "1M", "material": "PVC"}',
 4.3, 300, 'https://uzum.uz/ru/product/zaryadnyj-kabel-usb-type-clightning-695329', 'https://uzum.uz/ru/category/zaryadnye-kabeli', 0.6, 'Универсальный кабель 3-в-1.'),

('Electronics', 'Phone Cables', 'Кабель USB-C to Lightning 1м для iPhone быстрая зарядка', 'Unbranded', 35000, 55000,
 '{"connector": "USB-C to Lightning", "power": "20W PD", "length": "1M", "material": "braided", "data": "USB 2.0"}',
 4.4, 180, 'https://uzum.uz/ru/product/kabel-usbc-to-2027225', 'https://uzum.uz/ru/category/zaryadnye-kabeli', 0.6, 'MFi сертифицированный кабель для iPhone.'),

('Electronics', 'Phone Cables', 'Кабель USB Type-C to Type-C 60W 1M', 'Unbranded', 20000, 30000,
 '{"connector": "USB-C to USB-C", "power": "60W PD", "length": "1M", "material": "nylon braided"}',
 4.2, 220, 'https://uzum.uz/ru/category/zaryadnye-kabeli', 'https://uzum.uz/ru/category/zaryadnye-kabeli', 0.6, 'Прочный оплетенный кабель Type-C.'),

('Electronics', 'Phone Cables', 'Кабель Baseus Type-C to Lightning 1.2M', 'Baseus', 97000, 120000,
 '{"connector": "Type-C to Lightning", "power": "20W PD", "length": "1.2M", "material": "nylon braided"}',
 4.5, 60, 'https://uzum.uz/ru/product/kabel-baseus-typec-lightning-12345', 'https://uzum.uz/ru/category/zaryadnye-kabeli', 0.7, 'Брендовый кабель Baseus. Высокое качество.'),

('Electronics', 'Phone Cables', 'Кабель USB-C 100W 2M быстрая зарядка для ноутбука', 'Unbranded', 45000, 60000,
 '{"connector": "USB-C to USB-C", "power": "100W PD 3.0", "length": "2M", "material": "nylon braided + aluminum", "data": "USB 3.1 Gen2 10Gbps"}',
 4.3, 90, 'https://uzum.uz/ru/category/zaryadnye-kabeli', 'https://uzum.uz/ru/category/zaryadnye-kabeli', 0.5, 'Кабель 100W для зарядки ноутбуков MacBook и др.'),

-- ========== SMART WATCHES ==========
('Electronics', 'Smart Watches', 'Умные часы Smart часы Bluetooth звонки', 'Unbranded', 224000, 280000,
 '{"display": "1.85 inch TFT", "features": "BT call, heart rate, SpO2, sleep, 100+ sports", "battery": "300mAh, 7-14 days", "waterproof": "IP68"}',
 4.6, 117, 'https://uzum.uz/ru/product/umnye-chasy-smart-belyj---5-2151370', 'https://uzum.uz/ru/category/umnye-chasy-13381', 0.6, 'Популярные смарт-часы. Многоцветный выбор.'),

('Electronics', 'Smart Watches', 'Базовые умные часы фитнес-браслет', 'Unbranded', 79000, 100000,
 '{"display": "1.3 inch TFT", "features": "heart rate, step counter, sleep monitor", "battery": "200mAh, 7 days", "waterproof": "IP67"}',
 4.0, 50, 'https://uzum.uz/ru/category/umnye-chasy-13381', 'https://uzum.uz/ru/category/umnye-chasy-13381', 0.6, 'Бюджетный фитнес-браслет с базовыми функциями.'),

('Electronics', 'Smart Watches', 'Xiaomi Smart Band 9', 'Xiaomi', 339000, 380000,
 '{"display": "1.62 inch AMOLED", "features": "heart rate, SpO2, sleep, 150+ sports, BT call", "battery": "14 days", "waterproof": "5ATM"}',
 4.7, 300, 'https://uzum.uz/ru/category/umnye-chasy-13381', 'https://uzum.uz/ru/category/umnye-chasy-13381', 0.7, 'Оригинальный Xiaomi Smart Band 9. Очень популярен.'),

('Electronics', 'Smart Watches', 'Samsung Galaxy Watch 7 44mm', 'Samsung', 2565000, 3000000,
 '{"display": "1.47 inch Super AMOLED", "features": "ECG, blood pressure, GPS, body composition", "battery": "425mAh, 40h", "waterproof": "5ATM", "os": "Wear OS"}',
 4.6, 90, 'https://uzum.uz/ru/category/umnye-chasy-13381', 'https://uzum.uz/ru/category/umnye-chasy-13381', 0.7, 'Премиум смарт-часы Samsung.'),

('Electronics', 'Smart Watches', 'Apple Watch SE 2023 40mm', 'Apple', 4200000, 4500000,
 '{"display": "1.53 inch OLED", "features": "ECG, fall detection, GPS, workout tracking", "battery": "18h", "waterproof": "WR50", "os": "watchOS"}',
 4.8, 50, 'https://uzum.uz/ru/category/umnye-chasy-13381', 'https://uzum.uz/ru/category/umnye-chasy-13381', 0.7, 'Оригинальные Apple Watch SE.'),

-- ========== BLUETOOTH SPEAKERS ==========
('Electronics', 'Bluetooth Speakers', 'Портативная Bluetooth колонка Mi Portable 16W', 'Xiaomi', 260000, 300000,
 '{"power": "16W", "bluetooth": "5.0", "battery": "2200mAh", "playtime": "8h", "waterproof": "IPX5", "charging": "Type-C"}',
 4.5, 200, 'https://uzum.uz/ru/product/portativnaya-besprovodnaya-kolonka-927370', 'https://uzum.uz/ru/category/portativnye-kolonki', 0.7, 'Оригинальная Xiaomi колонка.'),

('Electronics', 'Bluetooth Speakers', 'Портативная Bluetooth колонка 20W стерео', 'Unbranded', 95000, 120000,
 '{"power": "20W (2x10W)", "bluetooth": "5.3", "battery": "3600mAh", "playtime": "8-12h", "features": "TF card, FM radio, TWS"}',
 4.3, 150, 'https://uzum.uz/ru/product/portativnaya-bluetooth-kolonka-1925261', 'https://uzum.uz/ru/category/portativnye-kolonki', 0.6, 'Бюджетная колонка с FM радио и картой памяти.'),

('Electronics', 'Bluetooth Speakers', 'JBL Go 3 портативная Bluetooth колонка', 'JBL', 290000, 350000,
 '{"power": "4.2W", "bluetooth": "5.1", "battery": "2.5h", "waterproof": "IP67", "features": "speakerphone"}',
 4.6, 180, 'https://uzum.uz/ru/category/portativnye-kolonki', 'https://uzum.uz/ru/category/portativnye-kolonki', 0.7, 'Оригинальная JBL. Компактная, защищенная.'),

('Electronics', 'Bluetooth Speakers', 'JBL Charge 5 портативная колонка 30W', 'JBL', 1350000, 1500000,
 '{"power": "30W", "bluetooth": "5.1", "battery": "7500mAh, 20h", "waterproof": "IP67", "features": "power bank function, speakerphone"}',
 4.7, 60, 'https://uzum.uz/ru/category/portativnye-kolonki', 'https://uzum.uz/ru/category/portativnye-kolonki', 0.7, 'Премиум JBL колонка + power bank.'),

('Electronics', 'Bluetooth Speakers', 'Marshall Emberton II портативная колонка', 'Marshall', 1440000, 1700000,
 '{"power": "20W", "bluetooth": "5.2", "battery": "30h", "waterproof": "IP67", "features": "multi-directional sound, stack mode"}',
 4.8, 30, 'https://uzum.uz/ru/category/portativnye-kolonki', 'https://uzum.uz/ru/category/portativnye-kolonki', 0.7, 'Премиум дизайн Marshall.'),

-- ========== ADDITIONAL: CHARGERS & ADAPTERS ==========
('Electronics', 'Chargers', 'Зарядное устройство USB Type-C 20W PD быстрая зарядка', 'Unbranded', 35000, 45000,
 '{"power": "20W PD", "port": "USB-C", "features": "GaN, fast charge iPhone/Samsung", "size": "compact"}',
 4.3, 100, 'https://uzum.uz/ru/category/zaryadnye-ustrojstva', 'https://uzum.uz/ru/category/zaryadnye-ustrojstva', 0.6, 'Компактное зарядное устройство 20W.'),

('Electronics', 'Chargers', 'Зарядное устройство Samsung 25W PD адаптер', 'Samsung', 149000, 170000,
 '{"power": "25W PD", "port": "USB-C", "features": "Samsung Super Fast Charging"}',
 4.5, 80, 'https://uzum.uz/ru/category/zaryadnye-ustrojstva', 'https://uzum.uz/ru/category/zaryadnye-ustrojstva', 0.7, 'Оригинальный Samsung адаптер.'),

('Electronics', 'Chargers', 'Зарядное устройство GaN 65W 3 порта', 'Unbranded', 120000, 150000,
 '{"power": "65W total", "ports": "2x USB-C + 1x USB-A", "features": "GaN tech, PD 3.0, QC 4.0", "compatible": "MacBook, iPhone, Samsung"}',
 4.4, 40, 'https://uzum.uz/ru/category/zaryadnye-ustrojstva', 'https://uzum.uz/ru/category/zaryadnye-ustrojstva', 0.5, 'GaN зарядка для ноутбука и телефона одновременно.');
