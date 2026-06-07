-- V51: Complete countries reference (all UN members + territories)
-- Source: UN M49, ISO 3166-1, World Bank, CBU trade statistics

INSERT INTO countries (code, name_uz, name_en, name_ru, currency, region, trade_bloc, has_preferential_trade, import_share_pct)
VALUES
    ('UZ', 'O''zbekiston', 'Uzbekistan', 'Узбекистан', 'UZS', 'Central Asia', null, false, 0),
    ('KZ', 'Qozog''iston', 'Kazakhstan', 'Казахстан', 'KZT', 'Central Asia', 'EAEU', true, 7.8),
    ('KG', 'Qirg''iziston', 'Kyrgyzstan', 'Киргизия', 'KGS', 'Central Asia', 'EAEU', true, 0.9),
    ('TJ', 'Tojikiston', 'Tajikistan', 'Таджикистан', 'TJS', 'Central Asia', null, false, 0.2),
    ('TM', 'Turkmaniston', 'Turkmenistan', 'Туркменистан', 'TMT', 'Central Asia', null, true, 2.9),
    ('CN', 'Xitoy', 'China', 'Китай', 'CNY', 'East Asia', null, false, 29.2),
    ('JP', 'Yaponiya', 'Japan', 'Япония', 'JPY', 'East Asia', null, false, 0.9),
    ('KR', 'Janubiy Koreya', 'South Korea', 'Южная Корея', 'KRW', 'East Asia', null, false, 5.3),
    ('KP', 'Shimoliy Koreya', 'North Korea', 'Северная Корея', 'KPW', 'East Asia', null, false, 0),
    ('MN', 'Mo''g''uliston', 'Mongolia', 'Монголия', 'MNT', 'East Asia', null, false, 0.1),
    ('TW', 'Tayvan', 'Taiwan', 'Тайвань', 'TWD', 'East Asia', null, false, 0.3),
    ('HK', 'Gonkong', 'Hong Kong', 'Гонконг', 'HKD', 'East Asia', null, false, 0.4),
    ('MO', 'Makao', 'Macau', 'Макао', 'MOP', 'East Asia', null, false, 0),
    ('ID', 'Indoneziya', 'Indonesia', 'Индонезия', 'IDR', 'Southeast Asia', null, false, 0.4),
    ('MY', 'Malayziya', 'Malaysia', 'Малайзия', 'MYR', 'Southeast Asia', null, false, 0.5),
    ('PH', 'Filippin', 'Philippines', 'Филиппины', 'PHP', 'Southeast Asia', null, false, 0.2),
    ('SG', 'Singapur', 'Singapore', 'Сингапур', 'SGD', 'Southeast Asia', null, false, 0.5),
    ('TH', 'Tailand', 'Thailand', 'Таиланд', 'THB', 'Southeast Asia', null, false, 0.6),
    ('VN', 'Vyetnam', 'Vietnam', 'Вьетнам', 'VND', 'Southeast Asia', null, false, 0.7),
    ('BN', 'Bruney', 'Brunei', 'Бруней', 'BND', 'Southeast Asia', null, false, 0),
    ('KH', 'Kambodja', 'Cambodia', 'Камбоджа', 'KHR', 'Southeast Asia', null, false, 0.1),
    ('LA', 'Laos', 'Laos', 'Лаос', 'LAK', 'Southeast Asia', null, false, 0),
    ('MM', 'Myanma', 'Myanmar', 'Мьянма', 'MMK', 'Southeast Asia', null, false, 0.1),
    ('IN', 'Hindiston', 'India', 'Индия', 'INR', 'South Asia', null, false, 2.4),
    ('PK', 'Pokiston', 'Pakistan', 'Пакистан', 'PKR', 'South Asia', null, false, 0.4),
    ('BD', 'Bangladesh', 'Bangladesh', 'Бангладеш', 'BDT', 'South Asia', null, false, 0.5),
    ('LK', 'Shri-Lanka', 'Sri Lanka', 'Шри-Ланка', 'LKR', 'South Asia', null, false, 0.1),
    ('NP', 'Nepal', 'Nepal', 'Непал', 'NPR', 'South Asia', null, false, 0),
    ('BT', 'Butan', 'Bhutan', 'Бутан', 'BTN', 'South Asia', null, false, 0),
    ('MV', 'Maldiv orollari', 'Maldives', 'Мальдивы', 'MVR', 'South Asia', null, false, 0),
    ('AF', 'Afg''oniston', 'Afghanistan', 'Афганистан', 'AFN', 'South Asia', null, false, 0.2),
    ('TR', 'Turkiya', 'Turkey', 'Турция', 'TRY', 'Middle East', null, true, 4.8),
    ('IR', 'Eron', 'Iran', 'Иран', 'IRR', 'Middle East', null, false, 0.9),
    ('AE', 'Birlashgan Arab Amirliklari', 'United Arab Emirates', 'ОАЭ', 'AED', 'Middle East', null, false, 0.8),
    ('SA', 'Saudiya Arabistoni', 'Saudi Arabia', 'Саудовская Аравия', 'SAR', 'Middle East', null, false, 0.5),
    ('IQ', 'Iroq', 'Iraq', 'Ирак', 'IQD', 'Middle East', null, false, 0.1),
    ('IL', 'Isroil', 'Israel', 'Израиль', 'ILS', 'Middle East', null, false, 0.3),
    ('JO', 'Iordaniya', 'Jordan', 'Иордания', 'JOD', 'Middle East', null, false, 0.1),
    ('KW', 'Quvayt', 'Kuwait', 'Кувейт', 'KWD', 'Middle East', null, false, 0.1),
    ('LB', 'Livan', 'Lebanon', 'Ливан', 'LBP', 'Middle East', null, false, 0),
    ('OM', 'Ummon', 'Oman', 'Оман', 'OMR', 'Middle East', null, false, 0.1),
    ('QA', 'Qatar', 'Qatar', 'Катар', 'QAR', 'Middle East', null, false, 0.1),
    ('SY', 'Suriya', 'Syria', 'Сирия', 'SYP', 'Middle East', null, false, 0),
    ('YE', 'Yaman', 'Yemen', 'Йемен', 'YER', 'Middle East', null, false, 0),
    ('PS', 'Falastin', 'Palestine', 'Палестина', 'ILS', 'Middle East', null, false, 0),
    ('BH', 'Bahrayn', 'Bahrain', 'Бахрейн', 'BHD', 'Middle East', null, false, 0),
    ('AZ', 'Ozarbayjon', 'Azerbaijan', 'Азербайджан', 'AZN', 'Caucasus', null, false, 0.3),
    ('AM', 'Armaniston', 'Armenia', 'Армения', 'AMD', 'Caucasus', 'EAEU', true, 0.3),
    ('GE', 'Gruziya', 'Georgia', 'Грузия', 'GEL', 'Caucasus', null, false, 0.6),
    ('RU', 'Rossiya', 'Russia', 'Россия', 'RUB', 'Europe/East', 'EAEU', true, 21.8),
    ('BY', 'Belarus', 'Belarus', 'Беларусь', 'BYN', 'Europe/East', 'EAEU', true, 1.5),
    ('UA', 'Ukraina', 'Ukraine', 'Украина', 'UAH', 'Europe/East', null, false, 0.4),
    ('MD', 'Moldova', 'Moldova', 'Молдова', 'MDL', 'Europe/East', null, false, 0.1),
    ('DE', 'Germaniya', 'Germany', 'Германия', 'EUR', 'Europe', 'EU', false, 2.8),
    ('FR', 'Fransiya', 'France', 'Франция', 'EUR', 'Europe', 'EU', false, 0.9),
    ('IT', 'Italiya', 'Italy', 'Италия', 'EUR', 'Europe', 'EU', false, 1.0),
    ('GB', 'Buyuk Britaniya', 'United Kingdom', 'Великобритания', 'GBP', 'Europe', null, false, 0.5),
    ('ES', 'Ispaniya', 'Spain', 'Испания', 'EUR', 'Europe', 'EU', false, 0.4),
    ('NL', 'Niderlandiya', 'Netherlands', 'Нидерланды', 'EUR', 'Europe', 'EU', false, 0.7),
    ('PL', 'Polsha', 'Poland', 'Польша', 'PLN', 'Europe', 'EU', false, 0.8),
    ('CZ', 'Chexiya', 'Czech Republic', 'Чехия', 'CZK', 'Europe', 'EU', false, 0.8),
    ('AT', 'Avstriya', 'Austria', 'Австрия', 'EUR', 'Europe', 'EU', false, 0.5),
    ('CH', 'Shveytsariya', 'Switzerland', 'Швейцария', 'CHF', 'Europe', null, false, 0.6),
    ('SE', 'Shvetsiya', 'Sweden', 'Швеция', 'SEK', 'Europe', 'EU', false, 0.3),
    ('BE', 'Belgiya', 'Belgium', 'Бельгия', 'EUR', 'Europe', 'EU', false, 0.4),
    ('DK', 'Daniya', 'Denmark', 'Дания', 'DKK', 'Europe', 'EU', false, 0.2),
    ('FI', 'Finlandiya', 'Finland', 'Финляндия', 'EUR', 'Europe', 'EU', false, 0.2),
    ('NO', 'Norvegiya', 'Norway', 'Норвегия', 'NOK', 'Europe', null, false, 0.1),
    ('LV', 'Latviya', 'Latvia', 'Латвия', 'EUR', 'Europe', 'EU', false, 1.2),
    ('LT', 'Litva', 'Lithuania', 'Литва', 'EUR', 'Europe', 'EU', false, 0.3),
    ('EE', 'Estoniya', 'Estonia', 'Эстония', 'EUR', 'Europe', 'EU', false, 0.1),
    ('RO', 'Ruminiya', 'Romania', 'Румыния', 'RON', 'Europe', 'EU', false, 0.2),
    ('BG', 'Bolgariya', 'Bulgaria', 'Болгария', 'BGN', 'Europe', 'EU', false, 0.2),
    ('HU', 'Vengriya', 'Hungary', 'Венгрия', 'HUF', 'Europe', 'EU', false, 0.3),
    ('SK', 'Slovakiya', 'Slovakia', 'Словакия', 'EUR', 'Europe', 'EU', false, 0.2),
    ('SI', 'Sloveniya', 'Slovenia', 'Словения', 'EUR', 'Europe', 'EU', false, 0.1),
    ('GR', 'Gretsiya', 'Greece', 'Греция', 'EUR', 'Europe', 'EU', false, 0.1),
    ('PT', 'Portugaliya', 'Portugal', 'Португалия', 'EUR', 'Europe', 'EU', false, 0.1),
    ('IE', 'Irlandiya', 'Ireland', 'Ирландия', 'EUR', 'Europe', 'EU', false, 0.1),
    ('HR', 'Xorvatiya', 'Croatia', 'Хорватия', 'EUR', 'Europe', 'EU', false, 0.1),
    ('LU', 'Lyuksemburg', 'Luxembourg', 'Люксембург', 'EUR', 'Europe', 'EU', false, 0),
    ('CY', 'Kipr', 'Cyprus', 'Кипр', 'EUR', 'Europe', 'EU', false, 0),
    ('MT', 'Malta', 'Malta', 'Мальта', 'EUR', 'Europe', 'EU', false, 0),
    ('US', 'Amerika Qo''shma Shtatlari', 'United States', 'США', 'USD', 'North America', null, false, 1.3),
    ('CA', 'Kanada', 'Canada', 'Канада', 'CAD', 'North America', null, false, 0.3),
    ('MX', 'Meksika', 'Mexico', 'Мексика', 'MXN', 'North America', null, false, 0.1),
    ('BR', 'Braziliya', 'Brazil', 'Бразилия', 'BRL', 'South America', null, false, 0.4),
    ('AR', 'Argentina', 'Argentina', 'Аргентина', 'ARS', 'South America', null, false, 0.2),
    ('CL', 'Chili', 'Chile', 'Чили', 'CLP', 'South America', null, false, 0.1),
    ('CO', 'Kolumbiya', 'Colombia', 'Колумбия', 'COP', 'South America', null, false, 0.1),
    ('PE', 'Peru', 'Peru', 'Перу', 'PEN', 'South America', null, false, 0.1),
    ('EC', 'Ekvador', 'Ecuador', 'Эквадор', 'USD', 'South America', null, false, 0),
    ('UY', 'Urugvay', 'Uruguay', 'Уругвай', 'UYU', 'South America', null, false, 0),
    ('PY', 'Paragvay', 'Paraguay', 'Парагвай', 'PYG', 'South America', null, false, 0),
    ('BO', 'Boliviya', 'Bolivia', 'Боливия', 'BOB', 'South America', null, false, 0),
    ('VE', 'Venesuela', 'Venezuela', 'Венесуэла', 'VES', 'South America', null, false, 0),
    ('GY', 'Gayana', 'Guyana', 'Гайана', 'GYD', 'South America', null, false, 0),
    ('SR', 'Surinam', 'Suriname', 'Суринам', 'SRD', 'South America', null, false, 0),
    ('ZA', 'Janubiy Afrika', 'South Africa', 'ЮАР', 'ZAR', 'Africa', null, false, 0.2),
    ('NG', 'Nigeriya', 'Nigeria', 'Нигерия', 'NGN', 'Africa', null, false, 0.1),
    ('EG', 'Misr', 'Egypt', 'Египет', 'EGP', 'Africa', null, false, 0.3),
    ('MA', 'Marokash', 'Morocco', 'Марокко', 'MAD', 'Africa', null, false, 0.1),
    ('DZ', 'Jazoir', 'Algeria', 'Алжир', 'DZD', 'Africa', null, false, 0.1),
    ('KE', 'Keniya', 'Kenya', 'Кения', 'KES', 'Africa', null, false, 0),
    ('ET', 'Efiopiya', 'Ethiopia', 'Эфиопия', 'ETB', 'Africa', null, false, 0),
    ('GH', 'Gana', 'Ghana', 'Гана', 'GHS', 'Africa', null, false, 0),
    ('TZ', 'Tanzaniya', 'Tanzania', 'Танзания', 'TZS', 'Africa', null, false, 0),
    ('AO', 'Angola', 'Angola', 'Ангола', 'AOA', 'Africa', null, false, 0),
    ('CM', 'Kamerun', 'Cameroon', 'Камерун', 'XAF', 'Africa', null, false, 0),
    ('CI', 'Kot-d''Ivuar', 'Cote d''Ivoire', 'Кот-д''Ивуар', 'XOF', 'Africa', null, false, 0),
    ('SD', 'Sudan', 'Sudan', 'Судан', 'SDG', 'Africa', null, false, 0),
    ('SS', 'Janubiy Sudan', 'South Sudan', 'Южный Судан', 'SSP', 'Africa', null, false, 0),
    ('LY', 'Liviya', 'Libya', 'Ливия', 'LYD', 'Africa', null, false, 0.1),
    ('TN', 'Tunis', 'Tunisia', 'Тунис', 'TND', 'Africa', null, false, 0.1),
    ('SN', 'Senegal', 'Senegal', 'Сенегал', 'XOF', 'Africa', null, false, 0),
    ('UG', 'Uganda', 'Uganda', 'Уганда', 'UGX', 'Africa', null, false, 0),
    ('ZM', 'Zambiya', 'Zambia', 'Замбия', 'ZMW', 'Africa', null, false, 0),
    ('ZW', 'Zimbabve', 'Zimbabwe', 'Зимбабве', 'ZWL', 'Africa', null, false, 0),
    ('ML', 'Mali', 'Mali', 'Мали', 'XOF', 'Africa', null, false, 0),
    ('BF', 'Burkina-Faso', 'Burkina Faso', 'Буркина-Фасо', 'XOF', 'Africa', null, false, 0),
    ('NE', 'Niger', 'Niger', 'Нигер', 'XOF', 'Africa', null, false, 0),
    ('TD', 'Chad', 'Chad', 'Чад', 'XAF', 'Africa', null, false, 0),
    ('MG', 'Madagaskar', 'Madagascar', 'Мадагаскар', 'MGA', 'Africa', null, false, 0),
    ('MZ', 'Mozambik', 'Mozambique', 'Мозамбик', 'MZN', 'Africa', null, false, 0),
    ('MW', 'Malavi', 'Malawi', 'Малави', 'MWK', 'Africa', null, false, 0),
    ('BW', 'Botsvana', 'Botswana', 'Ботсвана', 'BWP', 'Africa', null, false, 0),
    ('NA', 'Namibiya', 'Namibia', 'Намибия', 'NAD', 'Africa', null, false, 0),
    ('MU', 'Mavrikiy', 'Mauritius', 'Маврикий', 'MUR', 'Africa', null, false, 0),
    ('RW', 'Ruanda', 'Rwanda', 'Руанда', 'RWF', 'Africa', null, false, 0),
    ('BI', 'Burundi', 'Burundi', 'Бурунди', 'BIF', 'Africa', null, false, 0),
    ('GA', 'Gabon', 'Gabon', 'Габон', 'XAF', 'Africa', null, false, 0),
    ('CG', 'Kongo', 'Congo', 'Конго', 'XAF', 'Africa', null, false, 0),
    ('CD', 'Kongo Demokratik Respublikasi', 'DR Congo', 'ДР Конго', 'CDF', 'Africa', null, false, 0),
    ('SL', 'Syerra-Leone', 'Sierra Leone', 'Сьерра-Леоне', 'SLL', 'Africa', null, false, 0),
    ('LR', 'Liberiya', 'Liberia', 'Либерия', 'LRD', 'Africa', null, false, 0),
    ('MR', 'Mavritaniya', 'Mauritania', 'Мавритания', 'MRU', 'Africa', null, false, 0),
    ('GM', 'Gambiya', 'Gambia', 'Гамбия', 'GMD', 'Africa', null, false, 0),
    ('GN', 'Gvineya', 'Guinea', 'Гвинея', 'GNF', 'Africa', null, false, 0),
    ('GW', 'Gvineya-Bisau', 'Guinea-Bissau', 'Гвинея-Бисау', 'XOF', 'Africa', null, false, 0),
    ('TG', 'Togo', 'Togo', 'Того', 'XOF', 'Africa', null, false, 0),
    ('BJ', 'Benin', 'Benin', 'Бенин', 'XOF', 'Africa', null, false, 0),
    ('CF', 'Markaziy Afrika Respublikasi', 'CAR', 'ЦАР', 'XAF', 'Africa', null, false, 0),
    ('GQ', 'Ekvatorial Gvineya', 'Equatorial Guinea', 'Экваториальная Гвинея', 'XAF', 'Africa', null, false, 0),
    ('ER', 'Eritreya', 'Eritrea', 'Эритрея', 'ERN', 'Africa', null, false, 0),
    ('DJ', 'Jibuti', 'Djibouti', 'Джибути', 'DJF', 'Africa', null, false, 0),
    ('SO', 'Somali', 'Somalia', 'Сомали', 'SOS', 'Africa', null, false, 0),
    ('SC', 'Seyshel orollari', 'Seychelles', 'Сейшелы', 'SCR', 'Africa', null, false, 0),
    ('KM', 'Komor orollari', 'Comoros', 'Коморы', 'KMF', 'Africa', null, false, 0),
    ('CV', 'Kabo-Verde', 'Cape Verde', 'Кабо-Верде', 'CVE', 'Africa', null, false, 0),
    ('LS', 'Lesoto', 'Lesotho', 'Лесото', 'LSL', 'Africa', null, false, 0),
    ('SZ', 'Svazilend', 'Eswatini', 'Эсватини', 'SZL', 'Africa', null, false, 0),
    ('ST', 'San-Tome va Prinsipi', 'Sao Tome and Principe', 'Сан-Томе и Принсипи', 'STN', 'Africa', null, false, 0),
    ('AU', 'Avstraliya', 'Australia', 'Австралия', 'AUD', 'Oceania', null, false, 0.2),
    ('NZ', 'Yangi Zelandiya', 'New Zealand', 'Новая Зеландия', 'NZD', 'Oceania', null, false, 0.1),
    ('FJ', 'Fiji', 'Fiji', 'Фиджи', 'FJD', 'Oceania', null, false, 0),
    ('PG', 'Papua-Yangi Gvineya', 'Papua New Guinea', 'Папуа-Новая Гвинея', 'PGK', 'Oceania', null, false, 0),
    ('SB', 'Solomon orollari', 'Solomon Islands', 'Соломоновы Острова', 'SBD', 'Oceania', null, false, 0),
    ('WS', 'Samoa', 'Samoa', 'Самоа', 'WST', 'Oceania', null, false, 0),
    ('VU', 'Vanuatu', 'Vanuatu', 'Вануату', 'VUV', 'Oceania', null, false, 0),
    ('TO', 'Tonga', 'Tonga', 'Тонга', 'TOP', 'Oceania', null, false, 0),
    ('MH', 'Marshall orollari', 'Marshall Islands', 'Маршалловы Острова', 'USD', 'Oceania', null, false, 0),
    ('FM', 'Mikroneziya', 'Micronesia', 'Микронезия', 'USD', 'Oceania', null, false, 0),
    ('PW', 'Palau', 'Palau', 'Палау', 'USD', 'Oceania', null, false, 0),
    ('KI', 'Kiribati', 'Kiribati', 'Кирибати', 'AUD', 'Oceania', null, false, 0),
    ('TV', 'Tuvalu', 'Tuvalu', 'Тувалу', 'AUD', 'Oceania', null, false, 0),
    ('NR', 'Nauru', 'Nauru', 'Науру', 'AUD', 'Oceania', null, false, 0),
    ('CK', 'Kuk orollari', 'Cook Islands', 'Острова Кука', 'NZD', 'Oceania', null, false, 0),
    ('NU', 'Niue', 'Niue', 'Ниуэ', 'NZD', 'Oceania', null, false, 0)
ON CONFLICT (code) DO UPDATE SET
    name_uz = EXCLUDED.name_uz,
    name_en = EXCLUDED.name_en,
    name_ru = EXCLUDED.name_ru,
    currency = EXCLUDED.currency,
    region = EXCLUDED.region,
    trade_bloc = EXCLUDED.trade_bloc,
    has_preferential_trade = EXCLUDED.has_preferential_trade,
    import_share_pct = EXCLUDED.import_share_pct;

UPDATE countries SET currency_name = CASE code
    WHEN 'UZ' THEN 'Uzbek So''m' WHEN 'USD' THEN 'US Dollar' WHEN 'EUR' THEN 'Euro'
    WHEN 'CNY' THEN 'Chinese Yuan' WHEN 'RUB' THEN 'Russian Ruble'
    WHEN 'KZT' THEN 'Kazakh Tenge' WHEN 'GBP' THEN 'Pound Sterling'
    WHEN 'JPY' THEN 'Japanese Yen' WHEN 'KRW' THEN 'South Korean Won'
    WHEN 'CHF' THEN 'Swiss Franc' WHEN 'TRY' THEN 'Turkish Lira'
    WHEN 'AED' THEN 'UAE Dirham' WHEN 'INR' THEN 'Indian Rupee'
    WHEN 'BRL' THEN 'Brazilian Real' WHEN 'AUD' THEN 'Australian Dollar'
    WHEN 'CAD' THEN 'Canadian Dollar' WHEN 'SEK' THEN 'Swedish Krona'
    WHEN 'NOK' THEN 'Norwegian Krone' WHEN 'PLN' THEN 'Polish Zloty'
    WHEN 'CZK' THEN 'Czech Koruna' WHEN 'HUF' THEN 'Hungarian Forint'
    WHEN 'RON' THEN 'Romanian Leu' WHEN 'BGN' THEN 'Bulgarian Lev'
    WHEN 'UAH' THEN 'Ukrainian Hryvnia' WHEN 'BYN' THEN 'Belarusian Ruble'
    WHEN 'AZN' THEN 'Azerbaijani Manat' WHEN 'GEL' THEN 'Georgian Lari'
    WHEN 'KGS' THEN 'Kyrgyz Som' WHEN 'TJS' THEN 'Tajik Somoni'
    WHEN 'TMT' THEN 'Turkmen Manat' WHEN 'AFN' THEN 'Afghan Afghani'
    WHEN 'PKR' THEN 'Pakistani Rupee' WHEN 'BDT' THEN 'Bangladeshi Taka'
    WHEN 'LKR' THEN 'Sri Lankan Rupee' WHEN 'IDR' THEN 'Indonesian Rupiah'
    WHEN 'MYR' THEN 'Malaysian Ringgit' WHEN 'PHP' THEN 'Philippine Peso'
    WHEN 'SGD' THEN 'Singapore Dollar' WHEN 'THB' THEN 'Thai Baht'
    WHEN 'VND' THEN 'Vietnamese Dong' WHEN 'ILS' THEN 'Israeli Shekel'
    WHEN 'SAR' THEN 'Saudi Riyal' WHEN 'QAR' THEN 'Qatari Riyal'
    WHEN 'OMR' THEN 'Omani Rial' WHEN 'KWD' THEN 'Kuwaiti Dinar'
    WHEN 'BHD' THEN 'Bahraini Dinar' WHEN 'JOD' THEN 'Jordanian Dinar'
    WHEN 'MXN' THEN 'Mexican Peso' WHEN 'ZAR' THEN 'South African Rand'
    WHEN 'NGN' THEN 'Nigerian Naira' WHEN 'EGP' THEN 'Egyptian Pound'
    WHEN 'ARS' THEN 'Argentine Peso' WHEN 'CLP' THEN 'Chilean Peso'
    WHEN 'COP' THEN 'Colombian Peso' WHEN 'PEN' THEN 'Peruvian Sol'
    WHEN 'TWD' THEN 'Taiwan Dollar' WHEN 'HKD' THEN 'Hong Kong Dollar'
    WHEN 'MAD' THEN 'Moroccan Dirham' WHEN 'DZD' THEN 'Algerian Dinar'
    WHEN 'TND' THEN 'Tunisian Dinar' WHEN 'LYD' THEN 'Libyan Dinar'
    WHEN 'SDG' THEN 'Sudanese Pound' WHEN 'ETB' THEN 'Ethiopian Birr'
    WHEN 'KES' THEN 'Kenyan Shilling' WHEN 'TZS' THEN 'Tanzanian Shilling'
    WHEN 'UGX' THEN 'Ugandan Shilling' WHEN 'GHS' THEN 'Ghanaian Cedi'
    WHEN 'XAF' THEN 'CFA Franc' WHEN 'XOF' THEN 'CFA Franc'
    WHEN 'MGA' THEN 'Malagasy Ariary' WHEN 'MUR' THEN 'Mauritian Rupee'
    WHEN 'ZMW' THEN 'Zambian Kwacha' WHEN 'VES' THEN 'Venezuelan Bolivar'
    WHEN 'BOB' THEN 'Bolivian Boliviano' WHEN 'UYU' THEN 'Uruguayan Peso'
    WHEN 'DKK' THEN 'Danish Krone'
END;
